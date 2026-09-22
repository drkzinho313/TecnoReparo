/* Interface do TecnoReparo. Todas as alterações são realizadas pela API Python. */
(() => {
  "use strict";

  const $ = (selector, parent = document) => parent.querySelector(selector);
  const $$ = (selector, parent = document) => [...parent.querySelectorAll(selector)];
  const escape = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);
  const icon = (name, extra = "") => `<svg class="icon ${extra}" aria-hidden="true"><use href="/assets/icons.svg#${name}"></use></svg>`;
  const formatNumber = (value) => String(value).padStart(2, "0");
  const reducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const normalize = (value) => String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const STATUS = {
    aguardando: { label: "Aguardando", color: "amber" },
    em_reparo: { label: "Em reparo", color: "blue" },
    concluida: { label: "Concluída", color: "green" },
    aguardando_revisao: { label: "Em revisão", color: "purple" }
  };
  const VIEWS = {
    painel: "Visão geral", ordens: "Ordens de serviço", revisoes: "Revisões",
    relatorios: "Relatórios", laboratorio: "Laboratório"
  };
  const state = {
    view: VIEWS[location.hash.slice(1)] ? location.hash.slice(1) : "painel",
    orders: [], workshop: { bancadas: [], fila: [], revisoes: [] },
    report: { total_ordens: 0, por_status: {}, tipos_de_equipamento: [], indices_bancadas_livres: [] },
    online: false, loaded: false, busy: false, refreshing: false,
    query: "", filter: "todos", selectedId: null, drawerTab: "reparo",
    stepDraft: "", partDraft: "", reviewId: null,
    labOrder: "", labSize: 8, labResult: null, confirmation: null
  };

  class ApiClient {
    constructor() { this.pending = 0; }
    async request(path, { method = "GET", data } = {}) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 12000);
      this.pending += 1;
      $("#network-progress").hidden = false;
      try {
        const options = { method, signal: controller.signal, credentials: "same-origin" };
        if (data !== undefined) {
          options.headers = { "Content-Type": "application/json" };
          options.body = JSON.stringify(data);
        }
        const response = await fetch(path, options);
        const content = await response.json();
        if (!response.ok) {
          const error = new Error(content.erro || "Não foi possível concluir esta ação.");
          error.httpStatus = response.status;
          throw error;
        }
        return content.dados;
      } catch (error) {
        if (error.name === "AbortError") throw new Error("O servidor demorou a responder. Tente atualizar.");
        if (!error.httpStatus && (error instanceof TypeError || error instanceof SyntaxError)) {
          throw new Error("Não foi possível conectar ao servidor. Confira se o TecnoReparo está em execução.");
        }
        throw error;
      } finally {
        clearTimeout(timeout);
        this.pending -= 1;
        $("#network-progress").hidden = this.pending === 0;
      }
    }
  }
  const api = new ApiClient();

  function badge(status) {
    const info = STATUS[status] || { label: status, color: "" };
    return `<span class="badge ${info.color}"><span class="status-dot"></span>${escape(info.label)}</span>`;
  }
  function deviceIcon(order) { return /notebook|laptop/i.test(order.equipamento.tipo) ? "laptop" : "monitor"; }
  function getOrder(id) { return state.orders.find((order) => order.id === id); }
  function writable(blocked = false) {
    return `data-mutate data-blocked="${blocked}" ${blocked || state.busy || !state.online ? "disabled" : ""}`;
  }
  function empty(title, text, { compact = false, action = false } = {}) {
    return `<div class="empty-state ${compact ? "compact-empty" : ""}">${icon("inbox")}<h3>${escape(title)}</h3><p>${escape(text)}</p>${action ? `<button class="button button-soft" data-action="new-order">${icon("plus")}Cadastrar equipamento</button>` : ""}</div>`;
  }
  function heading(title, subtitle, { eyebrow = "SEU ESPAÇO DE TRABALHO", create = true } = {}) {
    const date = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "long" }).format(new Date());
    
      
  }
  function stats() {
    const counts = state.report.por_status;
    const items = [
      ["Ordens de serviço", state.report.total_ordens, "Todos os equipamentos", "clipboard", ""],
      ["Em espera", (counts.aguardando || 0) + (counts.aguardando_revisao || 0), "Novos atendimentos e revisões", "clock", "amber"],
      ["Em reparo", counts.em_reparo || 0, "Cuidados em andamento", "wrench", "blue"],
      ["Concluídas", counts.concluida || 0, "Prontas para a próxima etapa", "check-circle", "green"]
    ];
    return `<div class="stats-grid">${items.map(([label, value, note, name, color]) => `<article class="stat-card">
      <div class="stat-top"><span class="stat-label">${label}</span><span class="stat-icon ${color}">${icon(name)}</span></div>
      <strong class="stat-value">${formatNumber(value)}</strong><small class="stat-note">${note}</small></article>`).join("")}</div>`;
  }
  function benches() {
    const available = state.workshop.bancadas.filter((bench) => bench.livre).length;
    return `<section class="panel"><header class="panel-header"><div><h2>Bancadas de trabalho</h2><p>Um espaço para cada reparo.</p></div><span class="availability"><span class="status-dot"></span>${available} ${available === 1 ? "disponível" : "disponíveis"}</span></header>
      <div class="panel-body"><div class="bench-grid">${state.workshop.bancadas.map((bench) => {
        const order = getOrder(bench.ordem_id);
        return order ? `<button class="bench occupied" data-action="open-order" data-id="${escape(order.id)}" aria-label="Abrir ${escape(order.id)}, bancada ${bench.indice + 1}">
          <span class="bench-top"><span class="bench-number">Bancada ${formatNumber(bench.indice + 1)}</span><span class="bench-light"></span></span>
          <span class="bench-device">${icon(deviceIcon(order))}</span><strong>${escape(order.equipamento.tipo)}</strong><small>${escape(order.id)} · ${escape(order.cliente.nome)}</small>
          <span class="bench-footer">Em atendimento ${icon("arrow")}</span></button>` :
          `<article class="bench"><span class="bench-top"><span class="bench-number">Bancada ${formatNumber(bench.indice + 1)}</span><span class="bench-light"></span></span>
          <span class="bench-device">${icon("monitor")}</span><strong>Pronta para receber</strong><small>Espaço disponível</small><span class="bench-free-line"></span></article>`;
      }).join("")}</div></div></section>`;
  }
  function queue() {
    const orders = state.workshop.fila.map(getOrder).filter(Boolean);
    const available = state.workshop.bancadas.some((bench) => bench.livre);
    return `<section class="panel"><header class="panel-header"><div><h2>Próximos atendimentos</h2><p>Cada equipamento tem sua vez.</p></div><span class="badge amber">${formatNumber(orders.length)}</span></header>
      <div class="panel-body">${orders.length ? `<ol class="queue-list">${orders.slice(0, 3).map((order, i) => `<li class="queue-row"><span class="queue-position">${formatNumber(i + 1)}</span><div class="queue-info"><strong>${escape(order.cliente.nome)}</strong><small>${escape(order.equipamento.tipo)} · ${escape(order.id)}</small></div>${icon("chevron")}</li>`).join("")}</ol>` :
      empty("Tudo em dia por aqui", "Nenhum equipamento aguardando atendimento.", { compact: true })}
      ${orders.length > 3 ? `<p class="queue-more">E mais ${orders.length - 3} na espera.</p>` : ""}
      <div class="queue-actions"><button class="button button-soft button-full" data-action="attend" data-origin="fila" ${writable(!orders.length || !available)}><span>Atender próximo</span>${icon("arrow")}</button>
      <p class="helper-text">${!available ? "Todas as bancadas estão ocupadas." : orders.length ? "O primeiro da fila ocupa uma bancada livre." : "Novas ordens aparecerão aqui."}</p></div></div></section>`;
  }
  function filteredOrders() {
    const query = normalize(state.query);
    return [...state.orders].reverse().filter((order) => {
      const statusMatches = state.view !== "ordens" || state.filter === "todos" || order.status === state.filter;
      const searchable = [order.id, order.cliente.nome, order.equipamento.tipo, order.equipamento.numero_serie, order.equipamento.defeito].join(" ");
      return statusMatches && (!query || normalize(searchable).includes(query));
    });
  }
  function tableContent(compact = false) {
    const filtered = filteredOrders();
    const orders = compact ? filtered.slice(0, 5) : filtered;
    if (!orders.length) return empty(state.query || state.filter !== "todos" ? "Nenhum resultado encontrado" : "Sua primeira ordem começa aqui", state.query ? "Tente outro nome, número de ordem ou equipamento." : "Cadastre um equipamento para organizar o atendimento.", { action: !state.orders.length });
    return `<table class="orders-table"><thead><tr><th>Ordem</th><th>Equipamento / cliente</th><th>Situação</th><th>Bancada</th><th><span class="sr-only">Detalhes</span></th></tr></thead>
      <tbody>${orders.map((order) => `<tr><td><span class="order-code">${escape(order.id)}</span></td>
        <td><div class="device-cell"><span class="device-symbol">${icon(deviceIcon(order))}</span><div class="device-copy"><strong>${escape(order.equipamento.tipo)} <span class="optional-code">· ${escape(order.equipamento.numero_serie)}</span></strong><small>${escape(order.cliente.nome)}</small></div></div></td>
        <td>${badge(order.status)}</td><td><span class="bench-label">${order.bancada === null ? "—" : formatNumber(order.bancada + 1)}</span></td>
        <td><button class="icon-button" data-action="open-order" data-id="${escape(order.id)}" aria-label="Abrir ordem ${escape(order.id)}">${icon("arrow")}</button></td></tr>`).join("")}</tbody></table>
        <div class="table-bottom">Exibindo ${orders.length} de ${filtered.length} ${filtered.length === 1 ? "ordem" : "ordens"}.</div>`;
  }
  function orderPanel(compact = false) {
    const filters = [["todos", "Todas"], ...Object.entries(STATUS).map(([value, info]) => [value, info.label])];
    return `<section class="panel"><header class="panel-header"><div><h2>${compact ? "Ordens recentes" : "Todos os atendimentos"}</h2><p>${compact ? "Acompanhe o que está acontecendo na oficina." : "Encontre um equipamento e acompanhe cada etapa."}</p></div>${compact ? `<a class="subtle-link" href="#ordens">Ver todas ${icon("arrow")}</a>` : ""}</header>
      ${compact ? "" : `<div class="filters" aria-label="Filtrar ordens por situação">${filters.map(([value, name]) => `<button class="filter-tab ${state.filter === value ? "active" : ""}" aria-pressed="${state.filter === value}" data-action="filter" data-filter="${value}">${name}</button>`).join("")}</div>`}
      <div class="table-toolbar"><label class="search-field">${icon("search")}<input id="order-search" aria-label="Buscar ordens" value="${escape(state.query)}" placeholder="Buscar por cliente, ordem ou equipamento…" type="search" autocomplete="off"></label><span class="result-count" id="result-count">${filteredOrders().length} ordens</span></div>
      <div id="orders-result">${tableContent(compact)}</div></section>`;
  }
  function renderDashboard() {
    return heading("Sua oficina, em ordem.", "Menos tarefas soltas. Mais cuidado com cada equipamento.") + stats() +
      `<div class="dashboard-grid">${benches()}${queue()}</div>` + orderPanel(true);
  }
  function renderReviews() {
    const reviews = state.workshop.revisoes;
    const available = state.workshop.bancadas.some((bench) => bench.livre);
    return heading("Um novo olhar para cada reparo.", "Organize os retornos e dê atenção ao que precisa de revisão.", { eyebrow: "REVISÕES", create: false }) +
      `<div class="review-controls"><button class="button button-primary" data-action="attend" data-origin="revisoes" ${writable(!reviews.length || !available)}>${icon("wrench")}Atender revisão</button>
      <button class="button button-secondary" data-action="cancel-review" data-side="inicio" ${writable(!reviews.length)}>Cancelar do início</button><button class="button button-secondary" data-action="cancel-review" data-side="fim" ${writable(!reviews.length)}>Cancelar do fim</button></div>
      <div class="review-list">${reviews.length ? reviews.map((review, index) => {
        const order = getOrder(review.ordem_id);
        if (!order) return "";
        return `<article class="panel review-item"><span class="queue-position">${formatNumber(index + 1)}</span><div class="review-description"><div class="review-meta"><span class="order-code">${escape(review.ordem_id)}</span>${review.urgente ? `<span class="badge urgent">${icon("bolt")}Urgente</span>` : `<span class="badge">Revisão comum</span>`}</div><h3>${escape(order.cliente.nome)} · ${escape(order.equipamento.tipo)}</h3><p>${escape(review.motivo)}</p></div><button class="button button-ghost button-small" data-action="open-order" data-id="${escape(review.ordem_id)}">Ver ordem ${icon("arrow")}</button></article>`;
      }).join("") : `<section class="panel">${empty("Nenhuma revisão pendente", "Abra uma ordem concluída para solicitar uma nova revisão.")}</section>`}</div>
      <div class="review-explanation">${icon("info")}<span>Revisões comuns entram no fim; urgentes entram no início. Entre duas urgentes, a mais recente fica à frente. A fila de novos atendimentos permanece separada.</span></div>`;
  }
  function renderReports() {
    const total = state.report.total_ordens;
    const types = state.orders.reduce((counts, order) => {
      counts[order.equipamento.tipo] = (counts[order.equipamento.tipo] || 0) + 1;
      return counts;
    }, Object.create(null));
    return heading("Uma visão clara do seu trabalho.", { eyebrow: "RELATÓRIOS", create: false }) + stats() +
      `<div class="report-grid"><section class="panel"><header class="panel-header"><div><h2>Situação dos atendimentos</h2><p>Distribuição de todas as ordens cadastradas.</p></div></header><div class="panel-body">
      ${Object.entries(STATUS).map(([value, info]) => {
        const count = state.report.por_status[value] || 0;
        return `<div class="report-row"><div class="report-row-top"><span>${info.label}</span><strong>${count} ${count === 1 ? "ordem" : "ordens"}</strong></div><div class="report-track" role="img" aria-label="${info.label}: ${count} de ${total} ordens"><div class="report-fill ${info.color}" style="width:${total ? count / total * 100 : 0}%"></div></div></div>`;
      }).join("")}</div></section><section class="panel"><header class="panel-header"><div><h2>Equipamentos recebidos</h2><p>Tipos presentes nesta sessão.</p></div></header><div class="panel-body">${Object.keys(types).length ?
      Object.entries(types).map(([type, count]) => `<div class="type-row"><span class="device-symbol">${icon(/notebook/i.test(type) ? "laptop" : "monitor")}</span><strong>${escape(type)}</strong><span>${formatNumber(count)}</span></div>`).join("") :
      empty("Aguardando o primeiro cadastro", "Os tipos de equipamento aparecerão aqui.", { compact: true })}</div></section></div>`;
  }
  function renderLab() {
    const options = state.orders.map((order) => `<option value="${escape(order.id)}" ${state.labOrder === order.id ? "selected" : ""}>${escape(order.id)} · ${escape(order.cliente.nome)}</option>`).join("");
    return heading("Por dentro do TecnoReparo.") +
      `<div class="lab-intro">${icon("code")}<p>Consulte a distribuição dos equipamentos e a sequência dos próximos atendimentos, com base nas ordens de serviço cadastradas.</p></div>
      <div class="lab-grid"><section class="panel"><header class="panel-header"><div><h2>Vetor de bancadas</h2></div></header><div class="panel-body"><div class="structure-strip">${state.workshop.bancadas.map((bench) => `<div class="structure-node"><small>ÍNDICE ${bench.indice}</small>${escape(bench.ordem_id || "Livre")}</div>`).join("")}</div></div></section>
      <section class="panel"><header class="panel-header"><div><h2>Fila de atendimento</h2></div></header><div class="panel-body"><div class="structure-strip">${state.workshop.fila.length ? state.workshop.fila.map((id, i) => `${i ? icon("arrow") : ""}<div class="structure-node"><small>${i ? "EM ESPERA" : "INÍCIO"}</small>${escape(id)}</div>`).join("") : `<p class="helper-text">A fila está vazia.</p>`}</div></div></section>
      <form id="lab-form" class="lab-form"><label class="field">Ordem de serviço<select id="lab-order" required>${options || '<option value="">Cadastre uma ordem primeiro</option>'}</select></label>
      <label class="field">Busca<input id="lab-size" type="number" min="1" max="500" step="1" required value="${state.labSize}"></label>
      <button class="button button-primary" type="submit" ${!state.orders.length ? "disabled" : ""}>${icon("code")}Executar </button></form><div id="lab-result">${labResults()}</div></div></section></div>`;
  }
  function labResults() {
    const result = state.labResult;
    if (!result) return "";
    return `<div class="lab-result" role="status"><div class="lab-result-box"><h3>Recursão</h3><p>Simples: ${result.recursao.simples.etapas_contadas} etapas na lista.</p><code>Tempo O(n) · memória O(n)</code><p>Dupla: ${result.recursao.dupla.bancadas_ocupadas} bancadas ocupadas.</p><code>Tempo O(B) · memória O(log B)</code></div>
      <div class="lab-result-box"><h3>Cópias de dados</h3><p>Rasa compartilha as etapas: <strong>${result.copias.rasa_compartilha_lista_interna ? "sim" : "não"}</strong>.</p><p>Profunda compartilha as etapas: <strong>${result.copias.profunda_compartilha_lista_interna ? "sim" : "não"}</strong>.</p><p>Ordem original preservada: <strong>${result.copias.ordem_real_preservada ? "sim" : "não"}</strong>.</p></div>
      <div class="lab-result-box"><h3>Comparações na busca</h3><div class="comparison-row"><span>Melhor caso</span><strong>${result.busca.melhor_caso.comparacoes} · O(1)</strong></div><div class="comparison-row"><span>Caso médio</span><strong>${new Intl.NumberFormat("pt-BR").format(result.busca.caso_medio.comparacoes)} · O(n)</strong></div><div class="comparison-row"><span>Pior caso</span><strong>${result.busca.pior_caso.comparacoes} · O(n)</strong></div></div></div>
      <p class="lab-footnote">Ordem ${escape(result.id)}. A média considera busca bem-sucedida com posições equiprováveis. A demonstração de cópias não altera o cadastro. O experimento executa n buscas; o custo total do experimento é O(n²).</p>`;
  }

  function renderView({ animate = false } = {}) {
    const renders = {
      painel: renderDashboard,
      ordens: () => heading("Cada reparo, bem acompanhado.", "Cadastre, encontre e acompanhe os equipamentos da sua oficina.", { eyebrow: "ORDENS DE SERVIÇO" }) + orderPanel(),
      revisoes: renderReviews, relatorios: renderReports, laboratorio: renderLab
    };
    $("#main-content").innerHTML = `<div class="${animate ? "view-enter" : ""}">${renders[state.view]()}</div>`;
    $("#breadcrumb-current").textContent = VIEWS[state.view];
    document.title = VIEWS[state.view] + " — TecnoReparo";
    $("#nav-orders").textContent = state.orders.length;
    $("#nav-reviews").textContent = state.workshop.revisoes.length;
    $("#nav-reviews").hidden = !state.workshop.revisoes.length;
    $$(".nav-link").forEach((link) => {
      const active = link.dataset.view === state.view;
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
    syncWriteButtons();
  }
  function syncWriteButtons() {
    $$("[data-mutate]").forEach((button) => {
      button.disabled = state.busy || state.refreshing || !state.online || button.dataset.blocked === "true";
    });
  }
  function setConnection(online, error = "") {
    state.online = online;
    const status = $("#connection-state");
    status.classList.toggle("offline", !online);
    status.lastElementChild.textContent = online ? "Conectado" : "Sem conexão";
    $("#connection-banner").hidden = online;
    if (!online) $("#connection-message").textContent = error + (state.loaded ? " Os últimos dados recebidos continuam visíveis." : "");
    syncWriteButtons();
  }
  async function loadData() {
    try {
      const [orders, workshop, report] = await Promise.all([
        api.request("/api/ordens"), api.request("/api/estado"), api.request("/api/relatorio")
      ]);
      state.orders = orders;
      state.workshop = workshop;
      state.report = report;
      const firstLoad = !state.loaded;
      state.loaded = true;
      if (!state.labOrder || !getOrder(state.labOrder)) state.labOrder = orders[0]?.id || "";
      setConnection(true);
      renderView({ animate: firstLoad });
      if ($("#order-drawer").open) renderDrawer();
      $("#last-updated").textContent = "Atualizado às " + new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(new Date());
    } catch (error) {
      setConnection(false, error.message);
      if (!state.loaded) {
        $("#main-content").innerHTML = heading("Vamos conectar sua oficina.", "Inicie o servidor para acompanhar os atendimentos.", { create: false }) +
          `<section class="panel">${empty("Não foi possível carregar os dados", location.protocol === "file:" ? "Abra o sistema pelo endereço mostrado no terminal, após executar python main.py --demo." : "Verifique se o servidor Python continua em execução e clique em Tentar novamente.")}</section>`;
      }
      throw error;
    }
  }
  async function refresh(button) {
    if (state.refreshing || state.busy) return;
    state.refreshing = true;
    syncWriteButtons();
    if (button) { button.disabled = true; button.classList.add("is-loading"); }
    try { await loadData(); }
    catch (error) { toast(error.message, true); }
    finally {
      state.refreshing = false;
      syncWriteButtons();
      if (button) { button.disabled = false; button.classList.remove("is-loading"); }
    }
  }
  async function mutate(button, operation, message, errorTarget) {
    if (state.busy || state.refreshing) return null;
    state.busy = true;
    syncWriteButtons();
    if (button) { button.classList.add("is-loading"); button.setAttribute("aria-busy", "true"); }
    if (errorTarget) { $(errorTarget).hidden = true; $(errorTarget).textContent = ""; }
    let result;
    try {
      result = await operation();
    } catch (error) {
      if (errorTarget) { $(errorTarget).textContent = error.message; $(errorTarget).hidden = false; }
      if ($("#order-drawer").open) renderDrawer();
      toast(error.message, true);
      return null;
    } finally {
      if (result === undefined) {
        state.busy = false;
        syncWriteButtons();
        if (button) { button.classList.remove("is-loading"); button.removeAttribute("aria-busy"); }
      }
    }
    try {
      await loadData();
      toast(message);
    } catch (error) {
      // A escrita já foi confirmada: não repete o POST nem informa falha de gravação.
      if (result && result.id && result.equipamento) {
        const index = state.orders.findIndex((order) => order.id === result.id);
        if (index < 0) state.orders.push(result); else state.orders[index] = result;
      }
      toast("A ação foi salva. Atualize a tela para buscar os dados mais recentes.", true);
    } finally {
      state.busy = false;
      syncWriteButtons();
      if (button) { button.classList.remove("is-loading"); button.removeAttribute("aria-busy"); }
    }
    return result;
  }

  function openDialog(dialog) {
    dialog.classList.remove("is-closing");
    if (!dialog.open) dialog.showModal();
    document.body.classList.add("modal-open");
  }
  async function closeDialog(dialog) {
    if (!dialog || !dialog.open || dialog.classList.contains("is-closing")) return;
    dialog.classList.add("is-closing");
    await delay(reducedMotion() ? 0 : 180);
    dialog.close();
    dialog.classList.remove("is-closing");
    document.body.classList.toggle("modal-open", $$("dialog[open]").length > 0);
  }
  function toast(message, error = false) {
    const region = $("#toasts");
    const element = document.createElement("div");
    element.className = "toast" + (error ? " error" : "");
    element.setAttribute("role", error ? "alert" : "status");
    element.innerHTML = `${icon(error ? "alert" : "check-circle")}<p>${escape(message)}</p><button class="icon-button" aria-label="Fechar notificação">${icon("x")}</button>`;
    const remove = async () => {
      if (!element.isConnected || element.classList.contains("out")) return;
      element.classList.add("out");
      await delay(reducedMotion() ? 0 : 200);
      element.remove();
      if (!region.children.length && typeof region.hidePopover === "function" && region.matches(":popover-open")) region.hidePopover();
    };
    $("button", element).addEventListener("click", remove);
    region.append(element);
    if (typeof region.showPopover === "function") {
      region.setAttribute("popover", "manual");
      if (!region.matches(":popover-open")) region.showPopover();
    }
    if (region.children.length > 3) region.firstElementChild.remove();
    setTimeout(remove, error ? 7500 : 4800);
  }
  function confirmAction(title, message) {
    return new Promise((resolve) => {
      state.confirmation = resolve;
      $("#confirm-title").textContent = title;
      $("#confirm-message").textContent = message;
      openDialog($("#confirm-dialog"));
    });
  }
  async function resolveConfirmation(answer) {
    const resolve = state.confirmation;
    state.confirmation = null;
    await closeDialog($("#confirm-dialog"));
    if (resolve) resolve(answer);
  }
  function newOrder() {
    $("#new-order-form").reset();
    $("#new-order-error").hidden = true;
    openDialog($("#new-order-dialog"));
  }
  function openOrder(id) {
    if (!getOrder(id)) return;
    if (state.selectedId !== id) {
      state.drawerTab = "reparo";
      state.stepDraft = "";
      state.partDraft = "";
    }
    state.selectedId = id;
    renderDrawer();
    openDialog($("#order-drawer"));
  }
  function renderDrawer() {
    const order = getOrder(state.selectedId);
    if (!order) return;
    const editable = order.status === "em_reparo";
    const done = order.etapas.filter((step) => step.concluida).length;
    const total = order.etapas.length;
    const pieces = order.pecas_do_topo_para_base;
    const canFinish = editable && done === total && !pieces.length;
    const info = `<div class="order-summary"><span class="device-symbol">${icon(deviceIcon(order))}</span><div><h3>${escape(order.equipamento.tipo)}</h3><p>Nº de série: ${escape(order.equipamento.numero_serie)}</p></div></div>
      <div class="detail-grid"><div class="detail-item"><small>Cliente</small><p>${escape(order.cliente.nome)}</p></div><div class="detail-item"><small>Contato</small><p>${escape(order.cliente.contato)}</p></div></div>
      <div class="defect-note"><strong>DEFEITO INFORMADO</strong>${escape(order.equipamento.defeito)}${order.sintomas.length ? `<div class="symptom-list">${order.sintomas.map((symptom) => `<span>${escape(symptom)}</span>`).join("")}</div>` : ""}</div>`;
    const repair = `<section class="repair-section"><div class="section-title"><h3>Etapas do reparo</h3><small>${done} de ${total} concluídas</small></div>
      <div class="repair-progress" role="progressbar" aria-label="Etapas concluídas" aria-valuenow="${done}" aria-valuemin="0" aria-valuemax="${total}"><span style="width:${total ? done / total * 100 : 0}%"></span></div>
      <ul class="step-list">${order.etapas.map((step) => `<li class="step-item ${step.concluida ? "done" : ""}"><label class="step-label"><input type="checkbox" data-action="toggle-step" data-step="${step.id}" ${step.concluida ? "checked" : ""} ${writable(!editable)}><span>${escape(step.descricao)}</span></label>
      ${editable ? `<button class="icon-button" data-action="delete-step" data-step="${step.id}" aria-label="Remover etapa ${escape(step.descricao)}" ${writable(total <= 1)}>${icon("trash")}</button>` : ""}</li>`).join("")}</ul>
      ${editable ? `<form class="inline-form" id="step-form"><label class="sr-only" for="step-input">Nova etapa do reparo</label><input id="step-input" value="${escape(state.stepDraft)}" maxlength="200" placeholder="Adicionar uma etapa…" required><button class="button button-secondary" type="submit" aria-label="Adicionar etapa" ${writable(total >= 200)}>${icon("plus")}</button></form>` : ""}</section>
      <section class="repair-section"><div class="section-title"><h3>Peças retiradas</h3><small>${pieces.length} ${pieces.length === 1 ? "peça" : "peças"}</small></div>
      ${pieces.length ? `<div class="parts-list">${pieces.map((piece, index) => `<div class="part-row">${icon("package")}<strong>${escape(piece)}</strong>${index === 0 ? "<small>Recolocar primeiro</small>" : ""}</div>`).join("")}</div>` :
      `<p class="parts-empty">${icon("check-circle")}Nenhuma peça fora do equipamento.</p>`}
      ${editable ? `<div class="part-actions"><button class="button button-soft button-full" data-action="replace-part" ${writable(!pieces.length)}>${icon("arrow-down")}Recolocar última peça</button><form id="part-form" class="inline-form"><label class="sr-only" for="part-input">Peça a retirar</label><input id="part-input" value="${escape(state.partDraft)}" maxlength="100" placeholder="Nome da peça a retirar" required><button type="submit" class="button button-secondary" ${writable()}>Retirar</button></form></div>` : ""}</section>`;
    const history = `<ol class="timeline">${[...order.historico].reverse().map((event) => `<li>${escape(event)}</li>`).join("")}</ol>`;
    let footer = "";
    if (editable) {
      const reason = pieces.length ? "Recoloque todas as peças antes de finalizar." : done !== total ? "Conclua todas as etapas para liberar o equipamento." : "Tudo certo. A bancada será liberada.";
      footer = `<button class="button button-primary button-full" data-action="finish-order" ${writable(!canFinish)}>${icon("check-circle")}Concluir atendimento</button><p class="helper-text">${reason}</p>`;
    } else if (order.status === "concluida") {
      footer = `<button class="button button-secondary button-full" data-action="open-review">${icon("repeat")}Solicitar revisão</button>`;
    } else {
      footer = `<p class="helper-text">${order.status === "aguardando_revisao" ? "Este equipamento está na espera de revisões." : "O atendimento seguirá a ordem da fila de espera."}</p>`;
    }
    const drawerContent = $("#drawer-content");
    const previousScroll = $("#order-drawer").scrollTop;
    drawerContent.innerHTML = `<header class="drawer-header"><div><h2 id="drawer-title">${escape(order.id)}</h2>${badge(order.status)}</div><button class="icon-button" data-action="close-dialog" aria-label="Fechar detalhes">${icon("x")}</button></header>
      <div class="drawer-body">${info}<div class="drawer-tabs" aria-label="Conteúdo da ordem"><button class="drawer-tab ${state.drawerTab === "reparo" ? "active" : ""}" data-action="drawer-tab" data-tab="reparo" aria-pressed="${state.drawerTab === "reparo"}">Acompanhamento</button><button class="drawer-tab ${state.drawerTab === "historico" ? "active" : ""}" data-action="drawer-tab" data-tab="historico" aria-pressed="${state.drawerTab === "historico"}">Histórico</button></div>${state.drawerTab === "reparo" ? repair : history}</div>
      <footer class="drawer-action-bar">${footer}</footer>`;
    $("#order-drawer").scrollTop = previousScroll;
    syncWriteButtons();
  }

  // Um único manipulador mantém o funcionamento mesmo após atualizar as telas.
  document.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-action]");
    if (!button || button.disabled || button.tagName === "INPUT") return;
    const action = button.dataset.action;
    if (action === "new-order") newOrder();
    else if (action === "close-dialog") await closeDialog(button.closest("dialog"));
    else if (action === "refresh") await refresh(button);
    else if (action === "open-order") openOrder(button.dataset.id);
    else if (action === "filter") { state.filter = button.dataset.filter; renderView(); }
    else if (action === "drawer-tab") { state.drawerTab = button.dataset.tab; renderDrawer(); }
    else if (action === "session-info") toast("Os dados ficam nesta sessão. Ao encerrar o servidor Python, os cadastros são reiniciados.");
    else if (action === "confirm-no") await resolveConfirmation(false);
    else if (action === "confirm-yes") await resolveConfirmation(true);
    else if (action === "attend") {
      const order = await mutate(button, () => api.request("/api/atendimentos", { method: "POST", data: { origem: button.dataset.origin } }), "Atendimento iniciado. Hora de cuidar do equipamento.");
      if (order) openOrder(order.id);
    } else if (action === "replace-part") {
      const id = state.selectedId;
      await mutate(button, () => api.request("/api/ordens/" + id + "/pecas/recolocar", { method: "POST", data: {} }), "Peça recolocada no equipamento.");
    } else if (action === "finish-order") {
      const id = state.selectedId;
      await mutate(button, () => api.request("/api/ordens/" + id + "/concluir", { method: "POST", data: {} }), "Atendimento concluído. A bancada está disponível.");
    } else if (action === "delete-step") {
      const id = state.selectedId;
      const step = Number(button.dataset.step);
      if (await confirmAction("Remover esta etapa?", "A etapa será retirada do reparo. A remoção ficará registrada no histórico.")) {
        await mutate(button, () => api.request("/api/ordens/" + id + "/etapas/" + step, { method: "DELETE" }), "Etapa removida do reparo.");
      }
    } else if (action === "open-review") {
      const order = getOrder(state.selectedId);
      state.reviewId = order.id;
      $("#review-form").reset();
      $("#review-error").hidden = true;
      $("#review-order-label").textContent = order.id + " · " + order.cliente.nome;
      openDialog($("#review-dialog"));
    } else if (action === "cancel-review") {
      const side = button.dataset.side;
      if (await confirmAction("Cancelar solicitação de revisão?", "A revisão no " + (side === "inicio" ? "início" : "fim") + " da espera será cancelada. A ordem voltará à situação concluída.")) {
        await mutate(button, () => api.request("/api/revisoes/cancelar", { method: "POST", data: { extremidade: side } }), "Solicitação de revisão cancelada.");
      }
    }
  });
  document.addEventListener("input", (event) => {
    if (event.target.id === "order-search") {
      state.query = event.target.value;
      $("#orders-result").innerHTML = tableContent(state.view === "painel");
      $("#result-count").textContent = filteredOrders().length + " ordens";
    } else if (event.target.id === "step-input") state.stepDraft = event.target.value;
    else if (event.target.id === "part-input") state.partDraft = event.target.value;
  });
  document.addEventListener("change", async (event) => {
    if (event.target.dataset.action === "toggle-step") {
      const checkbox = event.target;
      const id = state.selectedId;
      const checked = checkbox.checked;
      const focused = document.activeElement === checkbox;
      await mutate(checkbox, () => api.request("/api/ordens/" + id + "/etapas/" + checkbox.dataset.step, { method: "PATCH", data: { concluida: checked } }), checked ? "Etapa concluída." : "Etapa marcada como pendente.");
      if (focused && $("#order-drawer").open && !document.activeElement.closest("button, input, textarea, select, a")) {
        $('#order-drawer [data-action="toggle-step"][data-step="' + checkbox.dataset.step + '"]')?.focus({ preventScroll: true });
      }
    } else if (event.target.id === "lab-order") {
      state.labOrder = event.target.value;
      state.labResult = null;
      $("#lab-result").innerHTML = "";
    }
  });
  document.addEventListener("submit", async (event) => {
    const form = event.target;
    if (!["new-order-form", "review-form", "step-form", "part-form", "lab-form"].includes(form.id)) return;
    event.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    if (form.id === "new-order-form") {
      const data = Object.fromEntries(new FormData(form));
      data.sintomas = data.sintomas.split(",").map((text) => text.trim()).filter(Boolean);
      const order = await mutate(submit, () => api.request("/api/ordens", { method: "POST", data }), "Ordem criada e adicionada à fila de espera.", "#new-order-error");
      if (order) { await closeDialog($("#new-order-dialog")); openOrder(order.id); }
    } else if (form.id === "review-form") {
      const values = new FormData(form);
      const result = await mutate(submit, () => api.request("/api/ordens/" + state.reviewId + "/revisoes", {
        method: "POST", data: { motivo: values.get("motivo"), urgente: values.has("urgente") }
      }), "Revisão adicionada à espera.", "#review-error");
      if (result) await closeDialog($("#review-dialog"));
    } else if (form.id === "step-form") {
      const id = state.selectedId;
      const text = $("#step-input").value;
      const result = await mutate(submit, () => api.request("/api/ordens/" + id + "/etapas", { method: "POST", data: { descricao: text } }), "Nova etapa adicionada ao reparo.");
      if (result) { state.stepDraft = ""; renderDrawer(); if ($("#order-drawer").open) $("#step-input")?.focus({ preventScroll: true }); }
    } else if (form.id === "part-form") {
      const id = state.selectedId;
      const text = $("#part-input").value;
      const result = await mutate(submit, () => api.request("/api/ordens/" + id + "/pecas/retirar", { method: "POST", data: { peca: text } }), "Peça registrada. Ela será a próxima a ser recolocada.");
      if (result) { state.partDraft = ""; renderDrawer(); if ($("#order-drawer").open) $("#part-input")?.focus({ preventScroll: true }); }
    } else if (form.id === "lab-form") {
      const id = $("#lab-order").value;
      const size = Number($("#lab-size").value);
      if (!id) return;
      state.labOrder = id;
      state.labSize = size;
      submit.disabled = true;
      submit.classList.add("is-loading");
      try {
        const [recursao, copias, busca] = await Promise.all([
          api.request("/api/ordens/" + id + "/recursao"),
          api.request("/api/ordens/" + id + "/copias"),
          api.request("/api/analises/busca?tamanho=" + size)
        ]);
        if (state.labOrder === id) {
          state.labResult = { id, recursao, copias, busca };
          if ($("#lab-result")) $("#lab-result").innerHTML = labResults();
        }
      } catch (error) { toast(error.message, true); }
      finally { submit.disabled = false; submit.classList.remove("is-loading"); }
    }
  });

  $$("dialog").forEach((dialog) => {
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      if (dialog.id === "confirm-dialog") resolveConfirmation(false);
      else closeDialog(dialog);
    });
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const box = dialog.getBoundingClientRect();
      const outside = event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom;
      if (outside) {
        if (dialog.id === "confirm-dialog") resolveConfirmation(false);
        else closeDialog(dialog);
      }
    });
    dialog.addEventListener("close", () => document.body.classList.toggle("modal-open", $$("dialog[open]").length > 0));
  });
  window.addEventListener("hashchange", () => {
    const view = location.hash.slice(1);
    if (!VIEWS[view]) return;
    state.view = view;
    state.query = "";
    state.filter = "todos";
    if (state.loaded) renderView({ animate: true });
    window.scrollTo({ top: 0, behavior: "instant" });
  });

  function ripple(button, x, y) {
    if (reducedMotion() || button.disabled) return;
    const box = button.getBoundingClientRect();
    const size = Math.max(box.width, box.height) * 2;
    const wave = document.createElement("span");
    wave.className = "click-ripple";
    wave.setAttribute("aria-hidden", "true");
    wave.style.width = wave.style.height = size + "px";
    wave.style.left = (x ?? box.width / 2) - size / 2 + "px";
    wave.style.top = (y ?? box.height / 2) - size / 2 + "px";
    button.append(wave);
    wave.addEventListener("animationend", () => wave.remove(), { once: true });
    setTimeout(() => wave.remove(), 900);
  }
  document.addEventListener("pointerdown", (event) => {
    const button = event.target.closest(".button, .icon-button, .filter-tab");
    if (!button) return;
    const box = button.getBoundingClientRect();
    ripple(button, event.clientX - box.left, event.clientY - box.top);
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest(".button, .icon-button, .filter-tab");
    if (button && event.detail === 0) ripple(button);
  });

  async function start() {
    try { await Promise.all([loadData(), delay(reducedMotion() ? 0 : 420)]); }
    catch (_) { /* O erro e a opção de tentar novamente ficam visíveis na página. */ }
    finally {
      $("#boot-loader").classList.add("is-leaving");
      await delay(reducedMotion() ? 0 : 300);
      $("#boot-loader").hidden = true;
    }
  }
  start();
})();
