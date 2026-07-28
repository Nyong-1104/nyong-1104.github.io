/**
 * pokePOP minigame config — separate from card catalog / GemRate.
 *
 * Cross-device:
 * - HTTPS site → WS_URL must be https/wss
 * - Override: ?ws=https://game.nyong.app
 */
(function (global) {
  function fromQuery() {
    try {
      const q = new URLSearchParams(location.search).get("ws");
      return q ? String(q).trim() : "";
    } catch {
      return "";
    }
  }

  function fromStorage() {
    try {
      return (
        (localStorage.getItem("pokepop-game:ws_url") ||
          localStorage.getItem("pokepop-bnb:ws_url") ||
          "")
          .trim()
      );
    } catch {
      return "";
    }
  }

  const queryWs = fromQuery();
  if (queryWs) {
    try {
      localStorage.setItem("pokepop-game:ws_url", queryWs);
    } catch {
      /* ignore */
    }
  }

  global.BnbConfig = {
    API_BASE: "",
    WS_URL: queryWs || fromStorage() || "http://localhost:3100",
    AUTH_PROVIDER: "local",
    BOARD_ID: "patrit14-solo-kills",
    STORAGE_PREFIX: "pokepop-game:",
    MAX_LOCAL_ENTRIES: 20,
    NICK_KEY: "pokepop-game:nickname",
  };
})(window);
