# TecnoReparo

**Simulador de Gestão de Assistência Técnica**

Aplicação acadêmica com backend Python em Programação Orientada a Objetos (POO)
e interface responsiva em HTML5, CSS3 e JavaScript puro. Implementa vetores,
listas encadeadas, filas, pilhas e deques; inclui recursão, análise de
complexidade e os recursos de Python pedidos inicialmente.

## Executar

Requer Python **3.10 ou superior**. Verificado com Python 3.12.
Usa somente a biblioteca padrão: não é necessário instalar pacotes com pip.

Extraia o ZIP, abra um terminal dentro da pasta `tecnoreparo_backend` e execute:

~~~bash
python main.py --demo
~~~

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000) no navegador.
Esse único comando entrega a interface e a API juntas. Não abra `index.html`
diretamente: as ações precisam do servidor Python. Deixe o terminal aberto
enquanto utiliza o sistema e pressione Ctrl+C para encerrar.

O modo `--demo` inclui três equipamentos e clientes fictícios. Sem `--demo`,
o sistema começa vazio. O catálogo JSON está em `/api`; `/api/estado` mostra
as bancadas e as filas. Para uma demonstração só no terminal, execute
`python demo.py`.

~~~bash
python main.py --bancadas 5 --porta 8001
python -m unittest discover -s tests -v
~~~

No Linux/macOS, use `python3` se `python` não estiver disponível.
No Windows, também é possível usar `py -3`.

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

Roteiro rápido para apresentação:

1. Inicie com `--demo` e observe as três bancadas e a fila de espera.
2. Abra a primeira bancada, marque as etapas e recoloque a peça **Tampa**.
3. Conclua o atendimento: a bancada fica disponível.
4. Solicite uma revisão na ordem concluída e consulte a tela **Revisões**.
5. Cadastre outra ordem e use **Atender próximo** para mostrar a ordem FIFO.
6. Abra **Laboratório**, escolha uma ordem e execute a demonstração.

Se o servidor for encerrado, a próxima requisição mostrará o erro. Reinicie o
servidor e clique em **Atualizar dados** ou **Tentar novamente**; os cadastros
anteriores não são recuperados, pois esta versão armazena tudo em memória.

## Alinhamento com a Unidade I

Fonte: `ESTRUTURA_DE_DADOS_NORMAL_GT.pdf`, enviado pelo usuário, seção 4.1,
Unidade I, página 2. A Unidade II começa na página 3.

| Conteúdo da Unidade I | Aplicação no projeto |
| --- | --- |
| Vetores | `VetorFixo`: bancadas com capacidade definida e acesso por índice. |
| Listas encadeadas | `ListaEncadeada`: etapas de cada ordem, com nós e referências. |
| Listas lineares restritas | Interfaces de `Fila`, `Pilha` e `Deque`, que limitam as operações disponíveis. |
| Pilhas | `Pilha`: última peça retirada é a primeira recolocada na simulação. |
| Filas | `Fila`: equipamentos aguardando o primeiro atendimento em ordem FIFO. |
| Deques | `Deque`: solicitações de revisão entram ou saem pelas duas extremidades. |
| Definição e métodos recursivos | Casos-base e casos recursivos documentados nos métodos. |
| Recursão simples | Contar os nós da lista de etapas, com uma chamada por nó. |
| Recursão dupla | Contar bancadas ocupadas, dividindo o intervalo em duas metades. |
| Complexidade e notação O-grande | Custos de tempo e memória descritos no código e neste guia. |
| Melhor, médio e pior caso | Contagem de comparações na busca sequencial em vetor. |

**Estrutura adicional escolhida: deque.** Está explicitamente na Unidade I.
O deque foi implementado com nós duplamente encadeados, possibilitando
inserir e remover nas duas pontas em O(1). Não usa `collections.deque`.

Tabelas hash próprias, tratamento de colisões e algoritmos de ordenação pertencem
à Unidade II do anexo. Não foram implementados como conteúdos deste trabalho.
`dict`, `set` e `sorted` são usados como recursos prontos de apoio do Python;
seu uso não equivale a implementar uma tabela hash ou um algoritmo de ordenação.

