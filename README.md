# TecnoReparo

**Simulador de Gestão de Assistência Técnica**

Aplicação acadêmica com backend Python em Programação Orientada a Objetos (POO)
e interface responsiva em HTML5, CSS3 e JavaScript puro. Implementa vetores,
listas encadeadas, filas, pilhas e deques; inclui recursão, análise de
complexidade e os recursos de Python pedidos inicialmente. A versão 3 também
implementa tabela hash própria, grafos geográficos, quatro algoritmos de
ordenação e gráficos Matplotlib, conforme os requisitos da atividade.

## Executar

Requer Python **3.10 ou superior**. Verificado com Python 3.12.
O backend HTTP usa a biblioteca padrão. Os gráficos exigem **Matplotlib**;
instale a dependência abaixo. Não é necessário Node.js para usar o sistema.

Abra um terminal na raiz do projeto, onde estão `main.py` e `requirements.txt`,
e execute:

~~~bash
python -m pip install -r requirements.txt
python main.py --demo
~~~

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000) no navegador.
Esse único comando entrega a interface e a API juntas. Não abra `index.html`
diretamente: as ações precisam do servidor Python. Deixe o terminal aberto
enquanto utiliza o sistema e pressione Ctrl+C para encerrar.

O modo `--demo` inclui três equipamentos, clientes fictícios e uma rede de
coleta/entrega com seis locais e sete conexões. Sem `--demo`,
o sistema começa vazio. O catálogo JSON está em `/api`; `/api/estado` mostra
as bancadas e as filas. Para uma demonstração só no terminal, execute
`python demo.py`.

~~~bash
python main.py --bancadas 5 --porta 8001
python -m unittest discover -s tests -v
~~~

No Linux/macOS, use `python3` se `python` não estiver disponível.
No Windows, também é possível usar `py -3`.

A raiz contém a única versão mantida, incluindo os recursos das Unidades I e II.
A pasta `arquivo/versao-inicial/` preserva uma cópia histórica; não use essa pasta
para iniciar o sistema ou implementar alterações.

Para isolar as dependências, pode criar um ambiente com `python -m venv .venv`
e ativá-lo antes da instalação (`.venv\Scripts\Activate.ps1` no PowerShell,
ou `source .venv/bin/activate` no Linux/macOS).

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
- **Laboratório:** visualização da ocupação das bancadas e da fila de atendimento.

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
6. Abra **Oficina** para acompanhar a ocupação das bancadas e a fila de atendimento.
7. Em **Análises**, consulte `OS-0001`, altere o método hash e abra a explicação dos baldes.
8. Em **Rotas**, calcule de “Assistência · exemplo” até “Entrega C · exemplo”: 3,20 km.
9. Em **Análises**, execute o comparativo e baixe o gráfico PNG.
10. Em **Ordens de serviço**, escolha campo, algoritmo e direção para ordenar os registros reais.

O roteiro completo e as justificativas de cada escolha estão em
[`GUIA_APRESENTACAO.md`](GUIA_APRESENTACAO.md).

O formulário de demonstração e os resultados de recursão, cópias e busca foram
removidos da interface. Esses conceitos continuam implementados no backend
e podem ser apresentados pelo comando `python demo.py` ou pelos endpoints JSON.

Se o servidor for encerrado, a próxima requisição mostrará o erro. Reinicie o
servidor e clique em **Atualizar dados** ou **Tentar novamente**; os cadastros
anteriores não são recuperados, pois esta versão armazena tudo em memória.

Rotas e análises carregam seus dados somente ao abrir a respectiva tela.
Uma falha nessas áreas mostra uma mensagem local com **Tentar novamente**;
as ordens, as bancadas e as revisões continuam disponíveis. A tentativa local
repete somente a consulta que falhou.

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

## Requisitos adicionais da atividade — Unidade II

| Exigência | Implementação e aplicação |
| --- | --- |
| Hash e seus métodos | `TabelaHash` armazena as ordens reais por ID. Divisão, multiplicação e dobramento; inserir/atualizar, buscar, remover e reindexar. Colisões por encadeamento separado, com `VetorFixo` e `ListaEncadeada`. |
| Grafos com geolocalização | `GrafoRotas` representa locais com latitude/longitude e conexões de mão dupla. Dijkstra calcula a menor distância; BFS identifica locais alcançáveis com a `Fila` própria. |
| Exibição com Matplotlib | Rede geográfica com caminho destacado e gráficos do comparativo, produzidos no backend em PNG. |
| Bolha, Inserção, Seleção e QuickSort | Quatro implementações próprias em `Ordenador`, usadas na ordenação real da lista de ordens e no experimento. QuickSort usa a `Pilha` própria. |
| Comparativo gráfico de desempenho | Mediana e faixa mínimo–máximo, para até três tamanhos de entrada e quatro cenários. Tempos efetivamente medidos, não estimados. |

