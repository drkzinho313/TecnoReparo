# TecnoReparo — guia de apresentação

**Tema:** organização de uma assistência técnica, do recebimento ao reparo e à coleta/entrega.
**Implementação:** Python em POO; interface HTML5, CSS3 e JavaScript; gráficos Matplotlib.

O projeto é um simulador acadêmico local. Os cadastros, o índice e a rede ficam
em memória durante a execução. O exemplo usa dados fictícios. As exigências
consideradas são as estruturas da Unidade I e os três diferenciais obrigatórios
mostrados na descrição da atividade enviada pelo aluno.

## Preparação

~~~bash
python -m pip install -r requirements.txt
python main.py --demo
~~~

Abra http://127.0.0.1:8000. Mantenha o terminal aberto.
Para uma apresentação sem depender de gerar os gráficos ao vivo,
`exemplos/` contém figuras e medições de demonstração. Para regenerar:

~~~bash
python demo_unidade2.py
~~~

## 1. Estruturas aplicadas ao atendimento

| Estrutura | O que mostrar | Justificativa |
| --- | --- | --- |
| Vetor | Bancadas da tela inicial e de Oficina | Capacidade definida; acessar a posição de uma bancada por índice. |
| Lista encadeada | Abrir uma ordem e acrescentar/remover uma etapa | Etapas encadeadas por nós; inserção no fim sem deslocar os demais elementos. |
| Fila | Atender o próximo equipamento | Mantém a ordem de chegada, FIFO. |
| Pilha | Retirar duas peças e recolocá-las | A última retirada é a primeira recolocada, LIFO. |
| Deque | Concluir uma ordem e solicitar revisão comum ou urgente | Comum entra no fim; urgente no início. Atendimento sai do início; cancelamento pode sair de qualquer ponta. |

As classes estão em `tecnoreparo/estruturas.py`. Fila e pilha compõem uma
lista encadeada. O deque usa nós duplamente encadeados. O vetor usa uma lista
Python de tamanho fixo como bloco de referências, sem crescimento pela sua API.
O vetor e a lista encadeada também sustentam os baldes da tabela hash.

As listas restritas não são uma sexta coleção separada: fila, pilha e deque
são abstrações com regras próprias de acesso e remoção.

## 2. Tabela hash — aplicação real e colisões

1. Abra **Análises** e consulte `OS-0001`.
2. Mostre o balde escolhido, as chaves examinadas e a quantidade de comparações.
3. Troque o método em **Organização do índice** e aplique. Consulte a mesma ordem.
4. Expanda **Como o índice organiza as ordens** para mostrar os baldes.
5. Execute **Demonstrar colisão e remoção**: três registros de exemplo entram no
   mesmo balde; o registro do meio é removido; a busca do último continua funcionando.

A tabela **substitui o dicionário de ordens do serviço**. Cadastro usa inserção;
consultas e atendimento usam busca. Atualizar uma chave existente substitui seu
valor sem duplicá-la. A operação de remoção é exercitada em tabela isolada,
porque apagar uma ordem real exigiria também reconciliar fila, bancada e revisões.
O exemplo de colisão não apaga atendimentos.

| Método | Como funciona nesta implementação | Por que mostrar no projeto |
| --- | --- | --- |
| Divisão | Converte os bytes UTF-8 da chave em código polinomial de 32 bits; usa `código % capacidade`. | Regra padrão simples e determinística para localizar IDs das ordens. |
| Multiplicação | Usa `floor(m × fração(código × A))`, com `A = (√5 − 1)/2`. | Permite comparar outra distribuição dos mesmos IDs, sem depender só do resto inteiro. |
| Dobramento | Soma blocos de dois bytes da chave e aplica módulo da capacidade. | Demonstra como várias partes do ID contribuem para o índice. |
| Encadeamento separado | Cada balde é uma lista encadeada de entradas. | Resolve colisões sem sobrescrever uma ordem que tenha outro ID. |
| Redimensionamento | Ao superar carga 0,75, cria capacidade `2m + 1` e redistribui as entradas. | Evita manter cadeias cada vez maiores à medida que chegam ordens. |

Não há promessa de distribuição perfeita: verifique os baldes com o conjunto
usado na apresentação. Essa hash serve à indexação; não é criptográfica.

**Custos:** para chaves de tamanho limitado, busca tem custo esperado O(1 + α)
com boa distribuição e α = n/m; no pior caso, O(n). Considerando o tamanho L
da chave, a conversão custa O(L). A implementação mantém uma lista auxiliar
para preservar a ordem de cadastro; remover dela custa O(n), mesmo se a cadeia
consultada for curta. Não apresente toda remoção como O(1).

Código: `tecnoreparo/tabela_hash.py` e o atributo `_ordens` de `TecnoReparo`.

## 3. Grafo com coordenadas e menor caminho

1. Abra **Rotas**. O modo `--demo` já inclui a rede; se começou vazio,
   clique em **Carregar exemplo**.
2. Selecione **Assistência · exemplo** e **Entrega C · exemplo**.
3. Calcule: o caminho é `P-0001 → P-0002 → P-0004 → P-0005`, com **3,20 km**.
4. O gráfico Matplotlib posiciona os vértices por latitude/longitude e destaca
   as conexões escolhidas em verde. Baixe o PNG se precisar.
5. Escolha **Local desconectado · exemplo** como destino: o sistema informa
   que não há caminho. Conecte-o a outro local e calcule novamente.
6. Cadastre um ponto com coordenadas próprias e, opcionalmente, vincule uma ordem.

**Modelagem:** vértices são locais; arestas são conexões de mão dupla;
pesos positivos são distâncias em quilômetros. O grafo usa dicionários de
adjacência. Uma conexão pode receber uma distância informada; se ficar em
branco, Haversine aproxima a distância geográfica entre as coordenadas.

