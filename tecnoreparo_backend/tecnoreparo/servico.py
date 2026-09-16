"""Regras de negócio independentes de HTTP e de qualquer interface visual."""

from __future__ import annotations

from copy import copy, deepcopy

from .estruturas import Deque, Fila, VetorFixo
from .modelos import (
    ConflitoError,
    Equipamento,
    NaoEncontradoError,
    OrdemServico,
    PedidoRevisao,
    StatusOrdem,
    ValidacaoError,
)


def validar_texto(valor: object, campo: str, limite: int = 200) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValidacaoError(f"{campo} deve ser um texto não vazio.")
    valor = valor.strip()
    if len(valor) > limite:
        raise ValidacaoError(f"{campo} aceita no máximo {limite} caracteres.")
    return valor


class TecnoReparo:
    """Serviço em memória, com transições validadas antes das alterações."""

    LIMITE_ETAPAS = 200

    def __init__(self, quantidade_bancadas: int = 3):
        if type(quantidade_bancadas) is not int or not 1 <= quantidade_bancadas <= 1000:
            raise ValidacaoError("Use de 1 a 1000 bancadas.")
        self._bancadas: VetorFixo[str] = VetorFixo(quantidade_bancadas)
        self._fila: Fila[str] = Fila()
        self._revisoes: Deque[PedidoRevisao] = Deque()
        self._ordens: dict[str, OrdemServico] = {}
        self._series_ativas: set[str] = set()
        self._proximo_id = 1

    def _ordem(self, ordem_id: str) -> OrdemServico:
        ordem_id = validar_texto(ordem_id, "ordem_id", 30)
        if ordem_id not in self._ordens:
            raise NaoEncontradoError("Ordem de serviço não encontrada.")
        return self._ordens[ordem_id]

    def _em_reparo(self, ordem_id: str) -> OrdemServico:
        ordem = self._ordem(ordem_id)
        if ordem.status != StatusOrdem.EM_REPARO:
            raise ConflitoError("A ordem precisa estar em uma bancada, em reparo.")
        return ordem

    @staticmethod
    def _validar_id_etapa(etapa_id: int) -> None:
        if type(etapa_id) is not int or etapa_id <= 0:
            raise ValidacaoError("O identificador da etapa deve ser um inteiro positivo.")

    def registrar_ordem(
        self,
        *,
        nome_cliente: str,
        contato: str,
        numero_serie: str,
        tipo: str,
        defeito: str,
        sintomas: list[str] | tuple[str, ...] | set[str] | None = None,
    ) -> dict:
        nome = validar_texto(nome_cliente, "nome_cliente", 100)
        contato = validar_texto(contato, "contato", 100)
        serie = validar_texto(numero_serie, "numero_serie", 80).upper()
        tipo = validar_texto(tipo, "tipo", 80)
        defeito = validar_texto(defeito, "defeito", 500)
        if sintomas is None:
            sintomas = []
        if not isinstance(sintomas, (list, tuple, set)) or len(sintomas) > 30:
            raise ValidacaoError("sintomas deve ser uma coleção de até 30 textos.")
        # Compreensão de conjunto remove duplicações e normaliza a escrita.
        sintomas_unicos = {validar_texto(s, "sintoma", 80).casefold() for s in sintomas}
        if serie in self._series_ativas:
            raise ConflitoError("Já existe uma ordem ativa para esse número de série.")
        identificador = f"OS-{self._proximo_id:04d}"
        equipamento = Equipamento(serie, tipo, defeito)
        ordem = OrdemServico(identificador, (nome, contato), equipamento, sintomas_unicos)
        self._ordens[identificador] = ordem
        self._series_ativas.add(serie)
        self._fila.enfileirar(identificador)
        self._proximo_id += 1
        return ordem.para_dict()

    def obter_ordem(self, ordem_id: str) -> dict:
        return self._ordem(ordem_id).para_dict()

    def listar_ordens(self, status: str | None = None) -> list[dict]:
        if status is not None and (
            not isinstance(status, str) or status not in {s.value for s in StatusOrdem}
        ):
            raise ValidacaoError("Status inválido.")
        # Compreensão de lista para filtrar sem alterar o cadastro.
        return [
            ordem.para_dict()
            for ordem in self._ordens.values()
            if status is None or ordem.status.value == status
        ]

    def atender_proximo(self, origem: str = "fila") -> dict:
        """A seleção da origem é explícita: FIFO comum ou deque de revisões."""
        if origem not in ("fila", "revisoes"):
            raise ValidacaoError("origem deve ser 'fila' ou 'revisoes'.")
        if origem == "fila" and self._fila.esta_vazia():
            raise ConflitoError("A fila comum está vazia.")
        if origem == "revisoes" and self._revisoes.esta_vazia():
            raise ConflitoError("O deque de revisões está vazio.")
        busca = self._bancadas.buscar(None)
        if busca.indice is None:
            raise ConflitoError("Todas as bancadas estão ocupadas.")
        # Só retira da fila/deque depois de confirmar uma bancada disponível.
        if origem == "fila":
            ordem = self._ordem(self._fila.desenfileirar())
        else:
            pedido = self._revisoes.remover_inicio()
            ordem = self._ordem(pedido.ordem_id)
            ordem.adicionar_etapa("Revisão: " + pedido.motivo)
            ordem.adicionar_etapa("Teste final da revisão")
        ordem.status = StatusOrdem.EM_REPARO
        ordem.bancada = busca.indice
        self._bancadas[busca.indice] = ordem.id
        ordem.historico.append(f"Atendimento iniciado na bancada de índice {busca.indice}.")
        return ordem.para_dict()

    def adicionar_etapa(self, ordem_id: str, descricao: str) -> dict:
        descricao = validar_texto(descricao, "descricao", 200)
        ordem = self._em_reparo(ordem_id)
        if len(ordem.etapas) >= self.LIMITE_ETAPAS:
            raise ConflitoError("Limite de 200 etapas por ordem atingido.")
        etapa = ordem.adicionar_etapa(descricao)
        ordem.historico.append(f"Etapa {etapa.id} adicionada: {descricao}.")
        return etapa.para_dict()

    def remover_etapa(self, ordem_id: str, etapa_id: int) -> dict:
        self._validar_id_etapa(etapa_id)
        ordem = self._em_reparo(ordem_id)
        etapa = ordem.etapas.buscar(lambda e: e.id == etapa_id)
        if etapa is None:
            raise NaoEncontradoError("Etapa não encontrada.")
        if len(ordem.etapas) == 1:
            raise ConflitoError("A ordem deve manter pelo menos uma etapa.")
        removida = ordem.etapas.remover_primeiro(lambda e: e.id == etapa_id)
        ordem.historico.append(f"Etapa {etapa_id} removida: {removida.descricao}.")
        return removida.para_dict()

    def marcar_etapa(self, ordem_id: str, etapa_id: int, concluida: bool) -> dict:
        self._validar_id_etapa(etapa_id)
        if type(concluida) is not bool:
            raise ValidacaoError("concluida deve ser true ou false.")
        ordem = self._em_reparo(ordem_id)
        etapa = ordem.etapas.buscar(lambda e: e.id == etapa_id)
        if etapa is None:
            raise NaoEncontradoError("Etapa não encontrada.")
        etapa.concluida = concluida
        ordem.historico.append(f"Etapa {etapa_id}: " + ("concluída." if concluida else "pendente."))
        return etapa.para_dict()

    def retirar_peca(self, ordem_id: str, peca: str) -> dict:
        peca = validar_texto(peca, "peca", 100)
        ordem = self._em_reparo(ordem_id)
        ordem.pecas.empilhar(peca)
        ordem.historico.append(f"Peça retirada: {peca}.")
        return {"peca_retirada": peca, "pecas_do_topo_para_base": list(ordem.pecas)}

    def recolocar_peca(self, ordem_id: str) -> dict:
        ordem = self._em_reparo(ordem_id)
        if ordem.pecas.esta_vazia():
            raise ConflitoError("Não há peças retiradas.")
        peca = ordem.pecas.desempilhar()
        ordem.historico.append(f"Peça recolocada: {peca}.")
        return {"peca_recolocada": peca, "pecas_do_topo_para_base": list(ordem.pecas)}

    def concluir_atendimento(self, ordem_id: str) -> dict:
        ordem = self._em_reparo(ordem_id)
        if not ordem.pecas.esta_vazia():
            raise ConflitoError("Recoloque todas as peças antes de concluir.")
        if any(not etapa.concluida for etapa in ordem.etapas):
            raise ConflitoError("Conclua todas as etapas antes de encerrar o atendimento.")
        assert ordem.bancada is not None
        self._bancadas[ordem.bancada] = None
        ordem.bancada = None
        ordem.status = StatusOrdem.CONCLUIDA
        self._series_ativas.remove(ordem.equipamento.numero_serie)
        ordem.historico.append("Atendimento concluído; bancada liberada.")
        return ordem.para_dict()

    def solicitar_revisao(self, ordem_id: str, motivo: str, urgente: bool = False) -> dict:
        motivo = validar_texto(motivo, "motivo", 150)
        if type(urgente) is not bool:
            raise ValidacaoError("urgente deve ser true ou false.")
        ordem = self._ordem(ordem_id)
        if ordem.status != StatusOrdem.CONCLUIDA:
            raise ConflitoError("Somente ordens concluídas podem solicitar revisão.")
        if ordem.equipamento.numero_serie in self._series_ativas:
            raise ConflitoError("O equipamento já tem outra ordem ativa.")
        if len(ordem.etapas) + 2 > self.LIMITE_ETAPAS:
            raise ConflitoError("Não há espaço para duas novas etapas de revisão.")
        pedido = PedidoRevisao(ordem.id, motivo, urgente)
        if urgente:
            self._revisoes.inserir_inicio(pedido)
        else:
            self._revisoes.inserir_fim(pedido)
        ordem.status = StatusOrdem.AGUARDANDO_REVISAO
        self._series_ativas.add(ordem.equipamento.numero_serie)
        ordem.historico.append("Revisão " + ("urgente" if urgente else "comum") + f" solicitada: {motivo}.")
        return ordem.para_dict()

    def cancelar_revisao(self, extremidade: str = "fim") -> dict:
        """Cancela o pedido na ponta escolhida; não significa 'último cadastrado'."""
        if extremidade not in ("inicio", "fim"):
            raise ValidacaoError("extremidade deve ser 'inicio' ou 'fim'.")
        if self._revisoes.esta_vazia():
            raise ConflitoError("Não há revisões aguardando atendimento.")
        pedido = (
            self._revisoes.remover_inicio()
            if extremidade == "inicio"
            else self._revisoes.remover_fim()
        )
        ordem = self._ordem(pedido.ordem_id)
        ordem.status = StatusOrdem.CONCLUIDA
        self._series_ativas.remove(ordem.equipamento.numero_serie)
        ordem.historico.append(f"Solicitação de revisão cancelada na ponta '{extremidade}'.")
        return ordem.para_dict()

    def estado(self) -> dict:
        return {
            "bancadas": [
                {"indice": indice, "ordem_id": ordem_id, "livre": ordem_id is None}
                for indice, ordem_id in enumerate(self._bancadas)
            ],
            "fila": list(self._fila),
            "revisoes": [
                {"ordem_id": p.ordem_id, "motivo": p.motivo, "urgente": p.urgente}
                for p in self._revisoes
            ],
            "total_ordens": len(self._ordens),
        }

    def relatorio(self) -> dict:
        # Compreensões de dicionário, conjunto e lista.
        por_status = {
            status.value: sum(o.status == status for o in self._ordens.values())
            for status in StatusOrdem
        }
        tipos = {o.equipamento.tipo for o in self._ordens.values()}
        livres = [i for i, valor in enumerate(self._bancadas) if valor is None]
        return {
            "total_ordens": len(self._ordens),
            "por_status": por_status,
            "tipos_de_equipamento": sorted(tipos),
            "indices_bancadas_livres": livres,
        }

    def analisar_recursao(self, ordem_id: str) -> dict:
        ordem = self._ordem(ordem_id)
        return {
            "simples": {
                "etapas_contadas": ordem.etapas.contar_recursivo(),
                "tempo": "O(n)",
                "memoria_auxiliar": "O(n)",
                "definicao": "C(None)=0; C(no)=1+C(no.proximo)",
            },
            "dupla": {
                "bancadas_ocupadas": self._bancadas.contar_ocupados_recursivo(),
                "tempo": "O(B)",
                "memoria_auxiliar": "O(log B)",
                "definicao": "Uma posição: 0 ou 1; intervalo maior: contar(esquerda)+contar(direita)",
            },
        }

    def demonstrar_copias(self, ordem_id: str) -> dict:
        """Altera apenas snapshots locais; nunca a ordem oficial."""
        antes = self.obter_ordem(ordem_id)
        original = self.obter_ordem(ordem_id)
        rasa = copy(original)
        profunda = deepcopy(original)
        compartilha_rasa = rasa["etapas"] is original["etapas"]
        compartilha_profunda = profunda["etapas"] is original["etapas"]
        rasa["etapas"][0]["descricao"] = "Alteração na cópia rasa"
        base_apos_rasa = original["etapas"][0]["descricao"]
        profunda["etapas"][0]["descricao"] = "Alteração na cópia profunda"
        return {
            "rasa_compartilha_lista_interna": compartilha_rasa,
            "profunda_compartilha_lista_interna": compartilha_profunda,
            "descricao_original_do_snapshot": base_apos_rasa,
            "descricao_da_copia_profunda": profunda["etapas"][0]["descricao"],
            "alterar_profunda_preservou_snapshot": original["etapas"][0]["descricao"] == base_apos_rasa,
            "ordem_real_preservada": self.obter_ordem(ordem_id) == antes,
        }

    @staticmethod
    def analisar_busca(tamanho: int = 8) -> dict:
        """Conta comparações; a média assume sucesso e posições equiprováveis."""
        if type(tamanho) is not int or not 1 <= tamanho <= 500:
            raise ValidacaoError("tamanho deve ser um inteiro de 1 a 500.")
        vetor: VetorFixo[int] = VetorFixo(tamanho)
        for indice in range(tamanho):
            vetor[indice] = indice
        comparacoes = [vetor.buscar(i).comparacoes for i in range(tamanho)]
        return {
            "tamanho": tamanho,
            "melhor_caso": {"comparacoes": comparacoes[0], "tempo": "O(1)"},
            "caso_medio": {
                "comparacoes": sum(comparacoes) / tamanho,
                "tempo": "O(n)",
                "hipotese": "Busca bem-sucedida; cada posição tem a mesma probabilidade.",
            },
            "pior_caso": {"comparacoes": comparacoes[-1], "tempo": "O(n)"},
            "ausente": {"comparacoes": vetor.buscar(-1).comparacoes, "tempo": "O(n)"},
            "nota": "Os custos descrevem uma busca. O experimento faz n buscas e custa O(n²).",
        }
