/* Rotas e análises usam exclusivamente os algoritmos da API Python. */
(() => {
  "use strict";
  class TecnoUnidade2 {
    constructor({ api, escape, icon, toast, confirmAction, atualizar, renderizar, ordens, disponivel }) {
      Object.assign(this, { api, escape, icon, toast, confirmAction, atualizar, renderizar, ordens, disponivel });
      this.rede = { pontos: [], trechos: [] };
      this.indice = null;
      this.rota = null;
      this.graficoRede = null;
      this.analise = null;
      this.consulta = null;
      this.exemplo = null;
      this.ocupado = false;
      this.rascunhos = {};
      this.cargas = {
        rotas: { carregada: false, erro: null, pendente: null },
        analises: { carregada: false, erro: null, pendente: null }
      };
      document.addEventListener("input", (evento) => {
        const form = evento.target.closest("form[data-u2-form]");
        if (form) this.rascunhos[form.dataset.u2Form] = Object.fromEntries(new FormData(form));
      });
      document.addEventListener("change", (evento) => {
        const form = evento.target.closest("form[data-u2-form]");
        if (form) this.rascunhos[form.dataset.u2Form] = Object.fromEntries(new FormData(form));
      });
      document.addEventListener("submit", (evento) => {
        const form = evento.target;
        if (!form.matches("form[data-u2-form]")) return;
        evento.preventDefault();
        this.enviar(form);
      });
      document.addEventListener("click", (evento) => {
        const botao = evento.target.closest("[data-u2-action]");
        if (botao && !botao.disabled) this.acao(botao);
      });
    }
    async carregar(area) {
      const areas = area === undefined ? ["rotas", "analises"] : [area];
      await Promise.all(areas.filter((nome) => this.cargas[nome]).map((nome) => this.carregarArea(nome)));
    }
    carregarArea(area) {
      const carga = this.cargas[area];
      if (carga.pendente) return carga.pendente;
      carga.erro = null;
      carga.pendente = Promise.resolve().then(async () => {
        try {
          if (area === "rotas") {
            const rede = await this.api.request("/api/rotas");
            if (JSON.stringify(rede) !== JSON.stringify(this.rede)) { this.rota = null; this.graficoRede = null; }
            this.rede = rede;
          } else {
            const indice = await this.api.request("/api/indice");
            // Consultas e exemplos anteriores podem ficar obsoletos após novos cadastros.
            this.consulta = null;
            if (this.indice && this.indice.metodo !== indice.metodo) this.exemplo = null;
            this.indice = indice;
          }
          carga.carregada = true;
        } catch (erro) {
          carga.erro = erro.message;
        } finally {
          carga.pendente = null;
          this.renderizar();
        }
      });
      this.renderizar();
      return carga.pendente;
    }
    estadoCarregamento(area) {
      const carga = this.cargas[area];
      const nome = area === "rotas" ? "Rotas" : "Análises";
      if (carga.erro) {
        return `<section class="panel"><div class="panel-body" role="alert"><h2>${nome} temporariamente indisponíveis</h2><p>${this.escape(carga.erro)}</p><p>Os atendimentos continuam disponíveis nas outras telas.</p><button type="button" class="button button-secondary" data-u2-action="recarregar" data-area="${area}">${this.icon("refresh")}Tentar novamente</button></div></section>`;
      }
      if (carga.pendente || !carga.carregada) {
        return `<section class="panel" aria-busy="true"><div class="panel-body" role="status">Carregando ${nome.toLowerCase()}…</div></section>`;
      }
      return "";
    }
    numero(valor, casas = 2) { return Number(valor).toLocaleString("pt-BR", { maximumFractionDigits: casas, minimumFractionDigits: casas }); }
    valor(form, campo, padrao = "") { return this.rascunhos[form]?.[campo] ?? padrao; }
    bloqueado(condicao = false) { return `data-u2-blocked="${condicao}" ${this.ocupado || !this.disponivel() || condicao ? "disabled" : ""}`; }
    sincronizar() {
      document.querySelectorAll("[data-u2-blocked]").forEach((el) => {
        el.disabled = this.ocupado || !this.disponivel() || el.dataset.u2Blocked === "true";
      });
    }
    opcoes(itens, atual) {
      return itens.map(([valor, texto]) => `<option value="${this.escape(valor)}" ${String(valor) === String(atual) ? "selected" : ""}>${this.escape(texto)}</option>`).join("");
    }
    locais(atual) { return this.opcoes(this.rede.pontos.map((p) => [p.id, p.nome]), atual); }
    nome(id) { return this.rede.pontos.find((p) => p.id === id)?.nome || id; }
    seletorLocais(form, campo, titulo, indice = 0) {
      const atual = this.valor(form, campo, this.rede.pontos[indice]?.id);
      return `<label class="field">${titulo}<select name="${campo}" required>${this.locais(atual) || '<option value="">Cadastre um local</option>'}</select></label>`;
    }
    botao(texto, acao, icone = "arrow", bloqueado = false) {
      return `<button type="button" class="button button-secondary" data-u2-action="${acao}" ${this.bloqueado(bloqueado)}>${this.icon(icone)}${texto}</button>`;
    }
    figura(dados, nome, descricao) {
      return `<figure class="u2-figure"><div class="u2-figure-scroll"><img src="${this.escape(dados)}" alt="${this.escape(descricao)}"></div><figcaption>Gerado pelo Matplotlib com os dados desta sessão.<a class="subtle-link" href="${this.escape(dados)}" download="${nome}.png">Baixar PNG ${this.icon("arrow-down")}</a></figcaption></figure>`;
    }
    renderRotas() {
      const estado = this.estadoCarregamento("rotas");
      if (estado) return estado;
      const e = this.escape, pontos = this.rede.pontos, rota = this.rota;
      const resultado = rota ? `<div class="u2-result" role="status"><strong>${rota.encontrada ? this.numero(rota.distancia_km) + " km · caminho encontrado" : "Não há caminho entre esses locais"}</strong><p>${rota.encontrada ? rota.locais.map((p) => e(p.nome)).join(" → ") : "Cadastre uma conexão para alcançar o destino."}</p><small>Dijkstra: ${rota.visitados_dijkstra.length} locais visitados. Busca em largura: ${rota.alcancaveis_bfs.length} locais alcançáveis a partir da origem.</small></div>` : "";
      return `<div class="u2-root" aria-busy="${this.ocupado}">
        <div class="u2-notice">${this.icon("info")}<p>Planeje coletas e entregas pelas conexões cadastradas. O exemplo usa locais e distâncias fictícios. Coordenadas e conexões próprias podem ser adicionadas; o cálculo não consulta ruas ou trânsito.</p></div>
        <section class="panel"><header class="panel-header"><div><h2>Encontre o melhor caminho</h2><p>${pontos.length} locais · ${this.rede.trechos.length} conexões de mão dupla</p></div>${this.botao("Carregar exemplo", "exemplo", "plus", !!pontos.length)}</header>
          <div class="panel-body"><form data-u2-form="rota" class="u2-inline-form">${this.seletorLocais("rota", "origem", "Saída")}${this.seletorLocais("rota", "destino", "Destino", 1)}<button type="submit" class="button button-primary" ${this.bloqueado(!pontos.length)}>${this.icon("arrow")}Calcular rota</button>${this.botao("Visualizar rede", "mapa", "layers", !pontos.length)}</form>${resultado}
          ${this.graficoRede ? this.figura(this.graficoRede, "tecnoreparo-rede", "Rede geográfica de coleta e entrega; o caminho calculado aparece em verde.") : '<div class="u2-chart-placeholder">Visualize a rede ou calcule uma rota para gerar o gráfico.</div>'}</div></section>
        <div class="u2-grid"><section class="panel"><header class="panel-header"><div><h2>Adicionar local</h2><p>Vincule um ponto de coleta ou entrega a uma ordem.</p></div></header><div class="panel-body">
          <form data-u2-form="local" class="u2-form"><label class="field">Nome do local<input name="nome" required maxlength="60" placeholder="Ex.: ponto de coleta do cliente" value="${e(this.valor("local", "nome"))}"></label>
          <div class="u2-form-pair"><label class="field">Latitude<input name="latitude" type="number" required min="-90" max="90" step="any" placeholder="-10.120" value="${e(this.valor("local", "latitude"))}"></label><label class="field">Longitude<input name="longitude" type="number" required min="-180" max="180" step="any" placeholder="-36.175" value="${e(this.valor("local", "longitude"))}"></label></div>
          <label class="field">Ordem vinculada <span class="optional">opcional</span><select name="ordem_id"><option value="">Sem vínculo</option>${this.opcoes(this.ordens().map((o) => [o.id, o.id + " · " + o.cliente.nome]), this.valor("local", "ordem_id"))}</select></label>
          <small class="helper-text">Use coordenadas em graus decimais. Até 40 locais por rede.</small><button type="submit" class="button button-primary" ${this.bloqueado(pontos.length >= 40)}>${this.icon("plus")}Adicionar local</button></form></div></section>
        <section class="panel"><header class="panel-header"><div><h2>Conectar locais</h2><p>Defina os caminhos que podem ser percorridos.</p></div></header><div class="panel-body"><form data-u2-form="conexao" class="u2-form">
          <div class="u2-form-pair">${this.seletorLocais("conexao", "origem", "Primeiro local")}${this.seletorLocais("conexao", "destino", "Segundo local", 1)}</div>
          <label class="field">Distância em km <span class="optional">opcional</span><input type="number" name="distancia_km" step="any" min="0.000001" max="40075" placeholder="Ex.: 2.5" value="${e(this.valor("conexao", "distancia_km"))}"></label>
          <small class="helper-text">Em branco, calcula a distância geográfica aproximada pela fórmula de Haversine. Ela não representa um trajeto por ruas. Repetir uma conexão atualiza sua distância.</small><button type="submit" class="button button-primary" ${this.bloqueado(pontos.length < 2)}>${this.icon("plus")}Salvar conexão</button></form></div></section></div>
        <div class="u2-grid"><section class="panel"><header class="panel-header"><div><h2>Locais cadastrados</h2><p>Remover um local também remove suas conexões.</p></div></header><div class="u2-list">${pontos.length ? pontos.map((p) => `<div class="u2-list-row"><div><strong>${e(p.nome)}</strong><small>${e(p.id)} · ${this.numero(p.latitude, 5)}, ${this.numero(p.longitude, 5)}${p.ordem_id ? " · " + e(p.ordem_id) : ""}</small></div><button type="button" class="icon-button" data-u2-action="remover-local" data-id="${e(p.id)}" aria-label="Remover ${e(p.nome)}" ${this.bloqueado()}>${this.icon("trash")}</button></div>`).join("") : '<p class="helper-text">Nenhum local cadastrado.</p>'}</div></section>
        <section class="panel"><header class="panel-header"><div><h2>Conexões disponíveis</h2><p>Pesos usados no cálculo do menor caminho.</p></div></header><div class="u2-list">${this.rede.trechos.length ? this.rede.trechos.map((t) => `<div class="u2-list-row"><div><strong>${e(this.nome(t.origem))} ↔ ${e(this.nome(t.destino))}</strong><small>${this.numero(t.distancia_km)} km · ${t.medida === "informada" ? "distância informada" : "aproximação geográfica"}</small></div><button type="button" class="icon-button" data-u2-action="remover-conexao" data-origem="${e(t.origem)}" data-destino="${e(t.destino)}" aria-label="Remover conexão entre ${e(this.nome(t.origem))} e ${e(this.nome(t.destino))}" ${this.bloqueado()}>${this.icon("trash")}</button></div>`).join("") : '<p class="helper-text">Nenhuma conexão cadastrada.</p>'}</div></section></div></div>`;
    }
    renderAnalises() {
      const estado = this.estadoCarregamento("analises");
      if (estado) return estado;
      const e = this.escape, indice = this.indice;
      if (!indice) return '<p class="helper-text">Aguardando os dados do servidor.</p>';
      const metodos = [["divisao", "Divisão"], ["multiplicacao", "Multiplicação"], ["dobramento", "Dobramento"]];
      const consulta = this.consulta, exemplo = this.exemplo, analise = this.analise;
      return `<div class="u2-root" aria-busy="${this.ocupado}"><div class="u2-grid">
        <section class="panel"><header class="panel-header"><div><h2>Consulta por número da ordem</h2><p>Busca direta no índice de atendimentos.</p></div><span class="badge green">Hash próprio</span></header><div class="panel-body">
          <form data-u2-form="consulta" class="u2-inline-form"><label class="field">Ordem de serviço<input name="chave" maxlength="30" required placeholder="OS-0001" value="${e(this.valor("consulta", "chave"))}"></label><button type="submit" class="button button-primary" ${this.bloqueado()}>${this.icon("search")}Consultar</button></form>
          ${consulta ? `<div class="u2-result" role="status"><strong>${consulta.encontrada ? e(consulta.ordem.cliente.nome) : "Ordem não encontrada"}</strong><p>Balde ${consulta.indice} · ${consulta.comparacoes} comparações · método ${e(consulta.metodo)}.</p><small>Chaves verificadas: ${e(consulta.chaves_visitadas.join(" → ") || "balde vazio")}</small>${consulta.encontrada ? `<button class="button button-soft button-small" data-action="open-order" data-id="${e(consulta.chave)}">Abrir ${e(consulta.chave)} ${this.icon("arrow")}</button>` : ""}</div>` : '<p class="helper-text">Use o número de uma ordem cadastrada para acompanhar sua localização na tabela.</p>'}
        </div></section><section class="panel"><header class="panel-header"><div><h2>Organização do índice</h2><p>Altere a função hash e redistribua os mesmos registros.</p></div></header><div class="panel-body"><form data-u2-form="hash" class="u2-inline-form"><label class="field">Método hash<select name="metodo">${this.opcoes(metodos, indice.metodo)}</select></label><button type="submit" class="button button-secondary" ${this.bloqueado()}>${this.icon("refresh")}Aplicar método</button></form>
          <div class="u2-metrics"><div><strong>${indice.quantidade}</strong><small>ordens</small></div><div><strong>${indice.capacidade}</strong><small>baldes</small></div><div><strong>${this.numero(indice.fator_carga)}</strong><small>fator de carga</small></div><div><strong>${indice.colisoes_atuais}</strong><small>colisões atuais</small></div></div></div></section></div>
        <section class="panel"><div class="panel-body"><details class="u2-details" ${exemplo ? "open" : ""}><summary>Como o índice organiza as ordens</summary><div class="u2-detail-content"><p>Divisão usa o resto da divisão do código da chave. Multiplicação distribui pela parte fracionária de um produto. Dobramento soma blocos dos bytes da chave. Colisões ficam em listas encadeadas dentro dos baldes.</p>
          <div class="u2-buckets">${indice.baldes.map((b) => `<div class="u2-bucket ${b.chaves.length ? "filled" : ""}"><small>BALDE ${b.indice}</small><span>${e(b.chaves.join(" → ") || "Vazio")}</span></div>`).join("")}</div><p class="helper-text">Maior cadeia: ${indice.maior_cadeia} registros. Redimensionamentos desde a criação deste índice: ${indice.redimensionamentos}. Ao ultrapassar 0,75 de carga, os registros são redistribuídos em um vetor maior.</p>
          ${this.botao("Demonstrar colisão e remoção", "colisao", "layers")}
          ${exemplo ? `<div class="u2-result" role="status"><strong>Três registros no mesmo balde</strong><p>Inserção: ${e(exemplo.inseridas.join(" → "))}. Busca de ${e(exemplo.busca.chave)}: ${exemplo.busca.comparacoes} comparações.</p><p>Após remover ${e(exemplo.removida)}, a busca de ${e(exemplo.busca_apos_remocao.chave)} continua funcionando, com ${exemplo.busca_apos_remocao.comparacoes} comparações.</p><small>${e(exemplo.aviso)}</small></div>` : ""}</div></details></div></section>
        <section class="panel"><header class="panel-header"><div><h2>Comparar algoritmos de ordenação</h2><p>Bolha, Inserção, Seleção e QuickSort executados em Python.</p></div><span class="badge">Matplotlib</span></header><div class="panel-body"><form data-u2-form="ordenacao" class="u2-benchmark-form">
          <label class="field">Quantidade de ordens<input name="tamanho" type="number" required min="2" max="500" step="1" value="${e(this.valor("ordenacao", "tamanho", 250))}"></label>
          <label class="field">Cenário<select name="cenario">${this.opcoes([["aleatorio", "Aleatório"], ["ordenado", "Já ordenado"], ["inverso", "Ordem inversa"], ["repetidos", "Chaves repetidas"]], this.valor("ordenacao", "cenario", "aleatorio"))}</select></label>
          <label class="field">Repetições<input name="repeticoes" type="number" required min="1" max="7" step="1" value="${e(this.valor("ordenacao", "repeticoes", 3))}"></label><label class="field">Semente<input name="semente" type="number" required min="0" max="1000000" step="1" value="${e(this.valor("ordenacao", "semente", 42))}"></label>
          <button type="submit" class="button button-primary" ${this.bloqueado()}>${this.icon("chart")}Executar comparação</button></form><p class="helper-text">Usa ordens sintéticas e entradas iguais para todos os métodos. Os tempos são medidos nesta máquina; os cadastros da oficina são preservados.</p>
          ${analise ? `<div class="u2-result" role="status"><strong>Menor mediana neste ensaio: ${e(analise.menor_mediana)}</strong><p>${analise.tamanho} ordens no maior conjunto · ${analise.repeticoes} repetições · semente ${analise.semente}</p><small>${e(analise.metodologia)}</small></div>${this.figura(analise.grafico, "tecnoreparo-ordenacao", "Comparação dos quatro algoritmos: tempo mediano por tamanho e intervalo mínimo e máximo.")}<div class="u2-table-scroll"><table class="u2-table"><caption>Resultados para ${analise.tamanho} ordens</caption><thead><tr><th>Algoritmo</th><th>Mediana (ms)</th><th>Mínimo–máximo (ms)</th><th>Comparações</th><th>Movimentos</th></tr></thead><tbody>${analise.resultados.filter((r) => r.tamanho === analise.tamanho).map((r) => `<tr><th scope="row">${e(r.nome)}</th><td>${this.numero(r.mediana_ms, 4)}</td><td>${this.numero(r.minimo_ms, 4)} – ${this.numero(r.maximo_ms, 4)}</td><td>${r.comparacoes}</td><td>${r.movimentos}</td></tr>`).join("")}</tbody></table></div>` : '<div class="u2-chart-placeholder">Execute a comparação para visualizar os tempos medidos.</div>'}
          <p class="helper-text">Para aplicar os algoritmos às ordens reais, escolha o campo e o método na tela <a class="subtle-link" href="#ordens">Ordens de serviço</a>.</p></div></section></div>`;
    }
    async operar(botao, operacao, { altera = false, mensagem = "" } = {}) {
      if (this.ocupado || !this.disponivel()) return;
      this.ocupado = true;
      const controles = [...document.querySelectorAll(".u2-root button, .u2-root input, .u2-root select")];
      controles.forEach((el) => { el.disabled = true; });
      botao?.classList.add("is-loading");
      botao?.setAttribute("aria-busy", "true");
      try {
        await operacao();
        if (altera) {
          try { await this.atualizar(); }
          catch (_) { this.toast("A alteração foi salva. Atualize para buscar o estado mais recente.", true); }
        }
        if (mensagem) this.toast(mensagem);
      } catch (erro) { this.toast(erro.message, true); }
      finally { this.ocupado = false; this.renderizar(); }
    }
    async enviar(form) {
      const tipo = form.dataset.u2Form, dados = Object.fromEntries(new FormData(form));
      this.rascunhos[tipo] = dados;
      const botao = form.querySelector('button[type="submit"]');
      const post = (path, data) => this.api.request(path, { method: "POST", data, timeoutMs: path === "/api/analises/ordenacao" ? 45000 : 12000 });
      if (tipo === "consulta") return this.operar(botao, async () => { this.consulta = await this.api.request("/api/indice/consulta?chave=" + encodeURIComponent(dados.chave)); });
      if (tipo === "hash") return this.operar(botao, async () => { this.indice = await post("/api/indice/configurar", dados); this.consulta = null; this.exemplo = null; }, { altera: true, mensagem: "Índice reorganizado. Os atendimentos foram preservados." });
      if (tipo === "rota") return this.operar(botao, async () => { this.rota = await post("/api/rotas/calcular", dados); this.graficoRede = this.rota.grafico; });
      if (tipo === "ordenacao") return this.operar(botao, async () => { this.analise = await post("/api/analises/ordenacao", { tamanho: Number(dados.tamanho), cenario: dados.cenario, repeticoes: Number(dados.repeticoes), semente: Number(dados.semente) }); });
      if (tipo === "local") return this.operar(botao, async () => {
        await post("/api/rotas/pontos", { nome: dados.nome, latitude: Number(dados.latitude), longitude: Number(dados.longitude), ordem_id: dados.ordem_id || null });
        delete this.rascunhos.local;
      }, { altera: true, mensagem: "Local adicionado à rede." });
      if (tipo === "conexao") return this.operar(botao, async () => {
        await post("/api/rotas/conexoes", { origem: dados.origem, destino: dados.destino, distancia_km: dados.distancia_km === "" ? null : Number(dados.distancia_km) });
      }, { altera: true, mensagem: "Conexão salva. Calcule novamente para atualizar a rota." });
    }
    async acao(botao) {
      if (botao.dataset.u2Action === "recarregar") return this.carregar(botao.dataset.area);
      if (this.ocupado || !this.disponivel()) return;
      const acao = botao.dataset.u2Action;
      if (acao === "mapa") return this.operar(botao, async () => { this.graficoRede = (await this.api.request("/api/rotas/mapa")).grafico; this.rota = null; });
      if (acao === "colisao") return this.operar(botao, async () => { this.exemplo = await this.api.request("/api/indice/demonstrar", { method: "POST", data: { metodo: this.indice.metodo } }); });
      if (acao === "exemplo") return this.operar(botao, () => this.api.request("/api/rotas/exemplo", { method: "POST", data: {} }), { altera: true, mensagem: "Rede de exemplo carregada." });
      if (acao === "remover-local" && await this.confirmAction("Remover este local?", "As conexões desse local também serão removidas. A ordem de serviço vinculada será preservada.")) {
        return this.operar(botao, () => this.api.request("/api/rotas/pontos/" + botao.dataset.id, { method: "DELETE" }), { altera: true, mensagem: "Local removido da rede." });
      }
      if (acao === "remover-conexao" && await this.confirmAction("Remover esta conexão?", "Esse trecho deixará de participar do cálculo das rotas.")) {
        return this.operar(botao, () => this.api.request("/api/rotas/conexoes", { method: "DELETE", data: { origem: botao.dataset.origem, destino: botao.dataset.destino } }), { altera: true, mensagem: "Conexão removida." });
      }
    }
  }
  window.TecnoUnidade2 = TecnoUnidade2;
})();
