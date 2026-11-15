import base64
import io
import json
import random
import struct
import threading
import unittest
from urllib.request import Request, urlopen
from wsgiref.simple_server import WSGIRequestHandler, make_server
from wsgiref.util import setup_testing_defaults
from wsgiref.validate import validator

from tecnoreparo import TecnoReparo
from tecnoreparo.api import ApiTecnoReparo
from tecnoreparo.grafo import GrafoRotas
from tecnoreparo.graficos import Graficos
from tecnoreparo.modelos import ConflitoError, NaoEncontradoError, ValidacaoError
from tecnoreparo.ordenacao import ComparadorOrdenacao, Ordenador
from tecnoreparo.tabela_hash import TabelaHash
from tecnoreparo.web import AplicacaoTecnoReparo


def cadastrar(servico, nome, serie):
    return servico.registrar_ordem(nome_cliente=nome, contato="Fictício", numero_serie=serie,
                                  tipo="Notebook", defeito="Teste acadêmico")


class TestHash(unittest.TestCase):
    def test_colisoes_busca_atualizacao_e_remocao_em_todos_os_metodos(self):
        for metodo in TabelaHash.METODOS:
            with self.subTest(metodo=metodo):
                tabela = TabelaHash(5, metodo, False)
                chaves = [f"OS-{i}" for i in range(300) if tabela.indice(f"OS-{i}") == 0][:4]
                self.assertEqual(len(chaves), 4)
                for i, chave in enumerate(chaves):
                    tabela.inserir(chave, i)
                self.assertEqual(tabela.rastrear(chaves[-1])["comparacoes"], 4)
                tabela.inserir(chaves[1], 55)
                self.assertEqual(len(tabela), 4)
                self.assertEqual(tabela[chaves[1]], 55)
                for chave in (chaves[1], chaves[0], chaves[-1]):
                    tabela.remover(chave)
                    self.assertNotIn(chave, tabela)
                    self.assertEqual(tabela[chaves[2]], 2)
                self.assertEqual(list(tabela), [chaves[2]])
                self.assertEqual(tabela.remover(chaves[2]), 2)
                self.assertEqual(tabela.estatisticas()["quantidade"], 0)
                with self.assertRaises(KeyError):
                    tabela.remover("inexistente")
                with self.assertRaises(KeyError):
                    tabela.buscar("inexistente")

    def test_redimensionamento_preserva_valores_unicode_e_ordem(self):
        for metodo in TabelaHash.METODOS:
            tabela = TabelaHash(3, metodo)
            chaves = [f"Ordem-ação-{i}" for i in range(100)]
            objetos = [object() for _ in chaves]
            for chave, objeto in zip(chaves, objetos):
                tabela[chave] = objeto
            self.assertEqual(list(tabela), chaves)
            self.assertEqual(list(tabela.values()), objetos)
            self.assertGreater(tabela.estatisticas()["redimensionamentos"], 0)
            self.assertLessEqual(tabela.estatisticas()["fator_carga"], .75)

    def test_exemplo_isolado_e_reindexacao_preservam_atendimentos(self):
        servico = TecnoReparo()
        for i in range(30):
            cadastrar(servico, f"Cliente {i}", str(i))
        servico.atender_proximo()
        antes = servico.listar_ordens()
        estado = servico.estado()
        for metodo in TabelaHash.METODOS:
            servico.configurar_indice(metodo)
            self.assertEqual(servico.listar_ordens(), antes)
            self.assertEqual(servico.estado(), estado)
            exemplo = servico.demonstrar_hash(metodo)
            self.assertTrue(exemplo["busca_apos_remocao"]["encontrada"])
            self.assertEqual(exemplo["antes"]["colisoes_atuais"], 2)
            self.assertEqual(exemplo["depois"]["colisoes_atuais"], 1)
            self.assertEqual(servico.listar_ordens(), antes)

    def test_chave_invalida_nao_altera_tabela(self):
        tabela = TabelaHash()
        for chave in (None, "", 4, [], {}):
            with self.subTest(chave=chave), self.assertRaises(ValueError):
                tabela.inserir(chave, "x")
        self.assertEqual(len(tabela), 0)


