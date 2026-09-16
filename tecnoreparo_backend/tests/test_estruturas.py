import random
import unittest
from collections import deque as DequeReferencia

from tecnoreparo.estruturas import (
    Deque, EstruturaVaziaError, Fila, ListaEncadeada, Pilha, VetorFixo,
)


class TestVetor(unittest.TestCase):
    def test_capacidade_e_indices(self):
        for capacidade in (0, -1, True, "3"):
            with self.subTest(capacidade=capacidade), self.assertRaises(ValueError):
                VetorFixo(capacidade)
        vetor = VetorFixo(3)
        vetor[1] = "OS-2"
        self.assertEqual(list(vetor), [None, "OS-2", None])
        for indice in (-1, 3, True, "0"):
            with self.subTest(indice=indice), self.assertRaises(IndexError):
                vetor[indice] = "fora"
        self.assertEqual(len(vetor), 3)

    def test_busca_conta_comparacoes(self):
        vetor = VetorFixo(4)
        for i in range(4):
            vetor[i] = i
        for alvo, esperado in ((0, 1), (2, 3), (3, 4), (99, 4)):
            with self.subTest(alvo=alvo):
                busca = vetor.buscar(alvo)
                self.assertEqual(busca.comparacoes, esperado)
                self.assertEqual(busca.indice, alvo if alvo < 4 else None)

    def test_recursao_dupla_com_tamanhos_pares_e_impares(self):
        for tamanho in (1, 2, 3, 7, 12):
            vetor = VetorFixo(tamanho)
            self.assertEqual(vetor.contar_ocupados_recursivo(), 0)
            for i in range(0, tamanho, 2):
                vetor[i] = "ocupado"
            self.assertEqual(vetor.contar_ocupados_recursivo(), (tamanho + 1) // 2)


class TestLista(unittest.TestCase):
    def test_insercao_e_percurso(self):
        lista = ListaEncadeada()
        lista.inserir_fim(2)
        lista.inserir_inicio(1)
        lista.inserir_fim(3)
        self.assertEqual(list(lista), [1, 2, 3])
        self.assertEqual(lista.primeiro(), 1)
        self.assertEqual(len(lista), 3)

    def test_remocao_reconecta_inicio_meio_fim(self):
        lista = ListaEncadeada()
        for i in range(5):
            lista.inserir_fim(i)
        for alvo, esperado in ((0, [1, 2, 3, 4]), (2, [1, 3, 4]), (4, [1, 3])):
            self.assertEqual(lista.remover_primeiro(lambda x: x == alvo), alvo)
            self.assertEqual(list(lista), esperado)
            self.assertEqual(len(lista), len(esperado))
        lista.inserir_fim(9)
        self.assertEqual(list(lista), [1, 3, 9])

    def test_ausente_nao_altera_lista(self):
        lista = ListaEncadeada()
        lista.inserir_fim("A")
        with self.assertRaises(ValueError):
            lista.remover_primeiro(lambda x: x == "B")
        self.assertEqual(list(lista), ["A"])
        self.assertIsNone(lista.buscar(lambda x: x == "B"))

    def test_reuso_apos_remover_unico_no(self):
        lista = ListaEncadeada()
        lista.inserir_fim("A")
        lista.remover_primeiro(lambda x: x == "A")
        self.assertTrue(lista.esta_vazia())
        lista.inserir_fim("B")
        self.assertEqual(lista.remover_inicio(), "B")
        lista.inserir_inicio("C")
        self.assertEqual(list(lista), ["C"])

    def test_vazia(self):
        lista = ListaEncadeada()
        for operacao in (lista.primeiro, lista.remover_inicio):
            with self.assertRaises(EstruturaVaziaError):
                operacao()

    def test_recursao_simples_e_limite_didatico(self):
        lista = ListaEncadeada()
        self.assertEqual(lista.contar_recursivo(), 0)
        for i in range(200):
            lista.inserir_fim(i)
        self.assertEqual(lista.contar_recursivo(), 200)
        lista.inserir_fim(200)
        with self.assertRaises(ValueError):
            lista.contar_recursivo()
        self.assertEqual(len(lista), 201)
        self.assertEqual(len(list(lista)), 201)


class TestFilaPilha(unittest.TestCase):
    def test_fila_fifo_e_consulta_sem_remover(self):
        fila = Fila()
        for item in ("A", "B", "C"):
            fila.enfileirar(item)
        self.assertEqual(fila.consultar_inicio(), "A")
        self.assertEqual(len(fila), 3)
        self.assertEqual([fila.desenfileirar() for _ in range(3)], ["A", "B", "C"])
        with self.assertRaises(EstruturaVaziaError):
            fila.desenfileirar()
        fila.enfileirar("D")
        self.assertEqual(fila.desenfileirar(), "D")

    def test_pilha_lifo_e_consulta_sem_remover(self):
        pilha = Pilha()
        for item in ("Tampa", "Memória", "Ventilador"):
            pilha.empilhar(item)
        self.assertEqual(pilha.consultar_topo(), "Ventilador")
        self.assertEqual(list(pilha), ["Ventilador", "Memória", "Tampa"])
        self.assertEqual([pilha.desempilhar() for _ in range(3)], ["Ventilador", "Memória", "Tampa"])
        with self.assertRaises(EstruturaVaziaError):
            pilha.consultar_topo()
        pilha.empilhar("Nova")
        self.assertEqual(pilha.desempilhar(), "Nova")

    def test_operacoes_intercaladas_contra_referencia(self):
        rng = random.Random(42)
        fila, referencia = Fila(), DequeReferencia()
        pilha, base = Pilha(), []
        for i in range(300):
            if not referencia or rng.choice((True, False)):
                fila.enfileirar(i)
                referencia.append(i)
                pilha.empilhar(i)
                base.append(i)
            else:
                self.assertEqual(fila.desenfileirar(), referencia.popleft())
                self.assertEqual(pilha.desempilhar(), base.pop())
            self.assertEqual(list(fila), list(referencia))
            self.assertEqual(list(pilha), list(reversed(base)))
            self.assertEqual(len(fila), len(referencia))


class TestDeque(unittest.TestCase):
    def test_quatro_extremidades(self):
        deque = Deque()
        deque.inserir_fim("comum")
        deque.inserir_inicio("urgente")
        self.assertEqual(deque.consultar_inicio(), "urgente")
        self.assertEqual(deque.consultar_fim(), "comum")
        self.assertEqual(deque.remover_fim(), "comum")
        self.assertEqual(deque.remover_inicio(), "urgente")
        self.assertTrue(deque.esta_vazia())

    def test_vazio_e_reuso_das_duas_pontas(self):
        deque = Deque()
        for remover in (deque.remover_inicio, deque.remover_fim):
            with self.assertRaises(EstruturaVaziaError):
                remover()
        deque.inserir_inicio(1)
        self.assertEqual(deque.remover_fim(), 1)
        deque.inserir_fim(2)
        self.assertEqual(deque.remover_inicio(), 2)
        self.assertEqual(len(deque), 0)

    def test_encadeamento_contra_deque_da_biblioteca(self):
        rng = random.Random(99)
        deque, referencia = Deque(), DequeReferencia()
        for i in range(500):
            operacao = rng.randrange(4) if referencia else rng.randrange(2)
            if operacao == 0:
                deque.inserir_inicio(i)
                referencia.appendleft(i)
            elif operacao == 1:
                deque.inserir_fim(i)
                referencia.append(i)
            elif operacao == 2:
                self.assertEqual(deque.remover_inicio(), referencia.popleft())
            else:
                self.assertEqual(deque.remover_fim(), referencia.pop())
            self.assertEqual(list(deque), list(referencia))
            self.assertEqual(len(deque), len(referencia))
            if referencia:
                self.assertEqual(deque.consultar_inicio(), referencia[0])
                self.assertEqual(deque.consultar_fim(), referencia[-1])


if __name__ == "__main__":
    unittest.main()
