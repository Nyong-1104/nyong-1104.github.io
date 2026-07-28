/**
 * pokePOP realtime server — keep separate from GemRate scrapers.
 * Default port 3100.
 */
const http = require("http");
const express = require("express");
const cors = require("cors");
const { Server } = require("socket.io");
const {
  normalizeCode,
  randomCode,
  createRoom,
  publicState,
  firstEmptySeat,
  seatOf,
  occupied,
  allReady,
  CODE_LEN,
  nickTakenInRoom,
} = require("./room");

const PORT = Number(process.env.POKEPOP_GAME_PORT || process.env.BNB_PORT || 3100);
const rooms = new Map(); // code -> room

const app = express();
app.use(cors());
app.get("/health", (_req, res) => {
  res.json({ ok: true, service: "pokepop-game", rooms: rooms.size });
});

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: true, methods: ["GET", "POST"] },
});

function emitRoom(room) {
  io.to(room.code).emit("room:state", publicState(room));
}

function leaveRoom(socket) {
  const code = socket.data.roomCode;
  if (!code) return;
  const room = rooms.get(code);
  socket.leave(code);
  socket.data.roomCode = null;
  if (!room) return;

  const seat = seatOf(room, socket.id);
  if (seat >= 0) room.seats[seat] = null;

  const left = occupied(room);
  if (!left.length) {
    rooms.delete(code);
    return;
  }

  if (room.hostId === socket.id) {
    room.hostId = left[0].id;
  }

  if (room.phase === "playing") {
    // Keep match going; host migration for snapshots handled client-side via new hostId.
  } else {
    left.forEach((p) => {
      p.ready = false;
    });
    room.phase = "lobby";
  }

  emitRoom(room);
}

function cleanName(name) {
  const n = String(name || "Guest").trim().slice(0, 12);
  return n || "Guest";
}

io.on("connection", (socket) => {
  socket.data.roomCode = null;

  socket.on("room:create", (payload, cb) => {
    try {
      leaveRoom(socket);
      let code = randomCode();
      while (rooms.has(code)) code = randomCode();

      const room = createRoom(socket.id, cleanName(payload && payload.name));
      room.code = code;
      room.seats[0] = {
        id: socket.id,
        name: cleanName(payload && payload.name),
        ready: false,
      };
      rooms.set(code, room);
      socket.join(code);
      socket.data.roomCode = code;
      const state = publicState(room);
      if (typeof cb === "function") cb({ ok: true, state });
      emitRoom(room);
    } catch (err) {
      if (typeof cb === "function") cb({ ok: false, error: String(err.message || err) });
    }
  });

  socket.on("room:join", (payload, cb) => {
    try {
      const code = normalizeCode(payload && payload.code);
      if (code.length !== CODE_LEN) {
        if (typeof cb === "function") cb({ ok: false, error: "방 코드는 4자리여야 해요." });
        return;
      }
      const room = rooms.get(code);
      if (!room) {
        if (typeof cb === "function") cb({ ok: false, error: "방을 찾을 수 없어요." });
        return;
      }
      if (room.phase !== "lobby") {
        if (typeof cb === "function") cb({ ok: false, error: "이미 게임이 시작됐어요." });
        return;
      }
      if (seatOf(room, socket.id) >= 0) {
        if (typeof cb === "function") cb({ ok: true, state: publicState(room) });
        return;
      }
      const seat = firstEmptySeat(room);
      if (seat < 0) {
        if (typeof cb === "function") cb({ ok: false, error: "방이 가득 찼어요 (최대 8명)." });
        return;
      }
      const joinName = cleanName(payload && payload.name);
      if (nickTakenInRoom(room, joinName, socket.id)) {
        if (typeof cb === "function") cb({ ok: false, error: "이미 같은 닉네임이 방에 있어요." });
        return;
      }

      leaveRoom(socket);
      room.seats[seat] = {
        id: socket.id,
        name: joinName,
        ready: false,
      };
      socket.join(code);
      socket.data.roomCode = code;
      const state = publicState(room);
      if (typeof cb === "function") cb({ ok: true, state });
      emitRoom(room);
    } catch (err) {
      if (typeof cb === "function") cb({ ok: false, error: String(err.message || err) });
    }
  });

  socket.on("room:ready", (payload, cb) => {
    const code = socket.data.roomCode;
    const room = code && rooms.get(code);
    if (!room || room.phase !== "lobby") {
      if (typeof cb === "function") cb({ ok: false, error: "로비가 아니에요." });
      return;
    }
    const seat = seatOf(room, socket.id);
    if (seat < 0) {
      if (typeof cb === "function") cb({ ok: false, error: "좌석이 없어요." });
      return;
    }
    room.seats[seat].ready = Boolean(payload && payload.ready);
    if (typeof cb === "function") cb({ ok: true, state: publicState(room) });
    emitRoom(room);
  });

  socket.on("room:start", (_payload, cb) => {
    const code = socket.data.roomCode;
    const room = code && rooms.get(code);
    if (!room) {
      if (typeof cb === "function") cb({ ok: false, error: "방이 없어요." });
      return;
    }
    if (socket.id !== room.hostId) {
      if (typeof cb === "function") cb({ ok: false, error: "방장만 시작할 수 있어요." });
      return;
    }
    if (!allReady(room)) {
      if (typeof cb === "function") {
        cb({ ok: false, error: "2명 이상, 전원 레디여야 시작해요." });
      }
      return;
    }
    room.phase = "playing";
    const state = publicState(room);
    if (typeof cb === "function") cb({ ok: true, state });
    io.to(code).emit("game:start", state);
    emitRoom(room);
  });

  socket.on("room:leave", (_payload, cb) => {
    leaveRoom(socket);
    if (typeof cb === "function") cb({ ok: true });
  });

  // Host-authority gameplay relay
  socket.on("game:input", (input) => {
    const code = socket.data.roomCode;
    const room = code && rooms.get(code);
    if (!room || room.phase !== "playing") return;
    const seat = seatOf(room, socket.id);
    if (seat < 0) return;
    // Forward to host (and ignore if sender is host — host reads local input)
    if (socket.id === room.hostId) return;
    io.to(room.hostId).emit("game:input", { seat, input, from: socket.id });
  });

  socket.on("game:state", (snapshot) => {
    const code = socket.data.roomCode;
    const room = code && rooms.get(code);
    if (!room || room.phase !== "playing") return;
    if (socket.id !== room.hostId) return;
    socket.to(code).emit("game:state", snapshot);
  });

  socket.on("game:end", (payload) => {
    const code = socket.data.roomCode;
    const room = code && rooms.get(code);
    if (!room || room.phase !== "playing") return;
    if (socket.id !== room.hostId) return;
    room.phase = "finished";
    occupied(room).forEach((p) => {
      p.ready = false;
    });
    io.to(code).emit("game:end", payload || {});
    // Return to lobby after a beat so clients can show results
    room.phase = "lobby";
    emitRoom(room);
  });

  socket.on("disconnect", () => {
    leaveRoom(socket);
  });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`[pokepop-game] listening on http://0.0.0.0:${PORT}`);
  console.log(`[pokepop-game] health: http://localhost:${PORT}/health`);
});
