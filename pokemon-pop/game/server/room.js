/**
 * pokePOP room helpers — room codes are always stored uppercase (case-insensitive).
 */
const MAX_SEATS = 8;
const CODE_LEN = 4;
const CHARSET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

/** Classic CA-style 8 spawn seats on 15×13. */
const SEAT_SPAWNS = [
  { x: 0, y: 0 },
  { x: 7, y: 0 },
  { x: 14, y: 0 },
  { x: 0, y: 6 },
  { x: 14, y: 6 },
  { x: 0, y: 12 },
  { x: 7, y: 12 },
  { x: 14, y: 12 },
];

function normalizeCode(code) {
  return String(code || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]/g, "")
    .slice(0, CODE_LEN);
}

function randomCode() {
  let out = "";
  for (let i = 0; i < CODE_LEN; i += 1) {
    out += CHARSET[(Math.random() * CHARSET.length) | 0];
  }
  return out;
}

function createRoom(hostSocketId, name) {
  return {
    code: "",
    hostId: hostSocketId,
    phase: "lobby", // lobby | playing | finished
    seats: Array.from({ length: MAX_SEATS }, () => null),
    createdAt: Date.now(),
  };
}

function publicState(room) {
  return {
    code: room.code,
    hostId: room.hostId,
    phase: room.phase,
    maxSeats: MAX_SEATS,
    seats: room.seats.map((p, seat) =>
      p
        ? {
            seat,
            id: p.id,
            name: p.name,
            ready: p.ready,
            isHost: p.id === room.hostId,
          }
        : null
    ),
    spawns: SEAT_SPAWNS,
  };
}

function firstEmptySeat(room) {
  for (let i = 0; i < MAX_SEATS; i += 1) {
    if (!room.seats[i]) return i;
  }
  return -1;
}

function seatOf(room, socketId) {
  return room.seats.findIndex((p) => p && p.id === socketId);
}

function occupied(room) {
  return room.seats.filter(Boolean);
}

function nickTakenInRoom(room, name, exceptId) {
  const key = String(name || "")
    .trim()
    .toLowerCase();
  return occupied(room).some(
    (p) => p.id !== exceptId && String(p.name || "").trim().toLowerCase() === key
  );
}

function allReady(room) {
  const players = occupied(room);
  return players.length >= 2 && players.every((p) => p.ready);
}

module.exports = {
  MAX_SEATS,
  CODE_LEN,
  SEAT_SPAWNS,
  normalizeCode,
  randomCode,
  createRoom,
  publicState,
  firstEmptySeat,
  seatOf,
  occupied,
  allReady,
  nickTakenInRoom,
};
