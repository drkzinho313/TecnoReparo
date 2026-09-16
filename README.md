# TecnoReparo

**Simulador de Gestão de Assistência Técnica**

Backend acadêmico em Python com Programação Orientada a Objetos (POO).
Implementa vetores, listas encadeadas, filas, pilhas e deques; inclui recursão,
análise de complexidade e os recursos de Python pedidos inicialmente.

## Executar

Requer Python **3.10 ou superior**. Verificado com Python 3.12.
Usa somente a biblioteca padrão: não é necessário instalar pacotes com pip.

Extraia o ZIP, abra um terminal dentro da pasta `tecnoreparo_backend` e execute:

~~~bash
python demo.py
~~~

Esse comando apresenta uma demonstração completa no terminal e encerra.
Para iniciar a API com três equipamentos fictícios:

~~~bash
python main.py --demo
~~~

A API ficará em [http://127.0.0.1:8000](http://127.0.0.1:8000).
A raiz mostra as rotas; `/api/estado` mostra as bancadas e as filas.
Sem `--demo`, o sistema começa vazio.

~~~bash
python main.py --bancadas 5 --porta 8001
python -m unittest discover -s tests -v
~~~

No Linux/macOS, use `python3` se `python` não estiver disponível.
No Windows, também é possível usar `py -3`.

**Escopo desta versão:** estado em memória, para execução local e apresentação
acadêmica. Encerrar o processo apaga os cadastros. A API não inclui banco de
dados, autenticação ou conexão automática com o esboço visual anterior.
O servidor `wsgiref` é a implementação de referência do Python, destinada aqui
ao uso local; não é um servidor de produção.

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
| `main.py` | Inicialização do servidor local. |
| `demo.py` | Apresentação dos conceitos no terminal, sem servidor. |
| `tests/` | Testes das estruturas, do fluxo e da API. |

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
| GET | `/` | Catálogo de rotas |
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

Uma futura interface executada em outra origem pode usar:

~~~bash
python main.py --demo --origem-frontend http://localhost:5173
~~~

Informe a origem real da interface. O parâmetro pode ser repetido.
O CORS responde a OPTIONS e permite somente as origens configuradas.
O frontend deverá substituir seus dados locais por chamadas à API.

## Verificação e apresentação

Os testes incluem FIFO, LIFO, integridade das pontas do deque, remoção de nós
no início/meio/fim, vetores cheios, ciclo completo de atendimento, conflitos,
cópias independentes, recursão, validação JSON, CORS e requisições a um
servidor HTTP real em uma porta local temporária. `collections.deque` aparece
somente nos testes, como referência para conferir a implementação manual.

Para apresentar: execute `demo.py`, explique as cinco estruturas, mostre
as classes em `estruturas.py`, compare as cópias e finalize com a busca e os testes.

## Referências

- Plano fornecido: `ESTRUTURA_DE_DADOS_NORMAL_GT.pdf`, Unidade I, p. 2.
- [Python: cópia rasa e profunda](https://docs.python.org/3/library/copy.html).
- [Python: implementação de referência WSGI](https://docs.python.org/3/library/wsgiref.html).
