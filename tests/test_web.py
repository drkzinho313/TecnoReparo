"""Contrato de entrega da interface e integração HTTP com o backend real."""

import io
import json
import threading
import unittest
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from wsgiref.simple_server import WSGIRequestHandler, make_server
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator

from tecnoreparo import TecnoReparo
from tecnoreparo.api import ApiTecnoReparo
from tecnoreparo.web import AplicacaoTecnoReparo


class RecursosHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.caminhos = set()

    def handle_starttag(self, tag, attrs):
        for nome, valor in attrs:
            if nome in ("href", "src") and valor and valor.startswith("/assets/"):
                self.caminhos.add(valor.split("#")[0])


class TestWeb(unittest.TestCase):
    def setUp(self):
        self.servico = TecnoReparo(2)
        self.app = AplicacaoTecnoReparo(ApiTecnoReparo(self.servico))

    def requisicao(self, metodo, caminho, dados=None, **extras):
        environ = {}
        setup_testing_defaults(environ)
        corpo = json.dumps(dados).encode() if dados is not None else b""
        environ.update({
            "REQUEST_METHOD": metodo, "PATH_INFO": caminho, "QUERY_STRING": "",
            "HTTP_HOST": "127.0.0.1:8000", "SERVER_PORT": "8000",
            "CONTENT_TYPE": "application/json", "CONTENT_LENGTH": str(len(corpo)),
            "wsgi.input": io.BytesIO(corpo),
        })
        environ.update(extras)
        resposta = {}

        def iniciar(status, cabecalhos, exc_info=None):
            resposta.update(status=int(status.split()[0]), cabecalhos=dict(cabecalhos))

        resultado = validator(self.app)(environ, iniciar)
        try:
            resposta["corpo"] = b"".join(resultado)
        finally:
            resultado.close()
        if metodo != "HEAD":
            self.assertEqual(len(resposta["corpo"]), int(resposta["cabecalhos"]["Content-Length"]))
        return resposta

    def test_html_publica_todos_os_recursos_locais(self):
        pagina = self.requisicao("GET", "/")
        self.assertEqual(pagina["status"], 200)
        self.assertEqual(pagina["cabecalhos"]["Content-Type"], "text/html; charset=utf-8")
        parser = RecursosHTML()
        parser.feed(pagina["corpo"].decode())
        self.assertTrue(parser.caminhos)
        for caminho in parser.caminhos:
            with self.subTest(caminho=caminho):
                recurso = self.requisicao("GET", caminho)
                self.assertEqual(recurso["status"], 200)
                self.assertTrue(recurso["corpo"])
                self.assertEqual(recurso["cabecalhos"]["X-Content-Type-Options"], "nosniff")
        self.assertIn("script-src 'self'", pagina["cabecalhos"]["Content-Security-Policy"])

    def test_head_preserva_cabecalhos_sem_enviar_corpo(self):
        for caminho in ("/", "/assets/styles.css", "/assets/app.js"):
            with self.subTest(caminho=caminho):
                get = self.requisicao("GET", caminho)
                head = self.requisicao("HEAD", caminho)
                self.assertEqual(head["status"], 200)
                self.assertEqual(head["cabecalhos"], get["cabecalhos"])
                self.assertEqual(head["corpo"], b"")

    def test_somente_arquivos_publicos_e_metodos_de_leitura(self):
        for caminho in ("/main.py", "/README.md", "/assets/../main.py", "/assets/inexistente"):
            with self.subTest(caminho=caminho):
                self.assertEqual(self.requisicao("GET", caminho)["status"], 404)
        resposta = self.requisicao("POST", "/assets/app.js", {})
        self.assertEqual(resposta["status"], 405)
        self.assertEqual(resposta["cabecalhos"]["Allow"], "GET, HEAD")

    def test_catalogo_json_e_estado_sao_encaminhados(self):
        catalogo = self.requisicao("GET", "/api")
        self.assertEqual(catalogo["status"], 200)
        self.assertTrue(json.loads(catalogo["corpo"])["dados"]["rotas"])
        estado = self.requisicao("GET", "/api/estado")
        self.assertEqual(json.loads(estado["corpo"])["dados"]["total_ordens"], 0)

    def test_origem_compara_protocolo_host_e_porta(self):
        for origem in ("http://127.0.0.1:8001", "https://127.0.0.1:8000", "http://localhost:8000", "null", "http://127.0.0.1:inválida"):
            with self.subTest(origem=origem):
                resposta = self.requisicao("GET", "/api/estado", HTTP_ORIGIN=origem)
                self.assertEqual(resposta["status"], 403)
        mesma = self.requisicao("GET", "/api/estado", HTTP_ORIGIN="http://127.0.0.1:8000")
        self.assertEqual(mesma["status"], 200)
        padrao = self.requisicao("GET", "/api/estado", HTTP_ORIGIN="http://localhost", HTTP_HOST="localhost:80")
        self.assertEqual(padrao["status"], 200)

    def test_interface_e_cadastro_pelo_mesmo_servidor_http(self):
        class Silencioso(WSGIRequestHandler):
            def log_message(self, format, *args):
                pass

        with make_server("127.0.0.1", 0, self.app, handler_class=Silencioso) as servidor:
            thread = threading.Thread(target=servidor.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{servidor.server_port}"
            try:
                with urlopen(base, timeout=3) as pagina:
                    self.assertEqual(pagina.status, 200)
                    self.assertIn(b"/assets/app.js", pagina.read())
                dados = {
                    "nome_cliente": "Cliente de teste", "contato": "Contato fictício",
                    "tipo": "Notebook", "numero_serie": "TESTE-WEB",
                    "defeito": "Não liga", "sintomas": ["Sem imagem"],
                }
                cadastro = Request(base + "/api/ordens", data=json.dumps(dados).encode(),
                                   headers={"Content-Type": "application/json", "Origin": base}, method="POST")
                with urlopen(cadastro, timeout=3) as resposta:
                    self.assertEqual(resposta.status, 201)
                    self.assertEqual(json.load(resposta)["dados"]["id"], "OS-0001")
                with urlopen(base + "/api/estado", timeout=3) as resposta:
                    self.assertEqual(json.load(resposta)["dados"]["fila"], ["OS-0001"])
            finally:
                servidor.shutdown()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
