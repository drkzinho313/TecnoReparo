/* Verificação do módulo JS sem navegador. Requer apenas Node.js (opcional). */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const listeners = {};
const sandbox = {
  window: {},
  document: { addEventListener: (name, fn) => { listeners[name] = fn; }, querySelectorAll: () => [] },
  FormData: class { constructor(form) { return Object.entries(form.dados); } },
};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../frontend/unidade2.js'), 'utf8'), sandbox);
const escape = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const calls = [], notices = [];
let updates = 0, renders = 0;
const point = { id: 'P-0001', nome: '<img src=x onerror=alert(1)>', latitude: 0, longitude: 1 };
const index = { metodo: 'divisao', quantidade: 1, capacidade: 2, fator_carga: .5, colisoes_atuais: 0, maior_cadeia: 1, redimensionamentos: 0, baldes: [{ indice: 0, chaves: ['OS-0001'] }, { indice: 1, chaves: [] }] };
const api = { request: async (url, options = {}) => {
  calls.push({ url, options });
  if (url === '/api/rotas') return { pontos: [point], trechos: [] };
  if (url === '/api/indice') return index;
  if (url === '/api/rotas/calcular') return { encontrada: true, distancia_km: 0, caminho: ['P-0001'], locais: [point], visitados_dijkstra: ['P-0001'], alcancaveis_bfs: ['P-0001'], grafico: 'data:image/png;base64,AA==' };
  if (url === '/api/analises/ordenacao') return { resultados: [], grafico: 'data:image/png;base64,AA==' };
  if (url === '/api/indice/configurar') return { ...index, metodo: options.data.metodo };
  return { id: 'P-0002' };
} };
const ui = new sandbox.window.TecnoUnidade2({ api, escape, icon: () => '', toast: (...args) => notices.push(args), confirmAction: async () => true, atualizar: async () => { updates++; }, renderizar: () => { renders++; }, ordens: () => [], disponivel: () => true });
const button = { classList: { add() {} }, setAttribute() {}, dataset: {} };
const submit = (tipo, dados) => ui.enviar({ dataset: { u2Form: tipo }, dados, querySelector: () => button });
(async () => {
  await ui.carregar();
  assert.ok(ui.renderRotas().includes('&lt;img src=x'));
  assert.ok(!ui.renderRotas().includes('<img src=x'));
  assert.ok(ui.renderAnalises().includes('Bolha, Inserção, Seleção e QuickSort'));
  await submit('local', { nome: 'Coleta', latitude: '-10.1', longitude: '-36.2', ordem_id: '' });
  assert.equal(calls.at(-1).url, '/api/rotas/pontos');
  assert.equal(calls.at(-1).options.data.latitude, -10.1);
  assert.equal(calls.at(-1).options.data.ordem_id, null);
  await submit('conexao', { origem: 'P-0001', destino: 'P-0002', distancia_km: '' });
  assert.equal(calls.at(-1).options.data.distancia_km, null);
  await submit('rota', { origem: 'P-0001', destino: 'P-0001' });
  assert.equal(ui.rota.distancia_km, 0);
  assert.ok(ui.renderRotas().includes('0,00 km'));
  await submit('ordenacao', { tamanho: '40', cenario: 'inverso', repeticoes: '2', semente: '42' });
  assert.equal(calls.at(-1).options.data.tamanho, 40);
  assert.equal(calls.at(-1).options.data.repeticoes, 2);
  await submit('hash', { metodo: 'multiplicacao' });
  assert.equal(ui.indice.metodo, 'multiplicacao');
  assert.equal(ui.consulta, null);
  await submit('consulta', { chave: 'OS-1 & teste' });
  assert.equal(calls.at(-1).url, '/api/indice/consulta?chave=OS-1%20%26%20teste');
  await ui.operar(button, async () => { throw new Error('Sem conexão'); });
  assert.equal(ui.ocupado, false);
  assert.equal(notices.at(-1)[0], 'Sem conexão');
  assert.equal(notices.at(-1)[1], true);
  assert.equal(updates, 3);
  assert.ok(renders >= 7);
  console.log('OK: formulários, parâmetros, escape, respostas e erros do módulo JS.');
})().catch((err) => { console.error(err); process.exitCode = 1; });