## Conceitos solicitados no início da conversa

| Recurso | Uso concreto |
| --- | --- |
| Listas nativas | Histórico textual de eventos da ordem e respostas de apresentação. |
| Tuplas | `(nome, contato)` identifica o cliente dentro de cada ordem. |
| Conjuntos | Sintomas sem duplicação e números de série com atendimento ativo. |
| Dicionários | Catálogo de ordens por ID e respostas JSON. |
| Compreensão de lista | Filtragem das ordens por status e seleção de bancadas livres. |
| Compreensão de conjunto | Normalização de sintomas e tipos de equipamentos distintos. |
| Compreensão de dicionário | Contagem de ordens por status no relatório. |
| Cópia rasa | `copy()` em uma representação da ordem: a lista interna de etapas é compartilhada. |
| Cópia profunda | `deepcopy()` cria uma representação independente para simulação. |

A demonstração das cópias altera apenas representações locais. O cadastro real
permanece intacto. Os endpoints retornam dados novos, sem expor os nós internos.

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

## Complexidade

`n` é o número de elementos; `B` é a quantidade de bancadas.
Comparações e manipulação de referências são consideradas O(1).
Os custos abaixo são dos TADs, sem o custo de serializar JSON.

| Operação | Melhor | Médio | Pior | Memória auxiliar |
| --- | --- | --- | --- | --- |
| Acessar/substituir posição do vetor | O(1) | O(1) | O(1) | O(1) |
| Buscar valor no vetor | O(1) | O(n)* | O(n) | O(1) |
| Inserir no início/fim da lista | O(1) | O(1) | O(1) | O(1) por novo nó |
| Buscar/remover por condição na lista | O(1) | O(n)* | O(n) | O(1) |
| Enfileirar/desenfileirar | O(1) | O(1) | O(1) | O(1) por operação |
| Empilhar/desempilhar | O(1) | O(1) | O(1) | O(1) por operação |
| Inserir/remover em ponta do deque | O(1) | O(1) | O(1) | O(1) por operação |
| Percorrer toda uma estrutura | O(n) | O(n) | O(n) | O(1) com iterador |
| Contar nós com recursão simples | O(n) | O(n) | O(n) | O(n) de chamadas |
| Contar ocupação com recursão dupla | O(B) | O(B) | O(B) | O(log B) de chamadas |

*Para busca bem-sucedida, assumindo posições equiprováveis. Sem uma hipótese
sobre as entradas, não se deve atribuir uma média exata.
Para oito posições: melhor = 1 comparação; média = 4,5; pior = 8.
Se o valor não existe, são oito comparações.

O-grande é um limite assintótico superior, não uma medida em segundos e não é,
por definição, sinônimo de pior caso. Aqui são apresentados limites por cenário.
As estruturas armazenam O(n) elementos/nós; isso é separado da memória auxiliar.

A busca de uma bancada livre custa O(B); atender não é O(1) só porque
desenfileirar é O(1). Responder com uma ordem também percorre suas etapas, peças
e histórico. `analisar_busca` executa n buscas e custa O(n²) no total;
os valores exibidos se referem ao custo de cada busca.

### Recursão

Simples, na lista:

~~~text
C(None) = 0
C(no) = 1 + C(no.proximo)
~~~

Dupla, no vetor:

~~~text
Intervalo vazio: 0
Uma posição: 1 se ocupada, 0 se livre
Intervalo maior: contar(metade esquerda) + contar(metade direita)
~~~

A recursão dupla faz duas chamadas em cada caso não trivial, sobre intervalos
disjuntos. Isso não a torna exponencial: a recorrência resulta em O(B).
A contagem recursiva de etapas tem limite didático de 200 nós; o fluxo normal
usa tamanho armazenado e percursos iterativos.

## API JSON

Sucesso: `{"dados": ...}`. Erro esperado: `{"erro": "mensagem"}`.
Campos desconhecidos são rejeitados. Índices de bancada começam em zero;
IDs de etapas não são reutilizados.

