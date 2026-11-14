"""Gera gráficos PNG e medições reproduzíveis da Unidade II sem abrir o servidor."""

import argparse
import base64
import csv
import json
import platform
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

from tecnoreparo import TecnoReparo


def salvar_png(uri, caminho):
    caminho.write_bytes(base64.b64decode(uri.split(",", 1)[1]))


def main():
    parser = argparse.ArgumentParser(description="Demonstra hash, grafos e ordenação do TecnoReparo")
    parser.add_argument("--saida", default="exemplos")
    parser.add_argument("--tamanho", type=int, default=250)
    parser.add_argument("--cenario", choices=("aleatorio", "ordenado", "inverso", "repetidos"), default="aleatorio")
    parser.add_argument("--repeticoes", type=int, default=3)
    args = parser.parse_args()
    destino = Path(args.saida)
    destino.mkdir(parents=True, exist_ok=True)
    servico = TecnoReparo()
    for i, nome in enumerate(("Marina Costa", "Lucas Almeida", "Beatriz Souza"), 1):
        servico.registrar_ordem(nome_cliente=nome, contato="Demonstração", numero_serie=f"DEMO-{i}",
                               tipo="Notebook", defeito="Exemplo acadêmico")
    demonstracao_hash = {metodo: servico.demonstrar_hash(metodo)
                         for metodo in ("divisao", "multiplicacao", "dobramento")}
    servico.exemplo_rotas()
    rota = servico.calcular_rota("P-0001", "P-0005")
    salvar_png(rota.pop("grafico"), destino / "rota.png")
    analise = servico.comparar_ordenacao(args.tamanho, args.cenario, args.repeticoes, 42)
    salvar_png(analise.pop("grafico"), destino / "ordenacao.png")
    with (destino / "ordenacao.csv").open("w", encoding="utf-8", newline="") as arquivo:
        campos = ("tamanho", "metodo", "mediana_ms", "minimo_ms", "maximo_ms", "comparacoes", "movimentos")
        writer = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(analise["resultados"])
    dados = {"gerado_em_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
             "matplotlib": matplotlib.__version__, "sistema": platform.system(),
             "aviso": "Exemplos fictícios. Tempos medidos nesta execução, não valores universais.",
             "hash": demonstracao_hash, "rota": rota, "ordenacao": analise}
    (destino / "resultados.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Hash: três métodos, colisões, inserção, busca e remoção demonstrados.")
    print("Rota:", " → ".join(rota["caminho"]), f'({rota["distancia_km"]:.2f} km)')
    print("Menor mediana neste ensaio:", analise["menor_mediana"])
    print("PNG, CSV e resultados salvos em:", destino.resolve())


if __name__ == "__main__":
    main()