class TestOrdenacao(unittest.TestCase):
    def test_quatro_algoritmos_ordenam_e_preservam_multiconjunto(self):
        rng = random.Random(42)
        entradas = [[], [2], [3, -1, 3, 0, -5], list(range(100)), list(range(100, 0, -1)),
                    [7] * 100, [rng.randint(-50, 50) for _ in range(250)]]
        for metodo in Ordenador.NOMES:
            for base in entradas:
                with self.subTest(metodo=metodo, tamanho=len(base)):
                    dados = list(base)
                    self.assertIs(Ordenador().ordenar(dados, metodo), dados)
                    self.assertEqual(dados, sorted(base))

    def test_chave_por_campo_e_estabilidade_dos_metodos_estaveis(self):
        base = [{"nome": "Z", "id": 1}, {"nome": "A", "id": 2}, {"nome": "Z", "id": 3}]
        for metodo in Ordenador.NOMES:
            resultado = Ordenador().ordenar(list(base), metodo, lambda d: d["nome"])
            self.assertEqual([d["nome"] for d in resultado], ["A", "Z", "Z"])
            self.assertEqual({d["id"] for d in resultado}, {1, 2, 3})
            if metodo in ("bolha", "insercao"):
                self.assertEqual([d["id"] for d in resultado], [2, 1, 3])

    def test_ordenar_ordens_reais_nao_reordena_fila_ou_cadastro(self):
        servico = TecnoReparo()
        for i, nome in enumerate(("Zelia", "Ana", "Bruno")):
            cadastrar(servico, nome, str(i))
        original = servico.listar_ordens()
        fila = servico.estado()["fila"]
        for metodo in Ordenador.NOMES:
            ordens = servico.listar_ordens(ordenar_por="cliente", metodo=metodo)
            self.assertEqual([o["cliente"]["nome"] for o in ordens], ["Ana", "Bruno", "Zelia"])
            self.assertEqual(servico.estado()["fila"], fila)
            self.assertEqual(servico.listar_ordens(), original)
        self.assertEqual(servico.atender_proximo()["id"], "OS-0001")

    def test_comparacao_tamanhos_medidas_e_reprodutibilidade(self):
        comparador = ComparadorOrdenacao()
        for cenario in comparador.CENARIOS:
            a = comparador.executar(24, cenario, 2, 9)
            b = comparador.executar(24, cenario, 2, 9)
            self.assertEqual(a["tamanhos"], [6, 12, 24])
            self.assertEqual(len(a["resultados"]), 12)
            for r, outro in zip(a["resultados"], b["resultados"]):
                self.assertEqual(len(r["tempos_ms"]), 2)
                self.assertLessEqual(r["minimo_ms"], r["mediana_ms"])
                self.assertLessEqual(r["mediana_ms"], r["maximo_ms"])
                self.assertGreaterEqual(r["minimo_ms"], 0)
                self.assertEqual(r["comparacoes"], outro["comparacoes"])
                self.assertEqual(r["movimentos"], outro["movimentos"])

    def test_parametros_invalidos(self):
        for argumentos in ({"tamanho": True}, {"tamanho": 1}, {"tamanho": 501}, {"repeticoes": 0},
                           {"repeticoes": 8}, {"semente": -1}, {"cenario": []}):
            with self.subTest(argumentos=argumentos), self.assertRaises(ValidacaoError):
                ComparadorOrdenacao().executar(**argumentos)
        for metodo in ("sorted", None, [], {}):
            with self.assertRaises(ValidacaoError):
                Ordenador().ordenar([2, 1], metodo)


