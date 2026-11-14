"""Quatro algoritmos próprios, aplicáveis às ordens e ao experimento comparativo."""
from dataclasses import dataclass, asdict
from random import Random
from statistics import median
from time import perf_counter_ns

from .estruturas import Pilha
from .modelos import ValidacaoError


@dataclass
class Metricas:
    comparacoes: int = 0
    movimentos: int = 0


class Ordenador:
    NOMES = {"bolha": "Bolha", "insercao": "Inserção", "selecao": "Seleção", "quicksort": "QuickSort"}

    def __init__(self):
        self.metricas = Metricas()

    def _comparar(self, a, b, chave):
        self.metricas.comparacoes += 1
        ka, kb = chave(a), chave(b)
        return (ka > kb) - (ka < kb)

    def _trocar(self, dados, a, b):
        if a != b:
            dados[a], dados[b] = dados[b], dados[a]
            self.metricas.movimentos += 2

    def ordenar(self, dados, metodo="quicksort", chave=lambda valor: valor):
        """Recebe uma lista de trabalho; alterações não atingem o cadastro original."""
        if not isinstance(metodo, str) or metodo not in self.NOMES:
            raise ValidacaoError("Algoritmo de ordenação inválido.")
        self.metricas = Metricas()
        getattr(self, metodo)(dados, chave)
        return dados

    def bolha(self, dados, chave):
        for fim in range(len(dados) - 1, 0, -1):
            mudou = False
            for i in range(fim):
                if self._comparar(dados[i], dados[i + 1], chave) > 0:
                    self._trocar(dados, i, i + 1)
                    mudou = True
            if not mudou:
                break

    def insercao(self, dados, chave):
        for i in range(1, len(dados)):
            valor = dados[i]
            j = i - 1
            while j >= 0 and self._comparar(dados[j], valor, chave) > 0:
                dados[j + 1] = dados[j]
                self.metricas.movimentos += 1
                j -= 1
            dados[j + 1] = valor
            self.metricas.movimentos += 1

    def selecao(self, dados, chave):
        for i in range(len(dados) - 1):
            menor = i
            for j in range(i + 1, len(dados)):
                if self._comparar(dados[j], dados[menor], chave) < 0:
                    menor = j
            self._trocar(dados, i, menor)

    def quicksort(self, dados, chave):
        """Partição em três faixas, pivô central e pilha explícita da Unidade I."""
        intervalos = Pilha()
        if len(dados) > 1:
            intervalos.empilhar((0, len(dados) - 1))
        while not intervalos.esta_vazia():
            inicio, fim = intervalos.desempilhar()
            pivo = dados[(inicio + fim) // 2]
            menor, atual, maior = inicio, inicio, fim
            while atual <= maior:
                comparacao = self._comparar(dados[atual], pivo, chave)
                if comparacao < 0:
                    self._trocar(dados, menor, atual)
                    menor += 1
                    atual += 1
                elif comparacao > 0:
                    self._trocar(dados, atual, maior)
                    maior -= 1
                else:
                    atual += 1
            if inicio < menor - 1:
                intervalos.empilhar((inicio, menor - 1))
            if maior + 1 < fim:
                intervalos.empilhar((maior + 1, fim))


class ComparadorOrdenacao:
    CENARIOS = ("aleatorio", "ordenado", "inverso", "repetidos")

    def executar(self, tamanho=250, cenario="aleatorio", repeticoes=3, semente=42):
        if type(tamanho) is not int or not 2 <= tamanho <= 500:
            raise ValidacaoError("Use um tamanho entre 2 e 500.")
        if cenario not in self.CENARIOS:
            raise ValidacaoError("Cenário inválido.")
        if type(repeticoes) is not int or not 1 <= repeticoes <= 7:
            raise ValidacaoError("Use de 1 a 7 repetições.")
        if type(semente) is not int or not 0 <= semente <= 1_000_000:
            raise ValidacaoError("Semente deve estar entre 0 e 1000000.")
        resultados = []
        tamanhos = []
        for valor in (max(2, tamanho // 4), max(2, tamanho // 2), tamanho):
            if valor not in tamanhos:
                tamanhos.append(valor)
        for n in tamanhos:
            numeros = list(range(1, n + 1))
            rng = Random(semente + n)
            if cenario == "aleatorio":
                rng.shuffle(numeros)
            elif cenario == "inverso":
                numeros.reverse()
            elif cenario == "repetidos":
                numeros = [rng.randint(1, max(2, n // 10)) for _ in numeros]
            base = [{"numero": valor, "id": f"SIM-{i:04d}"} for i, valor in enumerate(numeros)]
            por_metodo = {metodo: [] for metodo in Ordenador.NOMES}
            metricas = {}
            for metodo in Ordenador.NOMES:
                Ordenador().ordenar(list(base), metodo, chave=lambda ordem: ordem["numero"])
            # Rotaciona a ordem de execução para reduzir viés de sempre medir um primeiro.
            metodos = list(Ordenador.NOMES)
            for rodada in range(repeticoes):
                for metodo in metodos[rodada % 4:] + metodos[:rodada % 4]:
                    dados = list(base)  # Cópia fora do intervalo cronometrado.
                    ordenador = Ordenador()
                    inicio = perf_counter_ns()
                    ordenador.ordenar(dados, metodo, chave=lambda ordem: ordem["numero"])
                    duracao = perf_counter_ns() - inicio
                    assert all(dados[i]["numero"] <= dados[i + 1]["numero"] for i in range(n - 1))
                    por_metodo[metodo].append(duracao / 1_000_000)
                    metricas[metodo] = asdict(ordenador.metricas)
            for metodo, tempos in por_metodo.items():
                resultados.append({"tamanho": n, "metodo": metodo, "nome": Ordenador.NOMES[metodo],
                                   "mediana_ms": median(tempos), "minimo_ms": min(tempos),
                                   "maximo_ms": max(tempos), "tempos_ms": tempos, **metricas[metodo]})
        ultimo = [r for r in resultados if r["tamanho"] == tamanho]
        menor = min(ultimo, key=lambda r: r["mediana_ms"])
        return {"cenario": cenario, "tamanho": tamanho, "tamanhos": tamanhos,
                "repeticoes": repeticoes, "semente": semente, "resultados": resultados,
                "menor_mediana": menor["nome"], "dados": "Ordens sintéticas com chave numérica; cadastro real preservado.",
                "metodologia": "Mesmas entradas e cópias independentes; aquecimento; perf_counter_ns; mediana. "
                "Tempos incluem a instrumentação de comparações e movimentos. Resultados dependem do cenário e do computador."}
