"""Servidor descartável dos testes de navegador, em porta local livre."""
from pathlib import Path
import sys
from wsgiref.simple_server import WSGIRequestHandler, make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tecnoreparo import TecnoReparo
from tecnoreparo.api import ApiTecnoReparo
from tecnoreparo.web import AplicacaoTecnoReparo


class Silencioso(WSGIRequestHandler):
    def log_message(self, formato, *args):
        pass


if __name__ == "__main__":
    app = AplicacaoTecnoReparo(ApiTecnoReparo(TecnoReparo()))
    with make_server("127.0.0.1", 0, app, handler_class=Silencioso) as servidor:
        print(f"http://127.0.0.1:{servidor.server_port}", flush=True)
        servidor.serve_forever()
