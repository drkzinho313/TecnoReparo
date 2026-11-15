"""Demonstração determinística de todas as estruturas, sem iniciar servidor."""

import json

from tecnoreparo import TecnoReparo


def mostrar(titulo: str, dados: object) -> None:
    print("\n" + titulo)
    print(json.dumps(dados, ensure_ascii=False, indent=2))


def main() -> None:
    sistema = TecnoReparo(3)
    for i in range(1, 3):
        sistema.registrar_ordem(
            nome_cliente=f"Cliente fictício {i}", contato="Contato de demonstração",
            numero_serie=f"PC-{i}", tipo="Desktop", defeito="Não liga",
            sintomas=["Não liga", "não liga"],
        )
    mostrar("1. Vetor de bancadas e fila FIFO", sistema.estado())
    ordem = sistema.atender_proximo()
    identificador = ordem["id"]
    sistema.adicionar_etapa(identificador, "Verificar cabos")
    sistema.retirar_peca(identificador, "Tampa")
    sistema.retirar_peca(identificador, "Memória RAM")
    mostrar("2. Pilha LIFO: memória sai antes da tampa", sistema.recolocar_peca(identificador))
    sistema.recolocar_peca(identificador)
    mostrar("3. Recursão simples e dupla", sistema.analisar_recursao(identificador))
    mostrar("4. Cópia rasa e profunda", sistema.demonstrar_copias(identificador))
    for etapa in sistema.obter_ordem(identificador)["etapas"]:
        sistema.marcar_etapa(identificador, etapa["id"], True)
    sistema.concluir_atendimento(identificador)
    sistema.solicitar_revisao(identificador, "Verificar falha intermitente", urgente=True)
    mostrar("5. Deque: revisão urgente no início", sistema.estado())
    sistema.atender_proximo(origem="revisoes")
    for etapa in sistema.obter_ordem(identificador)["etapas"]:
        sistema.marcar_etapa(identificador, etapa["id"], True)
    sistema.concluir_atendimento(identificador)
    mostrar("6. Relatório com compreensões", sistema.relatorio())
    mostrar("7. Melhor, médio e pior caso de busca", sistema.analisar_busca(8))


if __name__ == "__main__":
    main()
