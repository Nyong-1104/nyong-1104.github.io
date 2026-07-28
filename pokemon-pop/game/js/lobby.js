(function (global) {
  const menuEl = document.getElementById("menu-overlay");
  const lobbyEl = document.getElementById("lobby-overlay");
  const historyEl = document.getElementById("history-overlay");
  const seatGrid = document.getElementById("lobby-seats");
  const codeLabel = document.getElementById("lobby-code");
  const lobbyStatus = document.getElementById("lobby-status");
  const btnReady = document.getElementById("lobby-ready");
  const btnStart = document.getElementById("lobby-start");
  const btnLeave = document.getElementById("lobby-leave");
  const joinCode = document.getElementById("join-code");
  const menuError = document.getElementById("menu-error");
  const authPanel = document.getElementById("auth-panel");
  const playPanel = document.getElementById("play-panel");
  const authNick = document.getElementById("auth-nick");
  const authPass = document.getElementById("auth-pass");
  const accountNick = document.getElementById("account-nick");
  const accountStats = document.getElementById("account-stats");
  const historySummary = document.getElementById("history-summary");
  const historyList = document.getElementById("history-list");

  let roomState = null;
  let myId = null;
  let myReady = false;

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function currentNick() {
    const s = window.BnbAccount.getSession();
    return s ? s.nickname : "";
  }

  function refreshAuthUI() {
    const session = window.BnbAccount.getSession();
    if (!session) {
      authPanel.hidden = false;
      playPanel.hidden = true;
      return;
    }
    authPanel.hidden = true;
    playPanel.hidden = false;
    accountNick.textContent = session.nickname;
    const st = session.stats || {};
    accountStats.textContent = `전적 ${st.wins || 0}승 ${st.losses || 0}패 · 킬 ${st.kills || 0} · 점수합 ${st.score || 0}`;
    window.BnbRanking.setNickname(session.nickname);
  }

  function refreshWsStatus() {
    const el = document.getElementById("ws-status");
    if (!el) return;
    const url = window.BnbConfig.WS_URL || "(없음)";
    el.textContent = `멀티 서버: ${url}`;
    window.BnbNet.connect()
      .then(() => {
        el.textContent = `멀티 서버 연결됨: ${url}`;
        el.style.color = "#9dffa8";
      })
      .catch(() => {
        el.textContent = `멀티 서버 연결 실패: ${url} (서버 실행/?ws= 확인)`;
        el.style.color = "#ffb4b4";
      });
  }

  function showMenu() {
    menuEl.hidden = false;
    lobbyEl.hidden = true;
    if (historyEl) historyEl.hidden = true;
    menuError.textContent = "";
    refreshAuthUI();
    refreshWsStatus();
  }

  function showLobby() {
    menuEl.hidden = true;
    lobbyEl.hidden = false;
  }

  function hideAll() {
    menuEl.hidden = true;
    lobbyEl.hidden = true;
  }

  function requireLogin() {
    const s = window.BnbAccount.getSession();
    if (!s) {
      menuError.textContent = "먼저 로그인 / 계정 등록을 해주세요.";
      return null;
    }
    return s;
  }

  function renderLobby(state) {
    roomState = state;
    if (!state) return;
    codeLabel.textContent = state.code;
    const sock = window.BnbNet.getSocket();
    myId = sock ? sock.id : myId;

    const seats = state.seats || [];
    seatGrid.innerHTML = seats
      .map((p, i) => {
        if (!p) {
          return `<div class="seat seat--empty"><span class="seat__num">${i + 1}</span><span>빈자리</span></div>`;
        }
        const me = p.id === myId ? " seat--me" : "";
        const ready = p.ready ? " seat--ready" : "";
        const host = p.isHost ? " · 방장" : "";
        return `<div class="seat${me}${ready}">
          <span class="seat__num">${i + 1}</span>
          <span class="seat__name">${escapeHtml(p.name)}${host}</span>
          <span class="seat__ready">${p.ready ? "READY" : "…"}</span>
        </div>`;
      })
      .join("");

    const meSeat = seats.find((p) => p && p.id === myId);
    myReady = Boolean(meSeat && meSeat.ready);
    btnReady.textContent = myReady ? "레디 취소" : "레디";
    btnStart.hidden = !(meSeat && meSeat.isHost);
    const filled = seats.filter(Boolean).length;
    const readyCount = seats.filter((p) => p && p.ready).length;
    lobbyStatus.textContent = `${filled}/8 · 레디 ${readyCount} · ${state.phase}`;
  }

  async function create() {
    menuError.textContent = "";
    const s = requireLogin();
    if (!s) return;
    try {
      const res = await window.BnbNet.createRoom(s.nickname);
      if (!res.ok) throw new Error(res.error || "방 생성 실패");
      showLobby();
      renderLobby(res.state);
    } catch (e) {
      menuError.textContent = e.message || String(e);
    }
  }

  async function join() {
    menuError.textContent = "";
    const s = requireLogin();
    if (!s) return;
    try {
      const res = await window.BnbNet.joinRoom(joinCode.value, s.nickname);
      if (!res.ok) throw new Error(res.error || "입장 실패");
      showLobby();
      renderLobby(res.state);
    } catch (e) {
      menuError.textContent = e.message || String(e);
    }
  }

  function renderHistory() {
    const s = window.BnbAccount.getSession();
    if (!s) return;
    const st = s.stats || {};
    historySummary.textContent = `${s.nickname} · ${st.wins || 0}승 ${st.losses || 0}패 · 킬 ${st.kills || 0}`;
    const hist = s.history || [];
    if (!hist.length) {
      historyList.innerHTML =
        "<li><span class='rank-pos'>-</span><span>아직 전적이 없어요</span><span></span></li>";
      return;
    }
    historyList.innerHTML = hist
      .map((h, i) => {
        const when = new Date(h.at).toLocaleString();
        return `<li>
          <span class="rank-pos">${i + 1}</span>
          <span>${h.won ? "승" : "패"} · 킬 ${h.kills || 0}</span>
          <span class="rank-score">${h.score || 0}</span>
          <span class="rank-meta">${when} · ${Math.floor(h.timeSec || 0)}초 · 봇 ${h.bots || 0}</span>
        </li>`;
      })
      .join("");
  }

  function bind() {
    document.getElementById("btn-login").addEventListener("click", async () => {
      menuError.textContent = "";
      const res = await window.BnbAccount.login(authNick.value, authPass.value);
      if (!res.ok) menuError.textContent = res.error;
      else {
        authPass.value = "";
        refreshAuthUI();
      }
    });

    document.getElementById("btn-register").addEventListener("click", async () => {
      menuError.textContent = "";
      const res = await window.BnbAccount.register(authNick.value, authPass.value);
      if (!res.ok) menuError.textContent = res.error;
      else {
        authPass.value = "";
        refreshAuthUI();
      }
    });

    document.getElementById("btn-logout").addEventListener("click", () => {
      window.BnbAccount.logout();
      refreshAuthUI();
    });

    document.getElementById("btn-history").addEventListener("click", () => {
      if (!requireLogin()) return;
      historyEl.hidden = false;
      renderHistory();
    });
    document.getElementById("history-close").addEventListener("click", () => {
      historyEl.hidden = true;
    });

    document.getElementById("btn-solo").addEventListener("click", () => {
      if (!requireLogin()) return;
      const bots = Number(document.getElementById("bot-count").value || 3);
      hideAll();
      window.BnbGame.startSolo(bots);
    });
    document.getElementById("btn-create").addEventListener("click", () => create());
    document.getElementById("btn-join").addEventListener("click", () => join());
    joinCode.addEventListener("keydown", (e) => {
      if (e.key === "Enter") join();
    });

    btnReady.addEventListener("click", async () => {
      const res = await window.BnbNet.setReady(!myReady);
      if (res.ok) renderLobby(res.state);
      else lobbyStatus.textContent = res.error || "레디 실패";
    });

    btnStart.addEventListener("click", async () => {
      const res = await window.BnbNet.startGame();
      if (!res.ok) lobbyStatus.textContent = res.error || "시작 실패";
    });

    btnLeave.addEventListener("click", async () => {
      await window.BnbNet.leaveRoom();
      roomState = null;
      showMenu();
      window.BnbGame.returnToMenu();
    });

    window.BnbNet.on("room:state", (state) => {
      renderLobby(state);
      if (state.phase === "lobby" && menuEl.hidden) {
        lobbyEl.hidden = false;
      }
    });

    window.BnbNet.on("game:start", (state) => {
      hideAll();
      window.BnbGame.startMulti(state);
    });

    window.BnbNet.on("game:end", (payload) => {
      window.BnbGame.onMultiEnd(payload || {});
    });

    showMenu();
  }

  global.BnbLobby = {
    bind,
    showMenu,
    showLobby,
    hideAll,
    renderLobby,
    getRoomState: () => roomState,
    currentNick,
  };
})(window);
