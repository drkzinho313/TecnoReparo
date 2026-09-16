import io
import json
import threading
import unittest
from urllib.request import Request, urlopen
from wsgiref.simple_server import WSGIRequestHandler, make_server
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator

from tecnoreparo import TecnoReparo
from tecnoreparo.api import ApiTecnoReparo


CADASTRO = {
    "nome_cliente": "Cliente fictício", "contato": "Contato de teste",
    "numero_serie": "PC-1", "tipo": "Desktop", "defeito": "Não liga",
    "sintomas": ["Não liga", "não liga"],
}


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.servico = TecnoReparo(2)
        self.app = ApiTecnoReparo(self.servico, ("http://localhost:5173",))

    def requisicao(self, metodo, caminho, dados=None, *, bruto=None, **environ_extra):
        environ = {}
        setup_testing_defaults(environ)
        path, _, query = caminho.partition("?")
        corpo = bruto if bruto is not None else (json.dumps(dados).encode() if dados is not None else b"")
        environ.update({
            "REQUEST_METHOD": metodo, "PATH_INFO": path, "QUERY_STRING": query,
            "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(corpo)),
            "wsgi.input": io.BytesIO(corpo),
        })
        environ.update(environ_extra)
        resposta = {}

        def iniciar(status, cabecalhos, exc_info=None):
            resposta.update(status=int(status.split()[0]), cabecalhos=dict(cabecalhos))

        resultado = validator(self.app)(environ, iniciar)
        try:
            conteudo = b"".join(resultado)
        finally:
            resultado.close()
        self.assertEqual(int(resposta["cabecalhos"]["Content-Length"]), len(conteudo))
        resposta["corpo"] = json.loads(conteudo) if conteudo else None
        return resposta

    def test_cadastro_consulta_e_fluxo_http_completo(self):
        cadastro = self.requisicao("POST", "/api/ordens", CADASTRO)
        self.assertEqual(cadastro["status"], 201)
        identificador = cadastro["corpo"]["dados"]["id"]
        self.assertEqual(self.requisicao("POST", "/api/atendimentos", {})["status"], 200)
        self.assertEqual(self.requisicao(
            "POST", f"/api/ordens/{identificador}/pecas/retirar", {"peca": "Tampa"},
        )["status"], 200)
        self.assertEqual(self.requisicao(
            "POST", f"/api/ordens/{identificador}/concluir", {},
        )["status"], 409)
        self.requisicao("POST", f"/api/ordens/{identificador}/pecas/recolocar", {})
        for etapa in (1, 2, 3):
            resposta = self.requisicao(
                "PATCH", f"/api/ordens/{identificador}/etapas/{etapa}", {"concluida": True},
            )
            self.assertEqual(resposta["status"], 200)
        concluida = self.requisicao("POST", f"/api/ordens/{identificador}/concluir", {})
        self.assertEqual(concluida["corpo"]["dados"]["status"], "concluida")
        estado = self.requisicao("GET", "/api/estado")
        self.assertTrue(estado["corpo"]["dados"]["bancadas"][0]["livre"])

    def test_documentacao_e_relatorio(self):
        raiz = self.requisicao("GET", "/")
        self.assertEqual(raiz["status"], 200)
        self.assertTrue(raiz["corpo"]["dados"]["rotas"])
        self.assertEqual(self.requisicao("GET", "/api/relatorio")["status"], 200)

    def test_campo_faltante_desconhecido_e_tipo_invalido(self):
        for dados in ({}, {**CADASTRO, "campo_extra": 1}, {**CADASTRO, "nome_cliente": 2}):
            self.assertEqual(self.requisicao("POST", "/api/ordens", dados)["status"], 400)
        self.assertEqual(self.servico.estado()["total_ordens"], 0)

    def test_json_invalido_array_e_unicode_invalido(self):
        for bruto in (b"{", b"[]", b"null", b"\xff"):
            with self.subTest(bruto=bruto):
                self.assertEqual(self.requisicao("POST", "/api/ordens", bruto=bruto)["status"], 400)

    def test_tipo_de_conteudo_e_limite(self):
        self.assertEqual(self.requisicao(
            "POST", "/api/ordens", CADASTRO, CONTENT_TYPE="text/plain",
        )["status"], 415)
        self.assertEqual(self.requisicao(
            "POST", "/api/ordens", bruto=b"x" * 65537,
        )["status"], 413)

    def test_rotas_e_metodos(self):
        self.assertEqual(self.requisicao("GET", "/api/inexistente")["status"], 404)
        self.assertEqual(self.requisicao("GET", "/api/ordens/OS-9999")["status"], 404)
        resposta = self.requisicao("PUT", "/api/ordens")
        self.assertEqual(resposta["status"], 405)
        self.assertIn("POST", resposta["cabecalhos"]["Allow"])

    def test_conflito_e_booleano_estrito(self):
        self.requisicao("POST", "/api/ordens", CADASTRO)
        self.assertEqual(self.requisicao("POST", "/api/ordens", CADASTRO)["status"], 409)
        self.requisicao("POST", "/api/atendimentos", {})
        resposta = self.requisicao(
            "PATCH", "/api/ordens/OS-0001/etapas/1", {"concluida": "true"},
        )
        self.assertEqual(resposta["status"], 400)

    def test_analises_e_filtro(self):
        self.requisicao("POST", "/api/ordens", CADASTRO)
        for caminho in (
            "/api/ordens/OS-0001/recursao", "/api/ordens/OS-0001/copias",
            "/api/ordens?status=aguardando", "/api/analises/busca?tamanho=8",
        ):
            self.assertEqual(self.requisicao("GET", caminho)["status"], 200)
        for caminho in ("/api/analises/busca?tamanho=abc", "/api/ordens?status=inexistente"):
            self.assertEqual(self.requisicao("GET", caminho)["status"], 400)

    def test_cors_explicito_e_preflight(self):
        resposta = self.requisicao("OPTIONS", "/api/ordens", HTTP_ORIGIN="http://localhost:5173")
        self.assertEqual(resposta["status"], 200)
        self.assertIn("POST", resposta["corpo"]["dados"]["metodos"])
        self.assertEqual(resposta["cabecalhos"]["Access-Control-Allow-Origin"], "http://localhost:5173")
        self.assertEqual(self.requisicao(
            "POST", "/api/ordens", CADASTRO, HTTP_ORIGIN="http://origem-invalida.example",
        )["status"], 403)
        self.assertEqual(self.servico.estado()["total_ordens"], 0)

    def test_revisao_pelo_endpoint(self):
        self.requisicao("POST", "/api/ordens", CADASTRO)
        self.requisicao("POST", "/api/atendimentos", {})
        for etapa in (1, 2, 3):
            self.requisicao("PATCH", f"/api/ordens/OS-0001/etapas/{etapa}", {"concluida": True})
        self.requisicao("POST", "/api/ordens/OS-0001/concluir", {})
        resposta = self.requisicao(
            "POST", "/api/ordens/OS-0001/revisoes", {"motivo": "Retorno", "urgente": True},
        )
        self.assertEqual(resposta["status"], 201)
        self.assertEqual(self.requisicao(
            "POST", "/api/revisoes/cancelar", {"extremidade": "fim"},
        )["corpo"]["dados"]["status"], "concluida")

    def test_servidor_real_em_porta_local(self):
        class Silencioso(WSGIRequestHandler):
            def log_message(self, format, *args):
                pass

        with make_server("127.0.0.1", 0, self.app, handler_class=Silencioso) as servidor:
            thread = threading.Thread(target=servidor.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{servidor.server_port}"
                requisicao = Request(
                    base + "/api/ordens", data=json.dumps(CADASTRO).encode(),
                    headers={"Content-Type": "application/json"}, method="POST",
                )
                with urlopen(requisicao, timeout=3) as resposta:
                    self.assertEqual(resposta.status, 201)
                with urlopen(base + "/api/estado", timeout=3) as resposta:
                    self.assertEqual(json.load(resposta)["dados"]["fila"], ["OS-0001"])
            finally:
                servidor.shutdown()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
