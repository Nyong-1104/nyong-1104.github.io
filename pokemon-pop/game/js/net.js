(function (global) {
  const cfg = global.BnbConfig;
  let socket = null;

  function connect() {
    if (socket && socket.connected) return Promise.resolve(socket);
    if (typeof io === "undefined") {
      return Promise.reject(new Error("socket.io 클라이언트가 없어요."));
    }
    return new Promise((resolve, reject) => {
      socket = io(cfg.WS_URL, {
        transports: ["websocket", "polling"],
        timeout: 8000,
      });
      const onErr = (err) => {
        cleanup();
        reject(err || new Error("서버에 연결할 수 없어요. WS_URL / 서버 실행을 확인하세요."));
      };
      function cleanup() {
        socket.off("connect", onOk);
        socket.off("connect_error", onErr);
      }
      function onOk() {
        cleanup();
        resolve(socket);
      }
      socket.once("connect", onOk);
      socket.once("connect_error", onErr);
    });
  }

  function getSocket() {
    return socket;
  }

  function emitAck(event, payload) {
    return connect().then(
      (s) =>
        new Promise((resolve) => {
          s.timeout(8000).emit(event, payload || {}, (err, res) => {
            if (err) resolve({ ok: false, error: "서버 응답 시간 초과" });
            else resolve(res || { ok: false, error: "빈 응답" });
          });
        })
    );
  }

  function createRoom(name) {
    return emitAck("room:create", { name });
  }

  function joinRoom(code, name) {
    return emitAck("room:join", { code, name });
  }

  function setReady(ready) {
    return emitAck("room:ready", { ready: Boolean(ready) });
  }

  function startGame() {
    return emitAck("room:start", {});
  }

  function leaveRoom() {
    return emitAck("room:leave", {});
  }

  function on(event, handler) {
    connect().then((s) => s.on(event, handler));
  }

  function off(event, handler) {
    if (socket) socket.off(event, handler);
  }

  function sendInput(input) {
    if (socket && socket.connected) socket.emit("game:input", input);
  }

  function sendState(snapshot) {
    if (socket && socket.connected) socket.emit("game:state", snapshot);
  }

  function sendEnd(payload) {
    if (socket && socket.connected) socket.emit("game:end", payload || {});
  }

  global.BnbNet = {
    connect,
    getSocket,
    createRoom,
    joinRoom,
    setReady,
    startGame,
    leaveRoom,
    on,
    off,
    sendInput,
    sendState,
    sendEnd,
  };
})(window);