class TestGrafo(unittest.TestCase):
    def setUp(self):
        self.grafo = GrafoRotas()
        self.ids = [self.grafo.adicionar_ponto(nome, -10 + i * .01, -36)["id"]
                    for i, nome in enumerate(("Oficina", "Apoio", "Entrega", "Isolado"))]
        a, b, c, _ = self.ids
        self.grafo.conectar(a, b, 1)
        self.grafo.conectar(b, c, 2)
        self.grafo.conectar(a, c, 10)

    def test_dijkstra_considera_pesos_e_bfs_conectividade(self):
        a, b, c, isolado = self.ids
        rota = self.grafo.menor_caminho(a, c)
        self.assertEqual(rota["caminho"], [a, b, c])
        self.assertEqual(rota["distancia_km"], 3)
        self.assertEqual(set(self.grafo.alcancaveis(a)), {a, b, c})
        self.assertEqual(self.grafo.menor_caminho(c, a)["caminho"], [c, b, a])
        self.assertNotIn(isolado, rota["alcancaveis_bfs"])

    def test_mesmo_local_e_destino_desconectado(self):
        a, _, _, isolado = self.ids
        self.assertEqual(self.grafo.menor_caminho(a, a)["distancia_km"], 0)
        self.assertEqual(self.grafo.menor_caminho(a, a)["caminho"], [a])
        rota = self.grafo.menor_caminho(a, isolado)
        self.assertFalse(rota["encontrada"])
        self.assertIsNone(rota["distancia_km"])
        self.assertEqual(rota["caminho"], [])
        json.dumps(rota, allow_nan=False)

    def test_remover_vertice_limpa_arestas_e_atualizacao_nao_duplica(self):
        a, b, c, _ = self.ids
        self.grafo.conectar(a, c, 1)
        self.assertEqual(len(self.grafo.estado()["trechos"]), 3)
        self.assertEqual(self.grafo.menor_caminho(a, c)["distancia_km"], 1)
        self.grafo.remover_ponto(b)
        self.assertEqual(len(self.grafo.estado()["trechos"]), 1)
        self.grafo.desconectar(a, c)
        self.assertFalse(self.grafo.menor_caminho(a, c)["encontrada"])
        with self.assertRaises(NaoEncontradoError):
            self.grafo.menor_caminho(a, b)

    def test_haversine_e_coordenadas(self):
        grafo = GrafoRotas()
        a = grafo.adicionar_ponto("A", 0, 0)["id"]
        b = grafo.adicionar_ponto("B", 0, 1)["id"]
        trecho = grafo.conectar(a, b)
        self.assertAlmostEqual(trecho["distancia_km"], 111.195, places=2)
        self.assertEqual(trecho["medida"], "geografica_aproximada")
        estado = grafo.estado()
        estado["pontos"][0]["nome"] = "Modificado"
        self.assertEqual(grafo.estado()["pontos"][0]["nome"], "A")

    def test_pesos_e_coordenadas_invalidos_nao_alteram_rede(self):
        a, b, _, _ = self.ids
        antes = self.grafo.estado()
        for peso in (0, -1, True, "2", float("nan"), float("inf"), 40076):
            with self.subTest(peso=peso), self.assertRaises(ValidacaoError):
                self.grafo.conectar(a, b, peso)
        for lat, lon in ((91, 0), (0, -181), (True, 1), (0, float("nan"))):
            with self.assertRaises(ValidacaoError):
                self.grafo.adicionar_ponto("X", lat, lon)
        self.assertEqual(self.grafo.estado(), antes)
        with self.assertRaises(ValidacaoError):
            self.grafo.conectar(a, a, 1)

    def test_vinculo_ordem_e_exemplo_nao_sobrescreve_rede(self):
        servico = TecnoReparo()
        cadastrar(servico, "Teste", "1")
        servico.exemplo_rotas()
        self.assertEqual(servico.estado_rotas()["pontos"][2]["ordem_id"], "OS-0001")
        rota = servico._rotas.menor_caminho("P-0001", "P-0005")
        self.assertEqual(rota["caminho"], ["P-0001", "P-0002", "P-0004", "P-0005"])
        self.assertAlmostEqual(rota["distancia_km"], 3.2)
        with self.assertRaises(ConflitoError):
            servico.exemplo_rotas()
        with self.assertRaises(NaoEncontradoError):
            servico.cadastrar_local("X", 0, 0, "OS-9999")


