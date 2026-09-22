# TecnoReparo

**Simulador de Gestão de Assistência Técnica**

Aplicação acadêmica com backend Python em Programação Orientada a Objetos (POO)
e interface responsiva em HTML5, CSS3 e JavaScript puro. Implementa vetores,
listas encadeadas, filas, pilhas e deques; inclui recursão, análise de
complexidade.

## Executar

Requer Python **3.10 ou superior**. Verificado com Python 3.12.
Usa somente a biblioteca padrão: não é necessário instalar pacotes com pip.

**Escopo desta versão:** estado em memória, para execução local e apresentação
acadêmica. Encerrar o processo apaga os cadastros. A API não inclui banco de
dados ou autenticação. A interface usa os dados reais dessa API local.
O servidor `wsgiref` é a implementação de referência do Python, destinada aqui
ao uso local; não é um servidor de produção.

## Interface web

- **Visão geral:** contadores, bancadas ocupadas ou disponíveis, fila e ordens recentes.
- **Ordens de serviço:** cadastro, busca por cliente/equipamento/ID e filtros de situação.
- **Detalhes do reparo:** painel lateral com etapas, peças retiradas, histórico e conclusão.
- **Revisões:** pedidos comuns ou urgentes, atendimento e cancelamento pelas duas pontas.
- **Relatórios:** distribuição das ordens e tipos de equipamento cadastrados.
- **Laboratório:** visualização do vetor e da fila, recursão, cópias e comparações na busca.

O visual usa fundo claro, navegação verde-escura, cartões e ícones SVG locais.
Inclui abertura animada, skeleton de carregamento, barra de progresso das
requisições, indicadores nos botões, efeito de onda no clique, transições de
telas, janelas e notificações. A preferência do sistema por movimento reduzido
é respeitada. O CSS adapta a navegação, as tabelas e os formulários para telas menores.

Nenhum framework, CDN, pacote npm, conexão externa ou etapa de compilação é
necessário. As alterações são enviadas à API por `fetch`; o frontend não mantém
um cadastro paralelo. Após cada alteração, busca novamente o estado do servidor.



## Organização em POO

| Arquivo | Responsabilidade |
| --- | --- |
| `tecnoreparo/estruturas.py` | TADs, nós, algoritmos de percurso e recursão. |
| `tecnoreparo/modelos.py` | Equipamento, etapa, solicitação de revisão e ordem de serviço. |
| `tecnoreparo/servico.py` | Cadastro, atendimento, regras, relatórios e demonstrações. |
| `tecnoreparo/api.py` | Tradução entre HTTP/JSON e chamadas ao serviço. |
| `tecnoreparo/web.py` | Entrega da interface e dos arquivos estáticos na mesma origem da API. |
| `frontend/index.html` | Navegação e formulários acessíveis. |
| `frontend/styles.css` | Visual, responsividade e animações CSS3. |
| `frontend/app.js` | Telas, efeitos de clique, formulários e integração com a API. |
| `frontend/*.svg` | Marca e ícones locais. |
| `main.py` | Inicialização do servidor local. |
| `demo.py` | Apresentação dos conceitos no terminal, sem servidor. |
| `tests/` | Testes das estruturas, do fluxo, da API e da entrega da interface. |

- **Abstração:** cada estrutura expõe operações próprias, como `enfileirar` e
  `empilhar`, sem exigir que o chamador manipule os nós.
- **Encapsulamento:** atributos com `_` são internos por convenção; a API recebe
  cópias de apresentação. Não são uma barreira de segurança da linguagem.
- **Herança:** `ListaEncadeada`, `Fila`, `Pilha` e `Deque` implementam o contrato
  abstrato `ColecaoLinear`.
- **Polimorfismo:** as coleções oferecem `len`, iteração e `esta_vazia` sob o
  mesmo contrato.
- **Composição:** fila e pilha usam uma lista encadeada interna; cada ordem tem
  sua própria lista de etapas e sua própria pilha de peças.

O vetor usa `[None] * capacidade` como bloco fixo de referências. A classe
não permite aumentar a capacidade e rejeita índices negativos ou fora do limite.
Ela modela um vetor didático; a `list` nativa isoladamente é dinâmica.

## Regras e funcionamento

1. O cadastro gera um ID, como `OS-0001`, e entra no final da fila comum.
2. Atender retira o primeiro ID da fila e ocupa a primeira bancada livre.
3. Durante o reparo, podem ser acrescentadas ou removidas etapas da lista.
4. Cada peça retirada entra no topo da pilha. Recolocar retira exclusivamente o topo.
5. Para concluir, todas as etapas precisam estar concluídas e a pilha deve estar vazia.
6. A conclusão libera a bancada e permite novo atendimento para o mesmo equipamento.
7. Uma ordem concluída pode solicitar revisão pelo deque.

O número de série é normalizado em maiúsculas. Um conjunto impede duas ordens
ativas para o mesmo equipamento. Os exemplos usam somente dados fictícios.

### Regras específicas do deque

- Revisão comum entra no **fim**.
- Revisão urgente entra no **início**.
- Atender uma revisão retira do **início**.
- Cancelar um pedido pode retirar do **início ou fim**, conforme a opção informada.
- Dois pedidos urgentes consecutivos ficam em ordem inversa de chegada:
  o mais recente passa à frente. É uma regra explícita desta simulação,
  não uma fila de prioridade estável.
- O operador escolhe `origem="fila"` ou `origem="revisoes"` ao atender.
  Revisões não interrompem automaticamente a fila comum.
- O início da revisão acrescenta duas etapas pendentes: revisão e teste final.
  Cancelar uma revisão ainda na espera mantém as etapas já concluídas.

A pilha de peças é uma simplificação didática de desmontagem/montagem em ordem
inversa, não um procedimento técnico de reparo de hardware.