**Dijkstra** foi escolhido para minimizar a soma dos pesos. Nesta implementação,
o próximo vértice é selecionado por varredura: **O(V² + E)**, com O(V) de estado
auxiliar. Não se deve citar O((V+E) log V), pois não há heap nesta versão.

**BFS**, usando a fila própria, mostra os vértices alcançáveis: **O(V + E)**,
com O(V) auxiliar. BFS não é usado para minimizar a distância ponderada.
A rede ocupa O(V + E), e cada aresta é armazenada nos dois sentidos.

**Limite da demonstração:** coordenadas geográficas não fornecem automaticamente
ruas ou trânsito. As conexões são cadastradas manualmente; o exemplo é fictício.
O menor caminho vale nessa rede e não equivale a uma navegação rodoviária real.
Não é um otimizador de entregas com múltiplas paradas.

Código: `tecnoreparo/grafo.py`; gráficos em `tecnoreparo/graficos.py`.

## 4. Quatro algoritmos de ordenação

1. Em **Ordens de serviço**, escolha **Cliente**, **Crescente** e alterne os quatro
   algoritmos. Todos devem produzir a mesma ordem por chave; empates podem variar.
2. Mostre que a fila de atendimento mantém a ordem de chegada.
3. Em **Análises**, execute 250 ordens sintéticas, cenário **Aleatório**, 3 repetições.
4. Compare os tempos, as contagens e o gráfico. Repita em **Já ordenado** e
   **Ordem inversa** para mostrar que a entrada afeta o desempenho.
5. Apresente a menor mediana **naquele ensaio**, sem declarar um vencedor universal.

| Algoritmo | Melhor caso de tempo | Caso médio¹ | Pior caso | Memória auxiliar² |
| --- | --- | --- | --- | --- |
| Bolha com parada antecipada | O(n) | O(n²) | O(n²) | O(1) |
| Inserção | O(n) | O(n²) | O(n²) | O(1) |
| Seleção | O(n²) | O(n²) | O(n²) | O(1) |
| QuickSort, partição em três faixas | O(n) com todas as chaves iguais; O(n log n) com partições equilibradas e chaves distintas | O(n log n) | O(n²) | Até O(n) para a pilha explícita |

¹ O caso médio depende de hipóteses sobre a distribuição das entradas. O pivô
do QuickSort desta versão é o elemento central, não um pivô aleatório.
² Exclui a cópia O(n) de apresentação, a entrada e a instrumentação. Bolha e
inserção preservam a ordem de empates no sentido crescente; inverter o resultado
para exibir em ordem decrescente pode inverter esses empates.

QuickSort reutiliza a **Pilha da Unidade I** para armazenar intervalos. Os
algoritmos são implementados manualmente: não delegam a `sorted` ou `list.sort`.
Na aplicação real, ordenam cópias das ordens retornadas ao frontend; o cadastro
canônico e a fila não são reordenados.

**Como a comparação é feita:**

- Entradas sintéticas com chave numérica, mesmos dados para os quatro métodos.
- Tamanhos próximos de n/4, n/2 e n; para valores pequenos, repetições de tamanho são eliminadas.
- Semente fixa torna as entradas reproduzíveis; não torna os tempos idênticos.
- Aquecimento antes das medições, cópias fora do cronômetro e rotação dos métodos.
- Medição por `perf_counter_ns`, mediana e mínimo/máximo de 1 a 7 repetições.
- Instrumentação incluída no tempo: uma comparação lógica conta uma vez;
  movimento é uma escrita na lista, e uma troca conta duas escritas.
- Verificação da ordem fora do intervalo cronometrado. As métricas aparecem
  para cada tamanho; a tabela da tela destaca o maior conjunto.

Código: `tecnoreparo/ordenacao.py`. `demo_unidade2.py` também exporta os
resultados brutos em JSON e os resumos em CSV. Matplotlib só desenha os resultados;
não executa a ordenação e não inventa tempos.

## 5. POO e demais recursos de Python

- **Abstração e polimorfismo:** coleções implementam `ColecaoLinear` com tamanho,
  iteração e consulta de vazio.
- **Composição:** uma ordem contém lista de etapas e pilha de peças; fila e
  pilha compõem listas; tabela hash compõe vetor e listas.
- **Encapsulamento:** regras de negócio ficam no serviço; a API expõe DTOs
  independentes, sem permitir que a interface altere os nós internos.
- **Tuplas:** cliente e intervalos do QuickSort. **Conjuntos:** sintomas únicos,
  séries ativas e vértices visitados. **Dicionários:** grafo, métricas e JSON.
- **Compreensões:** filtros, conjuntos normalizados, relatórios e distâncias.
- **Cópia rasa/profunda e recursão:** continuam em `python demo.py` e na API.
  O antigo formulário desses experimentos permanece removido da interface.

## Conferência antes da apresentação

~~~bash
python -m unittest discover -s tests -v
python demo_unidade2.py
~~~

A suíte tem 72 testes cobrindo as estruturas, regras e APIs, incluindo servidor
HTTP local, colisões, reindexação sem perda, todas as ordenações, pesos inválidos,
remoção de vértices, destinos desconectados e gráficos PNG gerados de verdade.
A versão mantida está na raiz do projeto. Os testes de navegador verificam
cadastro, atendimento, peças, conclusão, revisão, falhas isoladas de rotas/hash
e telas de celular. As capturas ficam em `test-results/`.

Testes JavaScript: `node tests/test_interface.cjs` e
`node tests/test_carregamento.cjs`. Para os testes no navegador, veja os comandos
de instalação e `npm run test:e2e` no [README](README.md).
