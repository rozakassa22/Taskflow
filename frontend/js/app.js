/* Main UI controller — view switching, auth, boards list, and board view. */
(function () {
  const $ = (id) => document.getElementById(id);

  let currentBoardId = null;
  let activeAuthTab = "login";

  // ---------- View routing ----------

  function showView(name) {
    for (const v of document.querySelectorAll(".view")) v.classList.add("hidden");
    $(`view-${name}`).classList.remove("hidden");
    $("navbar").classList.toggle("hidden", name === "auth");
  }

  function start() {
    if (api.getToken()) {
      $("user-email").textContent = api.getEmail() || "";
      goBoards();
    } else {
      showView("auth");
    }
  }

  // ---------- Auth ----------

  function setAuthTab(tab) {
    activeAuthTab = tab;
    for (const t of document.querySelectorAll(".tab"))
      t.classList.toggle("active", t.dataset.tab === tab);
    $("auth-submit").textContent = tab === "login" ? "Sign in" : "Create account";
  }

  async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = $("auth-email").value.trim();
    const password = $("auth-password").value;
    const errBox = $("auth-error");
    errBox.classList.add("hidden");
    const submit = $("auth-submit");
    submit.disabled = true;

    try {
      if (activeAuthTab === "register") {
        await api.register(email, password);
      }
      await api.login(email, password);
      $("user-email").textContent = email;
      goBoards();
    } catch (err) {
      errBox.textContent = err.message;
      errBox.classList.remove("hidden");
    } finally {
      submit.disabled = false;
    }
  }

  function handleLogout() {
    api.clearSession();
    start();
  }

  // ---------- Boards list ----------

  async function goBoards() {
    showView("boards");
    const grid = $("boards-grid");
    grid.innerHTML = "";
    let boards = [];
    try {
      boards = await api.listBoards();
    } catch (err) {
      if (/401|invalid/i.test(err.message)) {
        handleLogout();
        return;
      }
      throw err;
    }
    $("boards-empty").classList.toggle("hidden", boards.length > 0);
    for (const b of boards) {
      const div = document.createElement("div");
      div.className = "board-card";
      div.innerHTML = `
        <h3>${escapeHtml(b.name)}</h3>
        <div class="meta">${b.columns.length} columns · ${countCards(b)} cards</div>
      `;
      div.addEventListener("click", () => goBoard(b.id));
      grid.appendChild(div);
    }
  }

  function countCards(board) {
    return board.columns.reduce((sum, c) => sum + (c.cards ? c.cards.length : 0), 0);
  }

  // ---------- Single board ----------

  async function goBoard(id) {
    currentBoardId = id;
    showView("board");
    await refreshBoard();
  }

  async function refreshBoard() {
    const board = await api.getBoard(currentBoardId);
    $("board-title").textContent = board.name;
    renderColumns(board.columns);
  }

  function renderColumns(columns) {
    const container = $("columns");
    container.innerHTML = "";
    for (const col of columns) container.appendChild(renderColumn(col));
  }

  function renderColumn(column) {
    const node = document.createElement("section");
    node.className = "column";
    node.dataset.columnId = column.id;
    node.innerHTML = `
      <div class="column-header">
        <h3>${escapeHtml(column.name)}</h3>
        <span class="column-count">${column.cards.length}</span>
      </div>
      <div class="cards-list" data-column-id="${column.id}"></div>
      <button class="add-card-btn">+ Add card</button>
    `;

    const list = node.querySelector(".cards-list");
    for (const card of column.cards) list.appendChild(renderCard(card));

    node.querySelector(".add-card-btn").addEventListener("click", () => openCardModal(column.id));

    Sortable.create(list, {
      group: "cards",
      animation: 150,
      ghostClass: "sortable-ghost",
      chosenClass: "sortable-chosen",
      onEnd: handleCardDrop,
    });

    return node;
  }

  function renderCard(card) {
    const div = document.createElement("div");
    div.className = "card";
    div.dataset.cardId = card.id;
    div.innerHTML = `
      <button class="card-delete" title="Delete">✕</button>
      <div class="card-title">${escapeHtml(card.title)}</div>
      <div class="card-meta">
        <span class="priority-dot priority-${card.priority}"></span>
        <span>${card.priority}</span>
      </div>
    `;
    div.querySelector(".card-delete").addEventListener("click", async (e) => {
      e.stopPropagation();
      await api.deleteCard(card.id);
      refreshBoard();
    });
    return div;
  }

  async function handleCardDrop(evt) {
    const cardId = parseInt(evt.item.dataset.cardId, 10);
    const targetColumnId = parseInt(evt.to.dataset.columnId, 10);
    const newIndex = evt.newIndex;
    try {
      await api.moveCard(cardId, targetColumnId, newIndex);
    } catch (err) {
      alert(`Move failed: ${err.message}`);
    } finally {
      refreshBoard();
    }
  }

  // ---------- Modals ----------

  function openBoardModal() {
    $("modal-board").classList.remove("hidden");
    $("new-board-name").value = "";
    $("new-board-name").focus();
  }

  async function handleNewBoard(e) {
    e.preventDefault();
    const name = $("new-board-name").value.trim();
    if (!name) return;
    await api.createBoard(name);
    closeModals();
    goBoards();
  }

  let cardModalColumnId = null;
  function openCardModal(columnId) {
    cardModalColumnId = columnId;
    $("modal-card").classList.remove("hidden");
    $("new-card-title").value = "";
    $("new-card-description").value = "";
    $("new-card-priority").value = "normal";
    $("new-card-title").focus();
  }

  async function handleNewCard(e) {
    e.preventDefault();
    const payload = {
      title: $("new-card-title").value.trim(),
      description: $("new-card-description").value.trim() || null,
      priority: $("new-card-priority").value,
    };
    if (!payload.title) return;
    await api.createCard(cardModalColumnId, payload);
    closeModals();
    refreshBoard();
  }

  function closeModals() {
    for (const m of document.querySelectorAll(".modal")) m.classList.add("hidden");
  }

  async function handleDeleteBoard() {
    if (!currentBoardId) return;
    if (!confirm("Delete this board and all its cards?")) return;
    await api.deleteBoard(currentBoardId);
    currentBoardId = null;
    goBoards();
  }

  // ---------- Utilities ----------

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  // ---------- Wire-up ----------

  function init() {
    for (const t of document.querySelectorAll(".tab"))
      t.addEventListener("click", () => setAuthTab(t.dataset.tab));
    $("auth-form").addEventListener("submit", handleAuthSubmit);
    $("logout-btn").addEventListener("click", handleLogout);
    $("new-board-btn").addEventListener("click", openBoardModal);
    $("new-board-form").addEventListener("submit", handleNewBoard);
    $("new-card-form").addEventListener("submit", handleNewCard);
    $("back-btn").addEventListener("click", goBoards);
    $("delete-board-btn").addEventListener("click", handleDeleteBoard);
    for (const b of document.querySelectorAll("[data-close]"))
      b.addEventListener("click", closeModals);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") closeModals();
    });
    start();
  }

  document.addEventListener("DOMContentLoaded", init);
})();
