/* Fluxo real no navegador. Cada execução inicia e encerra um servidor vazio. */
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'test-results');

async function iniciarServidor() {
  const process = spawn(global.process.env.PYTHON || 'python', ['-u', 'tests/servidor_navegador.py'], {
    cwd: root, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']
  });
  let erros = '';
  process.stderr.on('data', (data) => { erros += data; });
  try {
    const url = await new Promise((resolve, reject) => {
      const timer = setTimeout(() => reject(new Error('Servidor não iniciou. ' + erros)), 15000);
      let saida = '';
      process.on('error', (erro) => { clearTimeout(timer); reject(erro); });
      process.on('exit', (code) => { clearTimeout(timer); reject(new Error(`Servidor encerrou (${code}). ${erros}`)); });
      process.stdout.on('data', (data) => {
        saida += data;
        const match = saida.match(/http:\/\/127\.0\.0\.1:\d+/);
        if (match) { clearTimeout(timer); resolve(match[0]); }
      });
    });
    return { process, url };
  } catch (erro) { process.kill(); throw erro; }
}

async function aguardarOficina(page) {
  await page.locator('#boot-loader').waitFor({ state: 'hidden' });
  await page.waitForFunction(() => document.querySelector('#connection-state').textContent.includes('Conectado'));
}
async function tela(page, nome) {
  await page.locator(`.nav-link[data-view="${nome}"]`).click();
}
async function painelFechado(page) {
  await page.locator('#order-drawer').waitFor({ state: 'hidden' });
}
async function semRolagemHorizontal(page) {
  const size = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: window.innerWidth }));
  assert.ok(size.page <= size.viewport + 1, `Conteúdo ultrapassa a tela: ${JSON.stringify(size)}`);
}

