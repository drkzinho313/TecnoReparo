"""Servidor local: python main.py --demo."""

import argparse
from wsgiref.simple_server import make_server

from tecnoreparo import TecnoReparo
from tecnoreparo.api import ApiTecnoReparo


def main() -> None:
    parser = argparse.ArgumentParser(description="TecnoReparo - backend acadêmico em POO")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, default=8000)
    parser.add_argument("--bancadas", type=int, default=3)
    parser.add_argument("--demo", action="store_true", help="Carrega três ordens fictícias.")
    parser.add_argument("--origem-frontend", action="append", default=[], help="Origem CORS exata; pode repetir.")
    args = parser.parse_args()
    if not 1 <= args.bancadas <= 1000 or not 1 <= args.porta <= 65535:
        parser.error("Use 1..1000 bancadas e porta 1..65535.")
    servico = TecnoReparo(args.bancadas)
    if args.demo:
        for i, tipo in enumerate(("Desktop", "Notebook", "Desktop"), start=1):
            servico.registrar_ordem(
                nome_cliente=f"Cliente fictício {i}",
                contato=f"Contato de demonstração {i}",
                numero_serie=f"DEMO-{i}",
                tipo=tipo,
                defeito="Equipamento não liga",
                sintomas=["Não liga", "não liga", "Sem imagem"],
            )
        primeira = servico.atender_proximo()
        servico.retirar_peca(primeira["id"], "Tampa")
    app = ApiTecnoReparo(servico, tuple(args.origem_frontend))
    with make_server(args.host, args.porta, app) as servidor:
        print(f"TecnoReparo: http://{args.host}:{args.porta}", flush=True)
        print("Dados em memória: são reiniciados ao encerrar. Ctrl+C para sair.", flush=True)
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor encerrado.")


if __name__ == "__main__":
    main()
