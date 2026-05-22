/* Tiny API client. Keeps the token in localStorage and attaches it to requests. */
(function () {
  const TOKEN_KEY = "taskflow:token";
  const EMAIL_KEY = "taskflow:email";

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setSession(token, email) {
    localStorage.setItem(TOKEN_KEY, token);
    if (email) localStorage.setItem(EMAIL_KEY, email);
  }

  function getEmail() {
    return localStorage.getItem(EMAIL_KEY);
  }

  function clearSession() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
  }

  async function request(method, path, body) {
    const headers = { "Content-Type": "application/json" };
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const opts = { method, headers };
    if (body !== undefined) opts.body = JSON.stringify(body);

    const resp = await fetch(path, opts);
    if (resp.status === 204) return null;

    let data = null;
    try {
      data = await resp.json();
    } catch (_) {
      data = null;
    }

    if (!resp.ok) {
      const msg = (data && data.detail) || resp.statusText || "request failed";
      throw new Error(msg);
    }
    return data;
  }

  window.api = {
    getToken,
    getEmail,
    setSession,
    clearSession,

    register: (email, password) =>
      request("POST", "/api/auth/register", { email, password }),

    login: async (email, password) => {
      const data = await request("POST", "/api/auth/login", { email, password });
      setSession(data.access_token, email);
      return data;
    },

    listBoards: () => request("GET", "/api/boards"),
    getBoard: (id) => request("GET", `/api/boards/${id}`),
    createBoard: (name) => request("POST", "/api/boards", { name }),
    deleteBoard: (id) => request("DELETE", `/api/boards/${id}`),

    createCard: (columnId, payload) =>
      request("POST", `/api/columns/${columnId}/cards`, payload),
    moveCard: (cardId, columnId, position) =>
      request("PATCH", `/api/cards/${cardId}/move`, { column_id: columnId, position }),
    deleteCard: (cardId) => request("DELETE", `/api/cards/${cardId}`),
  };
})();