(async () => {
  fs.mkdirSync(output, { recursive: true });
  const server = await iniciarServidor();
  let browser;
  try {
    browser = await chromium.launch({
      headless: true,
      ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {})
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    page.setDefaultTimeout(10000);
    const erros = [];
    page.on('pageerror', (erro) => erros.push(erro.message));
    const chamadas = [];
    page.on('request', (request) => chamadas.push(new URL(request.url()).pathname));
    await page.goto(server.url);
    await aguardarOficina(page);
    assert.ok(!chamadas.includes('/api/rotas') && !chamadas.includes('/api/indice'));

    // Cadastro, atendimento, pilha de peças, conclusão e revisão pela interface real.
    await page.getByRole('button', { name: 'Nova ordem de serviço', exact: true }).click();
    const form = page.locator('#new-order-form');
    await form.getByLabel('Nome do cliente', { exact: true }).fill('Cliente de teste');
    await form.getByLabel('Contato', { exact: true }).fill('contato de demonstração');
    await form.getByLabel('Número de série', { exact: true }).fill('E2E-001');
    await form.getByLabel('Defeito informado', { exact: true }).fill('Não liga');
    await form.getByRole('button', { name: 'Criar ordem de serviço' }).click();
    await page.locator('#drawer-title').waitFor();
    assert.equal(await page.locator('#drawer-title').textContent(), 'OS-0001');
    await page.keyboard.press('Escape');
    await painelFechado(page);
    await page.getByRole('button', { name: 'Atender próximo', exact: true }).click();
    await page.locator('#part-input').waitFor();
    assert.equal(await page.getByRole('button', { name: 'Concluir atendimento', exact: true }).isEnabled(), false);
    await page.getByLabel('Peça a retirar', { exact: true }).fill('Tampa');
    await page.locator('#part-form').getByRole('button', { name: 'Retirar', exact: true }).click();
    await page.locator('.part-row').waitFor();
    for (const etapa of ['Diagnóstico', 'Reparo', 'Teste final']) {
      await page.getByRole('checkbox', { name: etapa, exact: true }).check();
      await page.waitForFunction(() => !document.querySelector('[data-action="replace-part"]').disabled);
    }
    assert.equal(await page.getByRole('button', { name: 'Concluir atendimento', exact: true }).isEnabled(), false);
    await page.getByRole('button', { name: 'Recolocar última peça', exact: true }).click();
    await page.getByRole('button', { name: 'Concluir atendimento', exact: true }).click();
    await page.locator('#order-drawer').getByRole('button', { name: 'Solicitar revisão', exact: true }).click();
    await page.getByLabel('Motivo da revisão', { exact: true }).fill('Verificar novamente');
    await page.locator('#review-form').getByRole('button', { name: 'Solicitar revisão', exact: true }).click();
    await page.locator('#review-dialog').waitFor({ state: 'hidden' });
    await page.keyboard.press('Escape');
    await painelFechado(page);
    await tela(page, 'revisoes');
    await page.getByRole('button', { name: 'Atender revisão', exact: true }).click();
    await page.getByRole('checkbox', { name: 'Revisão: Verificar novamente', exact: true }).waitFor();
    await page.keyboard.press('Escape');
    await painelFechado(page);
    await tela(page, 'painel');
    await semRolagemHorizontal(page);
    await page.screenshot({ path: path.join(output, 'desktop.png'), fullPage: true });
    console.log('OK: cadastro, atendimento, peças, conclusão, revisão e Escape.');

    // Falhas HTTP de cada área, seguidas de recuperação sem recarregar a página.
    await page.route('**/api/rotas', (route) => route.fulfill({ status: 503, json: { erro: 'Falha simulada nas rotas' } }));
    await tela(page, 'rotas');
    await page.getByRole('heading', { name: 'Rotas temporariamente indisponíveis' }).waitFor();
    assert.equal(await page.locator('#connection-banner').isVisible(), false);
    await tela(page, 'analises');
    await page.getByRole('heading', { name: 'Consulta por número da ordem' }).waitFor();
    await tela(page, 'rotas');
    await page.getByRole('heading', { name: 'Rotas temporariamente indisponíveis' }).waitFor();
    await page.unroute('**/api/rotas');
    await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click();
    await page.getByRole('heading', { name: 'Adicionar local', exact: true }).waitFor();

    await page.route('**/api/indice', (route) => route.fulfill({ status: 503, json: { erro: 'Falha simulada no índice' } }));
    await tela(page, 'analises');
    await page.getByRole('heading', { name: 'Análises temporariamente indisponíveis' }).waitFor();
    await tela(page, 'ordens');
    await page.getByRole('button', { name: 'Abrir ordem OS-0001', exact: true }).waitFor();
    assert.equal(await page.locator('#connection-banner').isVisible(), false);
    await tela(page, 'analises');
    await page.getByRole('heading', { name: 'Análises temporariamente indisponíveis' }).waitFor();
    await page.unroute('**/api/indice');
    await page.getByRole('button', { name: 'Tentar novamente', exact: true }).click();
    await page.getByRole('heading', { name: 'Consulta por número da ordem' }).waitFor();
    console.log('OK: falhas de rotas e hash isoladas, com recuperação local.');

    // Uma área lenta também não impede atendimento nem mantém a abertura bloqueada.
    let liberar;
    const retida = new Promise((resolve) => { liberar = resolve; });
    await page.route('**/api/rotas', async (route) => { await retida; await route.continue(); });
    await page.goto(server.url + '/?cenario=lentidao#rotas');
    await aguardarOficina(page);
    await page.getByText('Carregando rotas…', { exact: true }).waitFor();
    await tela(page, 'ordens');
    await page.getByRole('button', { name: 'Abrir ordem OS-0001', exact: true }).click();
    await page.locator('#drawer-title').waitFor();
    liberar();
    await page.keyboard.press('Escape');
    await painelFechado(page);
    await page.unroute('**/api/rotas');
    console.log('OK: requisição lenta não bloqueia abertura nem consulta de ordens.');

    await page.setViewportSize({ width: 390, height: 844 });
    for (const view of ['painel', 'ordens', 'revisoes', 'rotas', 'analises']) {
      await tela(page, view);
      if (view === 'rotas') await page.getByRole('heading', { name: 'Adicionar local', exact: true }).waitFor();
      if (view === 'analises') await page.getByRole('heading', { name: 'Consulta por número da ordem' }).waitFor();
      await semRolagemHorizontal(page);
    }
    await tela(page, 'painel');
    await page.screenshot({ path: path.join(output, 'mobile.png'), fullPage: true });
    assert.deepEqual(erros, [], 'Nenhuma exceção JavaScript no navegador');
    console.log('OK: cinco telas em 390 px, sem transbordamento horizontal ou exceções JS.');
    await context.close();
  } finally {
    if (browser) await browser.close();
    server.process.kill();
  }
})().catch((erro) => { console.error(erro); process.exitCode = 1; });