class TestGraficosEAPI(unittest.TestCase):
    def setUp(self):
        self.servico = TecnoReparo()
        self.app = ApiTecnoReparo(self.servico)

    def requisicao(self, metodo, caminho, dados=None):
        environ = {}
        setup_testing_defaults(environ)
        path, _, query = caminho.partition("?")
        corpo = json.dumps(dados).encode() if dados is not None else b""
        environ.update(REQUEST_METHOD=metodo, PATH_INFO=path, QUERY_STRING=query,
                       CONTENT_TYPE="application/json", CONTENT_LENGTH=str(len(corpo)))
        environ["wsgi.input"] = io.BytesIO(corpo)
        status = []
        resultado = validator(self.app)(environ, lambda s, h, exc_info=None: status.append(int(s.split()[0])))
        try:
            resposta = json.loads(b"".join(resultado))
        finally:
            resultado.close()
        return status[0], resposta

    def conferir_png(self, uri):
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        png = base64.b64decode(uri.split(",", 1)[1], validate=True)
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        largura, altura = struct.unpack(">II", png[16:24])
        self.assertGreater(largura, 800)
        self.assertGreater(altura, 400)

    def test_api_hash_ordenacao_e_validacao(self):
        cadastrar(self.servico, "Zelia", "Z")
        cadastrar(self.servico, "Ana", "A")
        for metodo in TabelaHash.METODOS:
            status, resposta = self.requisicao("POST", "/api/indice/configurar", {"metodo": metodo})
            self.assertEqual(status, 200)
            self.assertEqual(resposta["dados"]["quantidade"], 2)
            status, resposta = self.requisicao("GET", "/api/indice/consulta?chave=OS-0002")
            self.assertEqual(resposta["dados"]["ordem"]["cliente"]["nome"], "Ana")
        status, resposta = self.requisicao("GET", "/api/ordens?ordenar_por=cliente&metodo=insercao")
        self.assertEqual(status, 200)
        self.assertEqual(resposta["dados"][0]["id"], "OS-0002")
        self.assertEqual(self.requisicao("GET", "/api/ordens?descendente=sim")[0], 400)
        for caminho, dados in (("/api/indice/configurar", {"metodo": []}),
                                ("/api/analises/ordenacao", {"tamanho": True}),
                                ("/api/rotas/pontos", {"nome": "X", "latitude": 91, "longitude": 0}),
                                ("/api/rotas/conexoes", {})):
            self.assertEqual(self.requisicao("POST", caminho, dados)[0], 400)

    def test_api_rotas_e_graficos_reais(self):
        self.assertEqual(self.requisicao("POST", "/api/rotas/exemplo", {})[0], 201)
        status, resposta = self.requisicao("POST", "/api/rotas/calcular", {"origem": "P-0001", "destino": "P-0005"})
        self.assertEqual(status, 200)
        self.assertAlmostEqual(resposta["dados"]["distancia_km"], 3.2)
        self.conferir_png(resposta["dados"]["grafico"])
        status, resposta = self.requisicao("POST", "/api/analises/ordenacao", {"tamanho": 12, "repeticoes": 1})
        self.assertEqual(status, 200)
        self.assertEqual(len(resposta["dados"]["resultados"]), 12)
        self.conferir_png(resposta["dados"]["grafico"])
        self.assertEqual(self.requisicao("DELETE", "/api/rotas/pontos/P-0006")[0], 200)
        self.assertEqual(self.requisicao("GET", "/api/rotas")[1]["dados"]["pontos"][-1]["id"], "P-0005")

    def test_grafico_rede_vazia_e_nome_com_sintaxe_matematica(self):
        self.conferir_png(Graficos.rede(self.servico.estado_rotas()))
        self.servico.cadastrar_local(r"$\invalidlatex$ <teste>", 0, 0)
        self.conferir_png(Graficos.rede(self.servico.estado_rotas()))

    def test_servidor_http_real_entrega_modulo_e_novas_operacoes(self):
        class Silencioso(WSGIRequestHandler):
            def log_message(self, *args):
                pass
        app = AplicacaoTecnoReparo(self.app)
        with make_server("127.0.0.1", 0, app, handler_class=Silencioso) as servidor:
            thread = threading.Thread(target=servidor.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{servidor.server_port}"
            try:
                with urlopen(base + "/assets/unidade2.js", timeout=5) as resposta:
                    self.assertIn(b"TecnoUnidade2", resposta.read())
                dados = json.dumps({"nome": "Coleta", "latitude": -10, "longitude": -36}).encode()
                req = Request(base + "/api/rotas/pontos", data=dados, headers={"Content-Type": "application/json"})
                with urlopen(req, timeout=5) as resposta:
                    self.assertEqual(resposta.status, 201)
                    self.assertEqual(json.load(resposta)["dados"]["id"], "P-0001")
                with urlopen(base + "/api/rotas", timeout=5) as resposta:
                    self.assertEqual(len(json.load(resposta)["dados"]["pontos"]), 1)
            finally:
                servidor.shutdown()
                thread.join(timeout=3)
