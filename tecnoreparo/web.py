"""Entrega a interface e a API na mesma origem, sem dependências externas."""

from pathlib import Path
from typing import Callable

from .api import ApiTecnoReparo


class AplicacaoTecnoReparo:
    def __init__(self, api: ApiTecnoReparo):
        self.api = api
        self._pasta = Path(__file__).resolve().parent.parent / "frontend"
        # Uma lista fechada impede acesso a código, arquivos locais ou travessia de diretórios.
        self._arquivos = {
            "/": ("index.html", "text/html; charset=utf-8"),
            "/assets/styles.css": ("styles.css", "text/css; charset=utf-8"),
            "/assets/app.js": ("app.js", "text/javascript; charset=utf-8"),
            "/assets/icons.svg": ("icons.svg", "image/svg+xml"),
            "/assets/favicon.svg": ("favicon.svg", "image/svg+xml"),
        }

    def __call__(self, environ: dict, start_response: Callable) -> list[bytes]:
        caminho = environ.get("PATH_INFO", "/")
        if caminho == "/api":
            contexto = dict(environ)
            contexto["PATH_INFO"] = "/"
            return self.api(contexto, start_response)
        if caminho.startswith("/api/"):
            return self.api(environ, start_response)
        metodo = environ.get("REQUEST_METHOD", "GET")
        if caminho not in self._arquivos:
            corpo = b"Recurso nao encontrado."
            start_response("404 Not Found", [
                ("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(corpo))),
            ])
            return [] if metodo == "HEAD" else [corpo]
        if metodo not in ("GET", "HEAD"):
            corpo = b"Metodo nao permitido."
            start_response("405 Method Not Allowed", [
                ("Content-Type", "text/plain; charset=utf-8"), ("Content-Length", str(len(corpo))),
                ("Allow", "GET, HEAD"),
            ])
            return [corpo]
        arquivo, tipo = self._arquivos[caminho]
        corpo = (self._pasta / arquivo).read_bytes()
        start_response("200 OK", [
            ("Content-Type", tipo), ("Content-Length", str(len(corpo))),
            ("Cache-Control", "no-cache"), ("X-Content-Type-Options", "nosniff"),
            ("Content-Security-Policy",
             "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
             "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
             "base-uri 'none'; frame-ancestors 'self'"),
        ])
        return [] if metodo == "HEAD" else [corpo]
