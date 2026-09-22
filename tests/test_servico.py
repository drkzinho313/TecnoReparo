import unittest

from tecnoreparo import TecnoReparo
from tecnoreparo.modelos import ConflitoError, NaoEncontradoError, ValidacaoError


class TestServico(unittest.TestCase):
    def setUp(self):
        self.sistema = TecnoReparo(2)

    def cadastrar(self, serie="PC-1", **extras):
        dados = dict(
            nome_cliente="Cliente fictício", contato="Contato de teste",
            numero_serie=serie, tipo="Desktop", defeito="Não liga",
            sintomas=["Não liga", "não liga", "Sem imagem"],
        )
        dados.update(extras)
        return self.sistema.registrar_ordem(**dados)["id"]

    def marcar_todas(self, identificador):
        for etapa in self.sistema.obter_ordem(identificador)["etapas"]:
            self.sistema.marcar_etapa(identificador, etapa["id"], True)

    def finalizada(self, serie):
        identificador = self.cadastrar(serie)
        self.sistema.atender_proximo()
        self.marcar_todas(identificador)
        self.sistema.concluir_atendimento(identificador)
        return identificador

    def test_cadastro_normaliza_conjuntos(self):
        identificador = self.cadastrar(" pc-1 ")
        ordem = self.sistema.obter_ordem(identificador)
        self.assertEqual(ordem["equipamento"]["numero_serie"], "PC-1")
        self.assertEqual(ordem["sintomas"], ["não liga", "sem imagem"])
        self.assertEqual(self.sistema.estado()["fila"], [identificador])

    def test_duplicado_ativo_nao_muda_fila(self):
        self.cadastrar()
        antes = self.sistema.estado()
        with self.assertRaises(ConflitoError):
            self.cadastrar("pc-1")
        self.assertEqual(self.sistema.estado(), antes)

    def test_validacao_de_cadastro_antes_de_mutar(self):
        for campo, valor in (
            ("nome_cliente", ""), ("contato", 42), ("numero_serie", None),
            ("sintomas", "não liga"), ("sintomas", [1]), ("defeito", "x" * 501),
        ):
            with self.subTest(campo=campo), self.assertRaises(ValidacaoError):
                self.cadastrar(**{campo: valor})
        self.assertEqual(self.sistema.estado()["total_ordens"], 0)

    def test_fifo_e_bancadas_cheias_preservam_espera(self):
        ids = [self.cadastrar(f"PC-{i}") for i in range(3)]
        self.assertEqual(self.sistema.atender_proximo()["id"], ids[0])
        self.assertEqual(self.sistema.atender_proximo()["id"], ids[1])
        antes = self.sistema.estado()
        with self.assertRaises(ConflitoError):
            self.sistema.atender_proximo()
        self.assertEqual(self.sistema.estado(), antes)

    def test_fila_vazia_e_origem_invalida(self):
        with self.assertRaises(ConflitoError):
            self.sistema.atender_proximo()
        with self.assertRaises(ValidacaoError):
            self.sistema.atender_proximo("inexistente")

    def test_operacoes_exigem_atendimento(self):
        identificador = self.cadastrar()
        for operacao in (
            lambda: self.sistema.retirar_peca(identificador, "Tampa"),
            lambda: self.sistema.adicionar_etapa(identificador, "Limpeza"),
            lambda: self.sistema.concluir_atendimento(identificador),
        ):
            with self.assertRaises(ConflitoError):
                operacao()

    def test_pilha_e_conclusao_com_etapas_pendentes(self):
        identificador = self.cadastrar()
        self.sistema.atender_proximo()
        self.sistema.retirar_peca(identificador, "Tampa")
        self.sistema.retirar_peca(identificador, "RAM")
        with self.assertRaises(ConflitoError):
            self.sistema.concluir_atendimento(identificador)
        self.assertEqual(self.sistema.recolocar_peca(identificador)["peca_recolocada"], "RAM")
        self.assertEqual(self.sistema.recolocar_peca(identificador)["peca_recolocada"], "Tampa")
        with self.assertRaises(ConflitoError):
            self.sistema.recolocar_peca(identificador)
        with self.assertRaises(ConflitoError):
            self.sistema.concluir_atendimento(identificador)
        self.marcar_todas(identificador)
        self.sistema.concluir_atendimento(identificador)
        self.assertTrue(self.sistema.estado()["bancadas"][0]["livre"])
        with self.assertRaises(ConflitoError):
            self.sistema.concluir_atendimento(identificador)

    def test_etapas_ids_estaveis_e_pelo_menos_uma(self):
        identificador = self.cadastrar()
        self.sistema.atender_proximo()
        self.sistema.remover_etapa(identificador, 2)
        nova = self.sistema.adicionar_etapa(identificador, "Verificar cabos")
        self.assertEqual(nova["id"], 4)
        self.sistema.remover_etapa(identificador, 1)
        self.sistema.remover_etapa(identificador, 3)
        with self.assertRaises(ConflitoError):
            self.sistema.remover_etapa(identificador, 4)
        with self.assertRaises(NaoEncontradoError):
            self.sistema.marcar_etapa(identificador, 2, True)

    def test_validacao_de_booleanos_e_ids(self):
        identificador = self.cadastrar()
        self.sistema.atender_proximo()
        for etapa_id, concluida in ((True, True), (0, True), (1, "true"), (1, 1)):
            with self.subTest(etapa=etapa_id), self.assertRaises(ValidacaoError):
                self.sistema.marcar_etapa(identificador, etapa_id, concluida)

    def test_dados_de_ordens_sao_independentes(self):
        a, b = self.cadastrar("A"), self.cadastrar("B")
        self.sistema.atender_proximo()
        self.sistema.atender_proximo()
        self.sistema.adicionar_etapa(a, "Etapa exclusiva")
        self.sistema.retirar_peca(a, "RAM")
        outra = self.sistema.obter_ordem(b)
        self.assertEqual(len(outra["etapas"]), 3)
        self.assertEqual(outra["pecas_do_topo_para_base"], [])

    def test_resposta_nao_expoe_estado_mutavel(self):
        identificador = self.cadastrar()
        resposta = self.sistema.obter_ordem(identificador)
        resposta["etapas"][0]["descricao"] = "Alterada fora do serviço"
        resposta["historico"].clear()
        resposta["cliente"]["nome"] = "Outro"
        real = self.sistema.obter_ordem(identificador)
        self.assertEqual(real["etapas"][0]["descricao"], "Diagnóstico")
        self.assertTrue(real["historico"])
        self.assertEqual(real["cliente"]["nome"], "Cliente fictício")

    def test_copia_rasa_profunda_preservam_cadastro(self):
        identificador = self.cadastrar()
        antes = self.sistema.obter_ordem(identificador)
        demo = self.sistema.demonstrar_copias(identificador)
        self.assertTrue(demo["rasa_compartilha_lista_interna"])
        self.assertFalse(demo["profunda_compartilha_lista_interna"])
        self.assertTrue(demo["alterar_profunda_preservou_snapshot"])
        self.assertTrue(demo["ordem_real_preservada"])
        self.assertEqual(self.sistema.obter_ordem(identificador), antes)

    def test_recursao_aplicada(self):
        identificador = self.cadastrar()
        self.sistema.atender_proximo()
        resposta = self.sistema.analisar_recursao(identificador)
        self.assertEqual(resposta["simples"]["etapas_contadas"], 3)
        self.assertEqual(resposta["dupla"]["bancadas_ocupadas"], 1)

    def test_busca_melhor_medio_pior_e_ausente(self):
        dados = self.sistema.analisar_busca(8)
        self.assertEqual(dados["melhor_caso"]["comparacoes"], 1)
        self.assertEqual(dados["caso_medio"]["comparacoes"], 4.5)
        self.assertEqual(dados["pior_caso"]["comparacoes"], 8)
        self.assertEqual(dados["ausente"]["comparacoes"], 8)
        for invalido in (0, 501, True, "8"):
            with self.assertRaises(ValidacaoError):
                self.sistema.analisar_busca(invalido)

    def test_revisoes_urgentes_entram_no_inicio(self):
        a, b, c = [self.finalizada(serie) for serie in ("A", "B", "C")]
        self.sistema.solicitar_revisao(a, "Comum")
        self.sistema.solicitar_revisao(b, "Urgente 1", True)
        self.sistema.solicitar_revisao(c, "Urgente 2", True)
        self.assertEqual([p["ordem_id"] for p in self.sistema.estado()["revisoes"]], [c, b, a])
        atendida = self.sistema.atender_proximo("revisoes")
        self.assertEqual(atendida["id"], c)
        self.assertEqual(len(atendida["etapas"]), 5)
        with self.assertRaises(ConflitoError):
            self.sistema.concluir_atendimento(c)
        self.marcar_todas(c)
        self.sistema.concluir_atendimento(c)

    def test_cancelamento_pelas_duas_pontas_preserva_etapas(self):
        a, b = self.finalizada("A"), self.finalizada("B")
        self.sistema.solicitar_revisao(a, "Comum")
        self.sistema.solicitar_revisao(b, "Urgente", True)
        self.assertEqual(self.sistema.cancelar_revisao("fim")["id"], a)
        cancelada = self.sistema.cancelar_revisao("inicio")
        self.assertEqual(cancelada["id"], b)
        self.assertEqual(cancelada["status"], "concluida")
        self.assertTrue(all(e["concluida"] for e in cancelada["etapas"]))
        with self.assertRaises(ConflitoError):
            self.sistema.cancelar_revisao()

    def test_revisao_rejeita_duplicidade_e_urgencia_invalida(self):
        identificador = self.finalizada("A")
        with self.assertRaises(ValidacaoError):
            self.sistema.solicitar_revisao(identificador, "Motivo", "sim")
        self.sistema.solicitar_revisao(identificador, "Motivo")
        antes = self.sistema.estado()
        with self.assertRaises(ConflitoError):
            self.sistema.solicitar_revisao(identificador, "Novamente")
        self.assertEqual(self.sistema.estado(), antes)

    def test_mesmo_equipamento_pode_ter_nova_ordem_apos_conclusao(self):
        antiga = self.finalizada("A")
        nova = self.cadastrar("A")
        self.assertNotEqual(antiga, nova)
        with self.assertRaises(ConflitoError):
            self.sistema.solicitar_revisao(antiga, "Retorno antigo")
        self.assertEqual(self.sistema.obter_ordem(antiga)["status"], "concluida")

    def test_limite_etapas(self):
        identificador = self.cadastrar()
        self.sistema.atender_proximo()
        for i in range(197):
            self.sistema.adicionar_etapa(identificador, f"Etapa {i}")
        with self.assertRaises(ConflitoError):
            self.sistema.adicionar_etapa(identificador, "Excedente")
        self.assertEqual(self.sistema.analisar_recursao(identificador)["simples"]["etapas_contadas"], 200)

    def test_relatorios_e_filtros(self):
        identificador = self.cadastrar()
        self.cadastrar("Outro", tipo="Notebook")
        self.sistema.atender_proximo()
        relatorio = self.sistema.relatorio()
        self.assertEqual(relatorio["por_status"]["aguardando"], 1)
        self.assertEqual(relatorio["por_status"]["em_reparo"], 1)
        self.assertEqual(relatorio["tipos_de_equipamento"], ["Desktop", "Notebook"])
        self.assertEqual(relatorio["indices_bancadas_livres"], [1])
        self.assertEqual(self.sistema.listar_ordens("em_reparo")[0]["id"], identificador)
        with self.assertRaises(ValidacaoError):
            self.sistema.listar_ordens("invalido")

    def test_ordem_ausente_e_numero_bancadas(self):
        with self.assertRaises(NaoEncontradoError):
            self.sistema.obter_ordem("OS-9999")
        for numero in (0, True, 1001, "3"):
            with self.assertRaises(ValidacaoError):
                TecnoReparo(numero)


if __name__ == "__main__":
    unittest.main()