| Método | Caminho | Corpo JSON ou parâmetro |
| --- | --- | --- |
| GET | `/api` | Catálogo de rotas JSON; `/` abre a interface |
| GET | `/api/estado` | Bancadas, fila e revisões |
| GET | `/api/relatorio` | Contagens por status |
| GET | `/api/ordens` | Filtro opcional `?status=aguardando` |
| POST | `/api/ordens` | Cadastro conforme exemplo abaixo |
| GET | `/api/ordens/{id}` | Consultar uma ordem |
| POST | `/api/atendimentos` | `{"origem":"fila"}` ou `{"origem":"revisoes"}` |
| POST | `/api/ordens/{id}/etapas` | `{"descricao":"Verificar cabos"}` |
| PATCH | `/api/ordens/{id}/etapas/{etapa}` | `{"concluida":true}` |
| DELETE | `/api/ordens/{id}/etapas/{etapa}` | Sem corpo |
| POST | `/api/ordens/{id}/pecas/retirar` | `{"peca":"Tampa"}` |
| POST | `/api/ordens/{id}/pecas/recolocar` | `{}` |
| POST | `/api/ordens/{id}/concluir` | `{}` |
| POST | `/api/ordens/{id}/revisoes` | `{"motivo":"Falha intermitente","urgente":true}` |
| POST | `/api/revisoes/cancelar` | `{"extremidade":"fim"}` ou `{"extremidade":"inicio"}` |
| GET | `/api/ordens/{id}/recursao` | Resultado dos dois métodos recursivos |
| GET | `/api/ordens/{id}/copias` | Demonstração de cópia sem alterar a ordem |
| GET | `/api/analises/busca` | `?tamanho=8`, entre 1 e 500 |

Exemplo de cadastro, enviado por POST a `/api/ordens`:

~~~json
{
  "nome_cliente": "Cliente fictício",
  "contato": "Contato de demonstração",
  "numero_serie": "PC-001",
  "tipo": "Desktop",
  "defeito": "Equipamento não liga",
  "sintomas": ["não liga", "sem imagem", "não liga"]
}
~~~

Envie `Content-Type: application/json`. Corpos têm limite de 64 KiB.
Status: `aguardando`, `em_reparo`, `concluida`, `aguardando_revisao`.
Erros comuns: 400 (dados inválidos), 404 (não encontrado), 405 (método),
409 (conflito de estado), 413 (tamanho) e 415 (tipo de conteúdo).

A interface incluída já funciona na mesma origem, sem configurar CORS.
Se você desenvolver outra interface em uma origem diferente, pode usar:

~~~bash
python main.py --demo --origem-frontend http://localhost:5173
~~~

Informe a origem real da interface. O parâmetro pode ser repetido.
O CORS responde a OPTIONS e permite a mesma origem do servidor e as origens
adicionais configuradas. Essa opção não é necessária para a interface incluída.

## Verificação e apresentação

Os testes incluem FIFO, LIFO, integridade das pontas do deque, remoção de nós
no início/meio/fim, vetores cheios, ciclo completo de atendimento, conflitos,
cópias independentes, recursão, validação JSON, CORS, entrega dos arquivos da
interface, bloqueio de caminhos não publicados e requisições a um servidor
HTTP real em uma porta local temporária. `collections.deque` aparece
somente nos testes, como referência para conferir a implementação manual.

Verificação desta entrega: testes Python e sintaxe JavaScript. O navegador
remoto de testes bloqueou o acesso ao endereço local, portanto a conferência
visual e as interações completas no navegador não foram realizadas aqui.

Para apresentar o código: execute `demo.py`, explique as cinco estruturas,
mostre as classes em `estruturas.py`, compare as cópias e finalize com a busca.

## Referências

- Plano fornecido: `ESTRUTURA_DE_DADOS_NORMAL_GT.pdf`, Unidade I, p. 2.
- [Python: cópia rasa e profunda](https://docs.python.org/3/library/copy.html).
- [Python: implementação de referência WSGI](https://docs.python.org/3/library/wsgiref.html).
