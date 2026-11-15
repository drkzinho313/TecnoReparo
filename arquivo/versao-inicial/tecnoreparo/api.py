"""Adaptador HTTP/JSON WSGI. O núcleo não depende desta camada."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from .modelos import ConflitoError, NaoEncontradoError, ValidacaoError
from .servico import TecnoReparo


class ErroHTTP(Exception):
    def __init__(self, codigo: int, mensagem: str, cabecalhos: list[tuple[str, str]] | None = None):
        super().__init__(mensagem)
        self.codigo = codigo
        self.cabecalhos = cabecalhos or []


@dataclass
class _Rota:
    metodo: str
    caminho: str
    padrao: re.Pattern
    acao: Callable
    status: int
    permitidos: set[str]
    obrigatorios: set[str]


class ApiTecnoReparo:
    LIMITE_CORPO = 65536

    def __init__(self, servico: TecnoReparo, origens_permitidas: tuple[str, ...] = ()):
        self.servico = servico
        self._origens = frozenset(origens_permitidas)
        self._rotas: list[_Rota] = []
        self._montar_rotas()

    def _rota(
        self, metodo: str, caminho: str, acao: Callable, *,
        status: int = 200, campos: str = "", obrigatorios: str = "",
    ) -> None:
        padrao = caminho.replace("{ordem_id}", r"(?P<ordem_id>OS-[0-9]+)")
        padrao = padrao.replace("{etapa_id}", r"(?P<etapa_id>[0-9]+)")
        self._rotas.append(_Rota(
            metodo, caminho, re.compile(padrao), acao, status,
            set(campos.split()), set(obrigatorios.split()),
        ))

    def _montar_rotas(self) -> None:
        s = self.servico
        self._rota("GET", "/", lambda p, b, q: {
            "projeto": "TecnoReparo",
            "versao": "2.0.0",
            "armazenamento": "em_memoria",
            "rotas": [
                {"metodo": r.metodo, "caminho": r.caminho, "campos_json": sorted(r.permitidos)}
                for r in self._rotas
            ],
        })
        self._rota("GET", "/api/estado", lambda p, b, q: s.estado())
        self._rota("GET", "/api/relatorio", lambda p, b, q: s.relatorio())
        self._rota("GET", "/api/ordens", lambda p, b, q: s.listar_ordens(q.get("status", [None])[0]))
        cadastro = "nome_cliente contato numero_serie tipo defeito"
        self._rota(
            "POST", "/api/ordens", lambda p, b, q: s.registrar_ordem(**b),
            status=201, campos=cadastro + " sintomas", obrigatorios=cadastro,
        )
        self._rota("GET", "/api/ordens/{ordem_id}", lambda p, b, q: s.obter_ordem(p["ordem_id"]))
        self._rota(
            "POST", "/api/atendimentos",
            lambda p, b, q: s.atender_proximo(b.get("origem", "fila")), campos="origem",
        )
        self._rota(
            "POST", "/api/ordens/{ordem_id}/etapas",
            lambda p, b, q: s.adicionar_etapa(p["ordem_id"], b["descricao"]),
            status=201, campos="descricao", obrigatorios="descricao",
        )
        self._rota(
            "PATCH", "/api/ordens/{ordem_id}/etapas/{etapa_id}",
            lambda p, b, q: s.marcar_etapa(p["ordem_id"], int(p["etapa_id"]), b["concluida"]),
            campos="concluida", obrigatorios="concluida",
        )
        self._rota(
            "DELETE", "/api/ordens/{ordem_id}/etapas/{etapa_id}",
            lambda p, b, q: s.remover_etapa(p["ordem_id"], int(p["etapa_id"])),
        )
        self._rota(
            "POST", "/api/ordens/{ordem_id}/pecas/retirar",
            lambda p, b, q: s.retirar_peca(p["ordem_id"], b["peca"]),
            campos="peca", obrigatorios="peca",
        )
        self._rota(
            "POST", "/api/ordens/{ordem_id}/pecas/recolocar",
            lambda p, b, q: s.recolocar_peca(p["ordem_id"]),
        )
        self._rota(
            "POST", "/api/ordens/{ordem_id}/concluir",
            lambda p, b, q: s.concluir_atendimento(p["ordem_id"]),
        )
        self._rota(
            "POST", "/api/ordens/{ordem_id}/revisoes",
            lambda p, b, q: s.solicitar_revisao(p["ordem_id"], b["motivo"], b.get("urgente", False)),
            status=201, campos="motivo urgente", obrigatorios="motivo",
        )
        self._rota(
            "POST", "/api/revisoes/cancelar",
            lambda p, b, q: s.cancelar_revisao(b.get("extremidade", "fim")),
            campos="extremidade",
        )
        self._rota(
            "GET", "/api/ordens/{ordem_id}/recursao",
            lambda p, b, q: s.analisar_recursao(p["ordem_id"]),
        )
        self._rota(
            "GET", "/api/ordens/{ordem_id}/copias",
            lambda p, b, q: s.demonstrar_copias(p["ordem_id"]),
        )
        self._rota(
            "GET", "/api/analises/busca",
            lambda p, b, q: s.analisar_busca(self._inteiro_query(q.get("tamanho", ["8"])[0])),
        )

    @staticmethod
    def _inteiro_query(valor: str) -> int:
        if not valor.isascii() or not valor.isdigit() or len(valor) > 6:
            raise ValidacaoError("tamanho deve ser um inteiro de 1 a 500.")
        return int(valor)

    def _ler_corpo(self, environ: dict) -> dict:
        try:
            tamanho = int(environ.get("CONTENT_LENGTH") or "0")
        except (TypeError, ValueError):
            raise ErroHTTP(400, "Content-Length inválido.") from None
        if tamanho < 0:
            raise ErroHTTP(400, "Content-Length inválido.")
        if tamanho > self.LIMITE_CORPO:
            raise ErroHTTP(413, "O corpo da requisição excede 64 KiB.")
        if not tamanho:
            return {}
        tipo = environ.get("CONTENT_TYPE", "").split(";")[0].strip().lower()
        if tipo != "application/json":
            raise ErroHTTP(415, "Envie o corpo como application/json.")
        conteudo = environ["wsgi.input"].read(tamanho)
        if len(conteudo) != tamanho:
            raise ErroHTTP(400, "Corpo da requisição incompleto.")
        try:
            corpo = json.loads(conteudo.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise ErroHTTP(400, "JSON inválido.") from None
        if not isinstance(corpo, dict):
            raise ErroHTTP(400, "O corpo JSON deve ser um objeto.")
        return corpo

    def _despachar(self, environ: dict) -> tuple[int, object, list[tuple[str, str]]]:
        caminho = environ.get("PATH_INFO", "/")
        metodo = environ.get("REQUEST_METHOD", "GET").upper()
        candidatas = [(r, r.padrao.fullmatch(caminho)) for r in self._rotas]
        candidatas = [(r, m) for r, m in candidatas if m is not None]
        if not candidatas:
            raise ErroHTTP(404, "Rota não encontrada.")
        metodos = sorted({r.metodo for r, _ in candidatas} | {"OPTIONS"})
        allow = [("Allow", ", ".join(metodos))]
        if metodo == "OPTIONS":
            return 200, {"dados": {"metodos": metodos}}, allow
        correspondencia = next(((r, m) for r, m in candidatas if r.metodo == metodo), None)
        if correspondencia is None:
            raise ErroHTTP(405, "Método não permitido para essa rota.", allow)
        rota, match = correspondencia
        corpo = self._ler_corpo(environ)
        extras = set(corpo) - rota.permitidos
        faltantes = rota.obrigatorios - set(corpo)
        if extras:
            raise ValidacaoError("Campos desconhecidos: " + ", ".join(sorted(extras)) + ".")
        if faltantes:
            raise ValidacaoError("Campos obrigatórios: " + ", ".join(sorted(faltantes)) + ".")
        query = parse_qs(environ.get("QUERY_STRING", ""), keep_blank_values=True, max_num_fields=20)
        resultado = rota.acao(match.groupdict(), corpo, query)
        return rota.status, {"dados": resultado}, []

    def _origem_autorizada(self, origem: str, environ: dict) -> bool:
        if origem in self._origens:
            return True
        esquema = environ.get("wsgi.url_scheme", "http")
        host = environ.get("HTTP_HOST") or (
            environ.get("SERVER_NAME", "localhost") + ":" + environ.get("SERVER_PORT", "80")
        )
        try:
            recebida = urlsplit(origem)
            local = urlsplit(esquema + "://" + host)
            porta_recebida = recebida.port if recebida.port is not None else (443 if recebida.scheme == "https" else 80)
            porta_local = local.port if local.port is not None else (443 if local.scheme == "https" else 80)
            return (
                recebida.scheme in ("http", "https")
                and recebida.scheme == local.scheme
                and recebida.hostname == local.hostname
                and porta_recebida == porta_local
                and recebida.username is None and recebida.password is None
                and recebida.path in ("", "/")
                and not recebida.query and not recebida.fragment
            )
        except ValueError:
            return False

    def __call__(self, environ: dict, start_response: Callable) -> list[bytes]:
        origem = environ.get("HTTP_ORIGIN")
        autorizada = bool(origem) and self._origem_autorizada(origem, environ)
        extras: list[tuple[str, str]] = []
        try:
            if origem and not autorizada:
                raise ErroHTTP(403, "Origem do frontend não autorizada nesta configuração.")
            codigo, resposta, extras = self._despachar(environ)
        except ErroHTTP as erro:
            codigo, resposta, extras = erro.codigo, {"erro": str(erro)}, erro.cabecalhos
        except ValidacaoError as erro:
            codigo, resposta = 400, {"erro": str(erro)}
        except NaoEncontradoError as erro:
            codigo, resposta = 404, {"erro": str(erro)}
        except ConflitoError as erro:
            codigo, resposta = 409, {"erro": str(erro)}
        except ValueError:
            codigo, resposta = 400, {"erro": "Parâmetro inválido."}
        except Exception:
            logging.exception("Falha inesperada no TecnoReparo")
            codigo, resposta = 500, {"erro": "Falha interna no servidor."}
        corpo = json.dumps(resposta, ensure_ascii=False).encode("utf-8")
        cabecalhos = [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(corpo))),
            ("Cache-Control", "no-store"),
        ] + extras
        if autorizada:
            cabecalhos += [
                ("Access-Control-Allow-Origin", origem),
                ("Vary", "Origin"),
                ("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type"),
            ]
        start_response(f"{codigo} {HTTPStatus(codigo).phrase}", cabecalhos)
        return [corpo]
