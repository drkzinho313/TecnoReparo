/* Regressões de falha parcial, recuperação e requisições concorrentes. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const sandbox = { window: {}, document: { addEventListener() {}, querySelectorAll: () => [] } };
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../frontend/unidade2.js'), 'utf8'), sandbox);
const rede = { pontos: [], trechos: [] };
const indice = { metodo: 'divisao', quantidade: 0, capacidade: 17, fator_carga: 0, colisoes_atuais: 0, maior_cadeia: 0, redimensionamentos: 0, baldes: [] };
const calls = [];
let falharRotas = true, falharIndice = false, liberarRotas;
const ui = new sandbox.window.TecnoUnidade2({
  api: { request: async (url) => {
    calls.push(url);
    if (url === '/api/rotas') {
      if (falharRotas) throw new Error('Rotas fora do ar');
      if (liberarRotas) await new Promise((resolve) => { liberarRotas = resolve; });
      return rede;
    }
    if (falharIndice) throw new Error('Índice fora do ar');
    return indice;
  } },
  escape: String, icon: () => '', toast() {}, confirmAction: async () => true,
  atualizar: async () => {}, renderizar() {}, ordens: () => [], disponivel: () => true
});
(async () => {
  await ui.carregar('painel');
  assert.equal(calls.length, 0, 'Painel não deve carregar recursos complementares');
  await ui.carregar();
  assert.equal(ui.cargas.rotas.erro, 'Rotas fora do ar');
  assert.equal(ui.indice, indice, 'Falha em rotas não deve impedir o índice');
  assert.match(ui.renderRotas(), /Tentar novamente/);
  assert.match(ui.renderAnalises(), /Comparar algoritmos/);

  falharRotas = false;
  await ui.acao({ dataset: { u2Action: 'recarregar', area: 'rotas' } });
  assert.equal(ui.cargas.rotas.erro, null);
  assert.match(ui.renderRotas(), /Adicionar local/);

  falharIndice = true;
  await ui.carregar('analises');
  assert.match(ui.renderAnalises(), /Índice fora do ar/);
  assert.match(ui.renderRotas(), /Adicionar local/);

  const antes = calls.length;
  liberarRotas = true;
  const primeira = ui.carregar('rotas');
  const segunda = ui.carregar('rotas');
  await Promise.resolve();
  assert.equal(calls.length, antes + 1, 'Reaproveitar carregamento em andamento');
  assert.match(ui.renderRotas(), /Carregando rotas/);
  liberarRotas();
  await Promise.all([primeira, segunda]);
  assert.equal(ui.cargas.rotas.pendente, null);
  falharIndice = false;
  await ui.carregar('analises');
  assert.equal(ui.cargas.analises.erro, null);
  console.log('OK: carregamento sob demanda, falhas isoladas, recuperação e concorrência.');
})().catch((erro) => { console.error(erro); process.exitCode = 1; });
