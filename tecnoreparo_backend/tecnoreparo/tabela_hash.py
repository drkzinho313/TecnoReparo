"""Tabela hash própria: vetor de baldes e colisões por encadeamento separado."""
from dataclasses import dataclass
from math import sqrt
from typing import Generic, Iterator, TypeVar

from .estruturas import ListaEncadeada, VetorFixo

T = TypeVar("T")


@dataclass
class EntradaHash(Generic[T]):
    chave: str
    valor: T


class TabelaHash(Generic[T]):
    METODOS = ("divisao", "multiplicacao", "dobramento")

    def __init__(self, capacidade: int = 17, metodo: str = "divisao", redimensionar: bool = True):
        if type(capacidade) is not int or capacidade < 2:
            raise ValueError("A capacidade deve ser um inteiro maior ou igual a 2.")
        if metodo not in self.METODOS:
            raise ValueError("Método hash inválido.")
        self.metodo = metodo
        self._automatico = redimensionar
        self._baldes = self._criar_baldes(capacidade)
        self._chaves: list[str] = []  # Preserva a ordem de cadastro na API.
        self._redimensionamentos = 0

    @staticmethod
    def _criar_baldes(capacidade):
        baldes = VetorFixo(capacidade)
        for i in range(capacidade):
            baldes[i] = ListaEncadeada()
        return baldes

    @staticmethod
    def codigo(chave: str) -> int:
        """Converte UTF-8 em inteiro determinístico de 32 bits (base 31)."""
        if not isinstance(chave, str) or not chave:
            raise ValueError("A chave deve ser um texto não vazio.")
        valor = 0
        for byte in chave.encode("utf-8"):
            valor = (31 * valor + byte) % (2**32)
        return valor

    def indice(self, chave: str) -> int:
        codigo = self.codigo(chave)
        m = len(self._baldes)
        if self.metodo == "multiplicacao":
            produto = codigo * ((sqrt(5) - 1) / 2)
            return int(m * (produto - int(produto)))
        if self.metodo == "dobramento":
            dados = chave.encode("utf-8")
            return sum(int.from_bytes(dados[i:i+2], "big") for i in range(0, len(dados), 2)) % m
        return codigo % m

    def __len__(self):
        return len(self._chaves)

    def __iter__(self):
        return iter(self._chaves)

    def buscar(self, chave: str) -> T:
        entrada = self._baldes[self.indice(chave)].buscar(lambda item: item.chave == chave)
        if entrada is None:
            raise KeyError(chave)
        return entrada.valor

    def __getitem__(self, chave):
        return self.buscar(chave)

    def __contains__(self, chave):
        try:
            self.buscar(chave)
            return True
        except KeyError:
            return False

    def inserir(self, chave: str, valor: T):
        balde = self._baldes[self.indice(chave)]
        entrada = balde.buscar(lambda item: item.chave == chave)
        if entrada is not None:
            entrada.valor = valor
            return
        if self._automatico and (len(self) + 1) / len(self._baldes) > 0.75:
            self._redimensionar(2 * len(self._baldes) + 1)
            balde = self._baldes[self.indice(chave)]
        balde.inserir_fim(EntradaHash(chave, valor))
        self._chaves.append(chave)

    def __setitem__(self, chave, valor):
        self.inserir(chave, valor)

    def remover(self, chave: str) -> T:
        try:
            entrada = self._baldes[self.indice(chave)].remover_primeiro(lambda item: item.chave == chave)
        except ValueError:
            raise KeyError(chave) from None
        self._chaves.remove(chave)
        return entrada.valor

    def values(self) -> Iterator[T]:
        for chave in self._chaves:
            yield self.buscar(chave)

    def _redimensionar(self, capacidade: int):
        entradas = [entrada for balde in self._baldes for entrada in balde]
        self._baldes = self._criar_baldes(capacidade)
        for entrada in entradas:
            self._baldes[self.indice(entrada.chave)].inserir_fim(entrada)
        self._redimensionamentos += 1

    def rastrear(self, chave: str) -> dict:
        indice = self.indice(chave)
        visitadas = []
        encontrada = False
        for entrada in self._baldes[indice]:
            visitadas.append(entrada.chave)
            if entrada.chave == chave:
                encontrada = True
                break
        return {"chave": chave, "codigo": self.codigo(chave), "indice": indice,
                "metodo": self.metodo, "encontrada": encontrada,
                "comparacoes": len(visitadas), "chaves_visitadas": visitadas}

    def estatisticas(self) -> dict:
        baldes = [{"indice": i, "chaves": [item.chave for item in balde]} for i, balde in enumerate(self._baldes)]
        ocupados = sum(bool(balde["chaves"]) for balde in baldes)
        return {"metodo": self.metodo, "capacidade": len(self._baldes), "quantidade": len(self),
                "fator_carga": len(self) / len(self._baldes), "baldes_ocupados": ocupados,
                "colisoes_atuais": len(self) - ocupados,
                "maior_cadeia": max(len(balde["chaves"]) for balde in baldes),
                "redimensionamentos": self._redimensionamentos, "baldes": baldes}

    @classmethod
    def demonstrar(cls, metodo="divisao") -> dict:
        """Cenário isolado e determinístico; não remove ordens reais."""
        tabela = cls(5, metodo, redimensionar=False)
        alvo = tabela.indice("EX-0")
        chaves = []
        for i in range(1000):
            chave = f"EX-{i}"
            if tabela.indice(chave) == alvo:
                chaves.append(chave)
            if len(chaves) == 3:
                break
        for i, chave in enumerate(chaves):
            tabela.inserir(chave, f"Registro de exemplo {i + 1}")
        antes = tabela.estatisticas()
        busca = tabela.rastrear(chaves[-1])
        tabela.remover(chaves[1])
        return {"aviso": "Exemplo isolado: nenhuma ordem real é excluída.", "inseridas": chaves,
                "antes": antes, "busca": busca, "removida": chaves[1], "depois": tabela.estatisticas(),
                "busca_apos_remocao": tabela.rastrear(chaves[-1])}
