"""Figuras Matplotlib em memória; sem estado global de pyplot no servidor."""
from base64 import b64encode
from io import BytesIO
from math import cos, radians
from textwrap import wrap

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator


class Graficos:
    CORES = {"bolha": "#168779", "insercao": "#3779b8", "selecao": "#bd802b", "quicksort": "#8561b5"}

    @staticmethod
    def _png(figura):
        buffer = BytesIO()
        FigureCanvasAgg(figura).print_png(buffer)
        return "data:image/png;base64," + b64encode(buffer.getvalue()).decode("ascii")

    @staticmethod
    def rede(rede, rota=None):
        pontos = {p["id"]: p for p in rede["pontos"]}
        figura = Figure(figsize=(11, max(5.8, len(pontos) * 0.48 + 1.5)), dpi=120,
                        layout="constrained", facecolor="white")
        eixo, legenda = figura.subplots(1, 2, gridspec_kw={"width_ratios": [3.2, 1]})
        legenda.axis("off")
        legenda.text(0, 1, "LOCAIS CADASTRADOS", fontsize=9, fontweight="bold", color="#526973", va="top")
        for i, ponto in enumerate(pontos.values()):
            texto = ponto["id"] + "\n" + "\n".join(wrap(ponto["nome"], 26))
            legenda.text(0, 0.92 - i * (0.90 / max(6, len(pontos))), texto, fontsize=8,
                         color="#25434c", va="top", linespacing=1.5, parse_math=False)
        caminho = rota["caminho"] if rota else []
        selecionados = {frozenset((a, b)) for a, b in zip(caminho, caminho[1:])}
        for trecho in rede["trechos"]:
            a, b = pontos[trecho["origem"]], pontos[trecho["destino"]]
            ativo = frozenset((a["id"], b["id"])) in selecionados
            cor = "#0d8777" if ativo else "#b8c8cb"
            eixo.plot([a["longitude"], b["longitude"]], [a["latitude"], b["latitude"]],
                      color=cor, linewidth=3 if ativo else 1.4, zorder=1)
            eixo.annotate(f'{trecho["distancia_km"]:.2f} km',
                          ((a["longitude"] + b["longitude"]) / 2, (a["latitude"] + b["latitude"]) / 2),
                          fontsize=8, color="#425a61", ha="center", va="center",
                          bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85, "pad": 1.3})
        for ponto in pontos.values():
            ativo = ponto["id"] in caminho
            eixo.scatter(ponto["longitude"], ponto["latitude"], s=85, zorder=3,
                         color="#0d8777" if ativo else "#3c6677", edgecolors="white", linewidths=1.5)
            eixo.annotate(ponto["id"],
                          (ponto["longitude"], ponto["latitude"]), xytext=(0, 10), textcoords="offset points", ha="center",
                          fontsize=8, color="#25434c", parse_math=False)
        if pontos:
            media = sum(p["latitude"] for p in pontos.values()) / len(pontos)
            eixo.set_aspect(1 / max(0.1, cos(radians(media))))
            eixo.margins(x=0.18, y=0.18)
            eixo.ticklabel_format(useOffset=False, style="plain")
            eixo.xaxis.set_major_locator(MaxNLocator(5))
            eixo.yaxis.set_major_locator(MaxNLocator(6))
        else:
            eixo.text(0.5, 0.5, "Cadastre locais e conexões para visualizar a rede.",
                      transform=eixo.transAxes, ha="center", color="#526973")
        titulo = "Rede de coleta e entrega"
        if rota:
            titulo += f' · {rota["distancia_km"]:.2f} km' if rota["encontrada"] else " · destino sem conexão"
        eixo.set_title(titulo, loc="left", fontsize=14, fontweight="bold", pad=16, color="#203d46")
        eixo.set_xlabel("Longitude (graus)")
        eixo.set_ylabel("Latitude (graus)")
        eixo.grid(alpha=0.16)
        for borda in eixo.spines.values():
            borda.set_color("#dce6e8")
        figura.supxlabel("Conexões cadastradas • verde: caminho calculado • sem ruas ou trânsito em tempo real", fontsize=9, color="#526973")
        return Graficos._png(figura)

    @staticmethod
    def ordenacao(analise):
        figura = Figure(figsize=(11, 4.8), dpi=120, layout="constrained", facecolor="white")
        curva, barras = figura.subplots(1, 2, gridspec_kw={"width_ratios": [1.15, 1]})
        finais = []
        for metodo, cor in Graficos.CORES.items():
            dados = [r for r in analise["resultados"] if r["metodo"] == metodo]
            curva.plot([r["tamanho"] for r in dados], [r["mediana_ms"] for r in dados],
                       marker="o", color=cor, label=dados[0]["nome"], linewidth=2)
            finais.append(dados[-1])
        curva.set_title("Tempo por tamanho de entrada", loc="left", fontsize=11, pad=12)
        curva.set_xlabel("Quantidade de ordens sintéticas")
        curva.set_ylabel("Mediana do tempo (ms)")
        curva.legend(frameon=False, fontsize=8)
        curva.set_xticks(analise["tamanhos"])
        curva.set_ylim(bottom=0)
        for i, r in enumerate(finais):
            barras.barh(i, r["mediana_ms"], color=Graficos.CORES[r["metodo"]], height=0.55,
                        xerr=[[max(0, r["mediana_ms"] - r["minimo_ms"])],
                              [max(0, r["maximo_ms"] - r["mediana_ms"])]], capsize=3)
        barras.set_yticks(range(4), [r["nome"] for r in finais])
        barras.invert_yaxis()
        barras.set_xlabel("Mediana (ms); hastes: mínimo e máximo")
        barras.set_title(f'Comparação com {analise["tamanho"]} ordens', loc="left", fontsize=11, pad=12)
        for eixo in (curva, barras):
            eixo.grid(axis="x" if eixo is barras else "y", alpha=0.16)
            eixo.set_axisbelow(True)
            for borda in eixo.spines.values():
                borda.set_color("#dce6e8")
        cenarios = {"aleatorio": "aleatório", "ordenado": "já ordenado", "inverso": "ordem inversa", "repetidos": "chaves repetidas"}
        figura.suptitle(f'Ordenação · {cenarios[analise["cenario"]]} · {analise["repeticoes"]} repetições',
                        fontsize=14, fontweight="bold", color="#203d46")
        figura.supxlabel("Tempos medidos com instrumentação; variam conforme entrada e computador.", fontsize=9, color="#526973")
        return Graficos._png(figura)