`dict` e `set` continuam como apoio para respostas JSON, adjacências e conjuntos.
Não substituem a implementação própria da tabela hash. `sorted` é usado em
rotinas auxiliares da versão anterior, como metadados da API; os quatro métodos
comparados e a ordenação solicitada das ordens não o utilizam.

### Limites da rede geográfica

O exemplo é fictício. É possível cadastrar até 40 locais com coordenadas
próprias, vincular uma ordem e criar até 120 conexões. As distâncias são
informadas em km ou calculadas por Haversine, como aproximação geográfica.
O grafo não conhece ruas, trânsito ou restrições de circulação: a rota só é
ótima dentro das conexões e dos pesos cadastrados. Não resolve uma viagem
com várias paradas nem usa GPS ou um serviço externo de mapas.
Pesos devem ser positivos. Origem igual ao destino produz distância zero;
destinos desconectados retornam ausência de caminho, sem distância infinita.

### Medições de ordenação

O experimento usa ordens **sintéticas** com chave numérica, de 2 a 500 registros,
para preservar os atendimentos. A mesma entrada é copiada para cada algoritmo;
as cópias e a verificação do resultado ficam fora do tempo medido. Há aquecimento,
rotação da ordem de execução, semente fixa e 1 a 7 repetições. O cronômetro é
`perf_counter_ns`. Os tempos incluem a instrumentação de comparações/movimentos.
“Movimento” é uma escrita em uma posição da lista; uma troca conta duas.
A menor mediana vale somente para aquele ensaio, cenário e computador.

Para gerar gráficos e dados sem abrir o navegador:

~~~bash
python demo_unidade2.py
python demo_unidade2.py --cenario inverso --tamanho 500 --repeticoes 5 --saida exemplos_inverso
~~~

`exemplos/` contém PNGs, CSV e JSON de uma execução real de demonstração,
com versões e horário registrados. Executar novamente substitui esses exemplos.
Os tempos serão diferentes, mesmo com a mesma semente.

## Conceitos solicitados no início da conversa

| Recurso | Uso concreto |
| --- | --- |
| Listas nativas | Histórico textual de eventos da ordem e respostas de apresentação. |
| Tuplas | `(nome, contato)` identifica o cliente dentro de cada ordem. |
| Conjuntos | Sintomas sem duplicação e números de série com atendimento ativo. |
| Dicionários | Adjacências do grafo, relatório e respostas JSON; o catálogo usa a tabela hash própria. |
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
| `tecnoreparo/tabela_hash.py` | Funções hash, baldes encadeados, busca, remoção e redimensionamento. |
| `tecnoreparo/grafo.py` | Coordenadas, conexões, Haversine, BFS e Dijkstra. |
| `tecnoreparo/ordenacao.py` | Quatro algoritmos e experimento de desempenho. |
| `tecnoreparo/graficos.py` | Figuras Matplotlib em memória, sem `pyplot` global. |
| `tecnoreparo/modelos.py` | Equipamento, etapa, solicitação de revisão e ordem de serviço. |
| `tecnoreparo/servico.py` | Cadastro, atendimento, regras, relatórios e demonstrações. |
| `tecnoreparo/api.py` | Tradução entre HTTP/JSON e chamadas ao serviço. |
| `tecnoreparo/web.py` | Entrega da interface e dos arquivos estáticos na mesma origem da API. |
| `frontend/index.html` | Navegação e formulários acessíveis. |
| `frontend/styles.css` | Visual, responsividade e animações CSS3. |
| `frontend/app.js` | Telas, efeitos de clique, formulários e integração com a API. |
| `frontend/unidade2.js` | Telas de rotas, índice hash e comparação. |
| `frontend/*.svg` | Marca e ícones locais. |
| `main.py` | Inicialização do servidor local. |
| `demo.py` | Apresentação dos conceitos no terminal, sem servidor. |
| `demo_unidade2.py` | Geração de gráficos e exportação das medições. |
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
| GET | `/api/ordens` | `status`, `ordenar_por=id/cliente/equipamento`, `metodo=bolha/insercao/selecao/quicksort`, `descendente=true/false` opcionais |
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

