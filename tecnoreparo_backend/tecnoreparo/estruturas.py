"""TADs implementados para estudo, sem collections.deque.

A lista nativa aparece somente como armazenamento de capacidade fixa do vetor.
Listas temporárias de apresentação são construídas fora das operações dos TADs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, Generic, Iterator, TypeVar

T = TypeVar("T")


class EstruturaVaziaError(IndexError):
    """Operação de remoção/consulta em estrutura vazia."""


class ColecaoLinear(ABC, Generic[T]):
    """Contrato comum: tamanho, percurso e consulta de vazio."""

    @abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __iter__(self) -> Iterator[T]:
        raise NotImplementedError

    def esta_vazia(self) -> bool:
        return len(self) == 0


@dataclass(frozen=True)
class ResultadoBusca:
    indice: int | None
    comparacoes: int


class VetorFixo(Generic[T]):
    """Vetor de B posições: acesso O(1), busca sequencial O(B).

    None representa posição livre. Não há append nem aumento de capacidade.
    A list do Python simula o bloco de referências de um vetor.
    """

    def __init__(self, capacidade: int):
        if type(capacidade) is not int or capacidade <= 0:
            raise ValueError("A capacidade deve ser um inteiro positivo.")
        self._dados: list[T | None] = [None] * capacidade

    def __len__(self) -> int:
        return len(self._dados)

    def __iter__(self) -> Iterator[T | None]:
        return iter(self._dados)

    def _validar_indice(self, indice: int) -> None:
        if type(indice) is not int or not 0 <= indice < len(self):
            raise IndexError("Índice fora dos limites do vetor.")

    def __getitem__(self, indice: int) -> T | None:
        self._validar_indice(indice)
        return self._dados[indice]

    def __setitem__(self, indice: int, valor: T | None) -> None:
        self._validar_indice(indice)
        self._dados[indice] = valor

    def buscar(self, valor: T | None) -> ResultadoBusca:
        for indice, atual in enumerate(self._dados):
            if atual == valor:
                return ResultadoBusca(indice, indice + 1)
        return ResultadoBusca(None, len(self))

    def contar_ocupados_recursivo(self) -> int:
        """Recursão dupla: duas chamadas sobre metades disjuntas.

        T(B)=2T(B/2)+O(1): O(B) tempo e O(log B) de pilha de chamadas.
        Não cria cópias/fatias do vetor.
        """
        def contar(inicio: int, fim: int) -> int:
            if inicio == fim:
                return 0
            if fim - inicio == 1:
                return int(self._dados[inicio] is not None)
            meio = (inicio + fim) // 2
            return contar(inicio, meio) + contar(meio, fim)

        return contar(0, len(self))


@dataclass(eq=False, slots=True)
class _NoSimples(Generic[T]):
    valor: T
    proximo: _NoSimples[T] | None = None


class ListaEncadeada(ColecaoLinear[T]):
    """Lista simplesmente encadeada com ponteiros de início e fim."""

    def __init__(self):
        self._inicio: _NoSimples[T] | None = None
        self._fim: _NoSimples[T] | None = None
        self._tamanho = 0

    def __len__(self) -> int:
        return self._tamanho

    def __iter__(self) -> Iterator[T]:
        atual = self._inicio
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def inserir_inicio(self, valor: T) -> None:
        novo = _NoSimples(valor, self._inicio)
        self._inicio = novo
        if self._fim is None:
            self._fim = novo
        self._tamanho += 1

    def inserir_fim(self, valor: T) -> None:
        novo = _NoSimples(valor)
        if self._fim is None:
            self._inicio = novo
        else:
            self._fim.proximo = novo
        self._fim = novo
        self._tamanho += 1

    def primeiro(self) -> T:
        if self._inicio is None:
            raise EstruturaVaziaError("A lista está vazia.")
        return self._inicio.valor

    def remover_inicio(self) -> T:
        valor = self.primeiro()
        assert self._inicio is not None
        self._inicio = self._inicio.proximo
        self._tamanho -= 1
        if self._inicio is None:
            self._fim = None
        return valor

    def buscar(self, predicado: Callable[[T], bool]) -> T | None:
        for valor in self:
            if predicado(valor):
                return valor
        return None

    def remover_primeiro(self, predicado: Callable[[T], bool]) -> T:
        """Localiza e remove o primeiro nó correspondente: O(n) no pior caso."""
        anterior = None
        atual = self._inicio
        while atual is not None:
            if predicado(atual.valor):
                if anterior is None:
                    self._inicio = atual.proximo
                else:
                    anterior.proximo = atual.proximo
                if atual is self._fim:
                    self._fim = anterior
                self._tamanho -= 1
                return atual.valor
            anterior = atual
            atual = atual.proximo
        raise ValueError("Elemento não encontrado na lista.")

    def contar_recursivo(self) -> int:
        """Recursão simples: C(no)=1+C(no.proximo), C(None)=0.

        O(n) tempo e O(n) memória de chamadas. A operação é didática:
        limitada a 200 nós, para não esgotar a pilha de chamadas do Python.
        O uso cotidiano de len(lista) é O(1) e não tem esse limite.
        """
        if len(self) > 200:
            raise ValueError("A demonstração recursiva aceita até 200 nós.")

        def contar(no: _NoSimples[T] | None) -> int:
            if no is None:
                return 0
            return 1 + contar(no.proximo)

        return contar(self._inicio)


class Fila(ColecaoLinear[T]):
    """FIFO por composição: insere no fim, retira do início, ambos O(1)."""

    def __init__(self):
        self._itens: ListaEncadeada[T] = ListaEncadeada()

    def __len__(self) -> int:
        return len(self._itens)

    def __iter__(self) -> Iterator[T]:
        return iter(self._itens)

    def enfileirar(self, valor: T) -> None:
        self._itens.inserir_fim(valor)

    def desenfileirar(self) -> T:
        return self._itens.remover_inicio()

    def consultar_inicio(self) -> T:
        return self._itens.primeiro()


class Pilha(ColecaoLinear[T]):
    """LIFO: início da lista representa o topo. Push/pop O(1)."""

    def __init__(self):
        self._itens: ListaEncadeada[T] = ListaEncadeada()

    def __len__(self) -> int:
        return len(self._itens)

    def __iter__(self) -> Iterator[T]:
        """Percorre do topo para a base."""
        return iter(self._itens)

    def empilhar(self, valor: T) -> None:
        self._itens.inserir_inicio(valor)

    def desempilhar(self) -> T:
        return self._itens.remover_inicio()

    def consultar_topo(self) -> T:
        return self._itens.primeiro()


@dataclass(eq=False, slots=True)
class _NoDuplo(Generic[T]):
    valor: T
    anterior: _NoDuplo[T] | None = None
    proximo: _NoDuplo[T] | None = None


class Deque(ColecaoLinear[T]):
    """Fila de duas extremidades, baseada em nós duplamente encadeados.

    As quatro operações nas pontas são O(1). Deque não é heap nem fila
    com ordenação automática por prioridade.
    """

    def __init__(self):
        self._inicio: _NoDuplo[T] | None = None
        self._fim: _NoDuplo[T] | None = None
        self._tamanho = 0

    def __len__(self) -> int:
        return self._tamanho

    def __iter__(self) -> Iterator[T]:
        atual = self._inicio
        while atual is not None:
            yield atual.valor
            atual = atual.proximo

    def inserir_inicio(self, valor: T) -> None:
        novo = _NoDuplo(valor, proximo=self._inicio)
        if self._inicio is None:
            self._fim = novo
        else:
            self._inicio.anterior = novo
        self._inicio = novo
        self._tamanho += 1

    def inserir_fim(self, valor: T) -> None:
        novo = _NoDuplo(valor, anterior=self._fim)
        if self._fim is None:
            self._inicio = novo
        else:
            self._fim.proximo = novo
        self._fim = novo
        self._tamanho += 1

    def consultar_inicio(self) -> T:
        if self._inicio is None:
            raise EstruturaVaziaError("O deque está vazio.")
        return self._inicio.valor

    def consultar_fim(self) -> T:
        if self._fim is None:
            raise EstruturaVaziaError("O deque está vazio.")
        return self._fim.valor

    def remover_inicio(self) -> T:
        valor = self.consultar_inicio()
        assert self._inicio is not None
        antigo = self._inicio
        self._inicio = antigo.proximo
        if self._inicio is None:
            self._fim = None
        else:
            self._inicio.anterior = None
        antigo.proximo = None
        self._tamanho -= 1
        return valor

    def remover_fim(self) -> T:
        valor = self.consultar_fim()
        assert self._fim is not None
        antigo = self._fim
        self._fim = antigo.anterior
        if self._fim is None:
            self._inicio = None
        else:
            self._fim.proximo = None
        antigo.anterior = None
        self._tamanho -= 1
        return valor
