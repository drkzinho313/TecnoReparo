"""Entidades da assistência técnica; cada OS compõe seus próprios TADs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .estruturas import ListaEncadeada, Pilha


class ErroDominio(Exception):
    """Erro esperado, adequado para exibição ao usuário."""


class ValidacaoError(ErroDominio):
    pass


class NaoEncontradoError(ErroDominio):
    pass


class ConflitoError(ErroDominio):
    pass


class StatusOrdem(str, Enum):
    AGUARDANDO = "aguardando"
    EM_REPARO = "em_reparo"
    CONCLUIDA = "concluida"
    AGUARDANDO_REVISAO = "aguardando_revisao"


@dataclass(frozen=True)
class Equipamento:
    numero_serie: str
    tipo: str
    defeito: str


@dataclass(frozen=True)
class PedidoRevisao:
    ordem_id: str
    motivo: str
    urgente: bool


@dataclass
class EtapaReparo:
    id: int
    descricao: str
    concluida: bool = False

    def para_dict(self) -> dict:
        return {"id": self.id, "descricao": self.descricao, "concluida": self.concluida}


class OrdemServico:
    """Objeto composto por equipamento, etapas, pilha e histórico.

    O serviço é responsável por validar as transições. As respostas públicas
    usam para_dict(), que cria dados de apresentação sem expor os nós internos.
    """

    def __init__(
        self,
        identificador: str,
        cliente: tuple[str, str],
        equipamento: Equipamento,
        sintomas: set[str],
    ):
        self.id = identificador
        self.cliente = cliente  # Tupla: (nome, contato).
        self.equipamento = equipamento
        self.sintomas = set(sintomas)
        self.status = StatusOrdem.AGUARDANDO
        self.bancada: int | None = None
        self.etapas: ListaEncadeada[EtapaReparo] = ListaEncadeada()
        self.pecas: Pilha[str] = Pilha()
        self.historico: list[str] = ["Ordem cadastrada na fila comum."]
        self._proximo_id_etapa = 1
        for descricao in ("Diagnóstico", "Reparo", "Teste final"):
            self.adicionar_etapa(descricao)

    def adicionar_etapa(self, descricao: str) -> EtapaReparo:
        etapa = EtapaReparo(self._proximo_id_etapa, descricao)
        self.etapas.inserir_fim(etapa)
        self._proximo_id_etapa += 1
        return etapa

    def para_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente": {"nome": self.cliente[0], "contato": self.cliente[1]},
            "equipamento": {
                "numero_serie": self.equipamento.numero_serie,
                "tipo": self.equipamento.tipo,
                "defeito": self.equipamento.defeito,
            },
            "sintomas": sorted(self.sintomas),
            "status": self.status.value,
            "bancada": self.bancada,
            "etapas": [etapa.para_dict() for etapa in self.etapas],
            "pecas_do_topo_para_base": list(self.pecas),
            "historico": list(self.historico),
        }