Rotas adicionadas na versão 3:

| Método | Caminho | Corpo JSON ou parâmetro |
| --- | --- | --- |
| GET | `/api/indice` | Estatísticas e baldes da tabela de ordens |
| GET | `/api/indice/consulta` | `?chave=OS-0001`: rastro da consulta e ordem encontrada |
| POST | `/api/indice/configurar` | `{"metodo":"divisao"}`; também `multiplicacao` e `dobramento` |
| POST | `/api/indice/demonstrar` | `{"metodo":"divisao"}`: inserção, colisão, busca e remoção isoladas |
| POST | `/api/analises/ordenacao` | `{"tamanho":250,"cenario":"aleatorio","repeticoes":3,"semente":42}` |
| GET | `/api/rotas` | Locais e conexões |
| GET | `/api/rotas/mapa` | Gráfico da rede |
| POST | `/api/rotas/exemplo` | `{}`; apenas quando a rede está vazia |
| POST | `/api/rotas/pontos` | `{"nome":"Coleta","latitude":-10.12,"longitude":-36.17,"ordem_id":"OS-0001"}`; vínculo opcional |
| DELETE | `/api/rotas/pontos/{ponto_id}` | Remove local e conexões incidentes |
| POST | `/api/rotas/conexoes` | `{"origem":"P-0001","destino":"P-0002","distancia_km":2.5}`; distância opcional |
| DELETE | `/api/rotas/conexoes` | `{"origem":"P-0001","destino":"P-0002"}` |
| POST | `/api/rotas/calcular` | `{"origem":"P-0001","destino":"P-0005"}` |

Gráficos são retornados no campo `grafico`, como data URI PNG em base64,
e exibidos pela interface sem serviço externo.

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

Verificação desta revisão: 72 testes Python, dois scripts de testes JavaScript
e testes de integração em navegador Edge headless. O fluxo no navegador cobre
cadastro, atendimento, peças, conclusão, revisão e fechamento por Escape.
Também cobre falhas independentes de rotas/hash, recuperação local, resposta
lenta e cinco telas com largura de celular (390 px), sem transbordamento
horizontal. Capturas de desktop e celular ficam em `test-results/`.

Os testes Python incluem colisões, reindexação, ordenação sem alterar a fila,
medições, validação geográfica, destinos desconectados e gráficos PNG reais.

Testes JavaScript sem dependências adicionais (Node.js):

~~~bash
node tests/test_interface.cjs
node tests/test_carregamento.cjs
~~~

Para repetir o fluxo em navegador, instale as ferramentas opcionais de teste:

~~~bash
npm install
npx playwright install chromium
npm run test:e2e
~~~

O teste inicia um servidor vazio em uma porta local livre e o encerra ao terminar.
Não utiliza os cadastros de um servidor já aberto. O comando `python` precisa
estar disponível; se necessário, defina `PYTHON` com o caminho do interpretador.
Para usar o Edge já instalado, dispense o download do Chromium e defina
`BROWSER_CHANNEL=msedge` (`$env:BROWSER_CHANNEL = "msedge"` no PowerShell).
Node.js e Playwright são necessários apenas para os testes opcionais.
Também é possível usar `pnpm install --frozen-lockfile` e `pnpm test:e2e`;
o arquivo `pnpm-lock.yaml` fixa as dependências de teste desta revisão.

Para apresentar o código: execute `demo.py`, explique as cinco estruturas,
mostre as classes em `estruturas.py` e continue com o roteiro de Unidade II
em `GUIA_APRESENTACAO.md`.

## Referências

- Plano fornecido: `ESTRUTURA_DE_DADOS_NORMAL_GT.pdf`, Unidade I, p. 2.
- [Python: cópia rasa e profunda](https://docs.python.org/3/library/copy.html).
- [Python: medição de tempo](https://docs.python.org/3/library/time.html#time.perf_counter_ns).
- [Matplotlib: figuras em servidor web](https://matplotlib.org/stable/gallery/user_interfaces/web_application_server_sgskip.html).
- [Python: implementação de referência WSGI](https://docs.python.org/3/library/wsgiref.html).

