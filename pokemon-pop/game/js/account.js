/**
 * Local accounts + match history for pokePOP minigame.
 * Later: Google login (1 Google account → 1 game id) via Auth provider — keep separate from card site.
 */
(function (global) {
  const cfg = global.BnbConfig;
  const ACC_KEY = `${cfg.STORAGE_PREFIX}accounts`;
  const ACC_KEY_LEGACY = "pokepop-bnb:accounts";
  const SESSION_KEY = `${cfg.STORAGE_PREFIX}session`;
  const SESSION_KEY_LEGACY = "pokepop-bnb:session";
  const MAX_WEIGHT = 16; // 한글 8 = 영문/숫자 16
  const MAX_HISTORY = 40;

  function normalizeKey(nick) {
    return String(nick || "")
      .trim()
      .toLowerCase();
  }

  function charWeight(ch) {
    if (/[가-힣]/.test(ch)) return 2;
    if (/[A-Za-z0-9]/.test(ch)) return 1;
    return -1;
  }

  function validateNickname(raw) {
    const nick = String(raw || "").trim();
    if (!nick) return { ok: false, error: "닉네임을 입력하세요." };
    let weight = 0;
    for (const ch of nick) {
      const w = charWeight(ch);
      if (w < 0) {
        return { ok: false, error: "한글, 영문, 숫자만 사용할 수 있어요." };
      }
      weight += w;
      if (weight > MAX_WEIGHT) {
        return {
          ok: false,
          error: "너무 길어요. 한글 최대 8자 / 영문·숫자 최대 16자예요.",
        };
      }
    }
    return { ok: true, nick, weight };
  }

  function migrateLegacyIfNeeded() {
    try {
      if (!localStorage.getItem(ACC_KEY) && localStorage.getItem(ACC_KEY_LEGACY)) {
        localStorage.setItem(ACC_KEY, localStorage.getItem(ACC_KEY_LEGACY));
      }
      if (!localStorage.getItem(SESSION_KEY) && localStorage.getItem(SESSION_KEY_LEGACY)) {
        localStorage.setItem(SESSION_KEY, localStorage.getItem(SESSION_KEY_LEGACY));
      }
    } catch {
      /* ignore */
    }
  }

  function readAccounts() {
    migrateLegacyIfNeeded();
    try {
      const raw = localStorage.getItem(ACC_KEY);
      const list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch {
      return [];
    }
  }

  function writeAccounts(list) {
    localStorage.setItem(ACC_KEY, JSON.stringify(list));
  }

  function findByNick(nick) {
    const key = normalizeKey(nick);
    return readAccounts().find((a) => normalizeKey(a.nickname) === key) || null;
  }

  function isNicknameTaken(nick, exceptId) {
    const key = normalizeKey(nick);
    return readAccounts().some(
      (a) => normalizeKey(a.nickname) === key && a.id !== exceptId
    );
  }

  /** SHA-256 hex — works on http://LAN-IP too (crypto.subtle needs secure context). */
  function sha256Fallback(bytes) {
    // Minimal SHA-256 (public domain style) for non-secure HTTP LAN testing.
    function rotr(n, x) {
      return (x >>> n) | (x << (32 - n));
    }
    const K = [
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
      0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
      0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
      0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
      0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
      0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
      0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
    ];
    let h0 = 0x6a09e667;
    let h1 = 0xbb67ae85;
    let h2 = 0x3c6ef372;
    let h3 = 0xa54ff53a;
    let h4 = 0x510e527f;
    let h5 = 0x9b05688c;
    let h6 = 0x1f83d9ab;
    let h7 = 0x5be0cd19;
    const l = bytes.length;
    const bitLenHi = Math.floor((l * 8) / 0x100000000);
    const bitLenLo = (l * 8) >>> 0;
    const withPad = new Uint8Array(((l + 9 + 63) & ~63));
    withPad.set(bytes);
    withPad[l] = 0x80;
    const dv = new DataView(withPad.buffer);
    dv.setUint32(withPad.length - 8, bitLenHi, false);
    dv.setUint32(withPad.length - 4, bitLenLo, false);
    const W = new Uint32Array(64);
    for (let i = 0; i < withPad.length; i += 64) {
      for (let t = 0; t < 16; t++) W[t] = dv.getUint32(i + t * 4, false);
      for (let t = 16; t < 64; t++) {
        const s0 = rotr(7, W[t - 15]) ^ rotr(18, W[t - 15]) ^ (W[t - 15] >>> 3);
        const s1 = rotr(17, W[t - 2]) ^ rotr(19, W[t - 2]) ^ (W[t - 2] >>> 10);
        W[t] = (W[t - 16] + s0 + W[t - 7] + s1) >>> 0;
      }
      let a = h0;
      let b = h1;
      let c = h2;
      let d = h3;
      let e = h4;
      let f = h5;
      let g = h6;
      let h = h7;
      for (let t = 0; t < 64; t++) {
        const S1 = rotr(6, e) ^ rotr(11, e) ^ rotr(25, e);
        const ch = (e & f) ^ (~e & g);
        const temp1 = (h + S1 + ch + K[t] + W[t]) >>> 0;
        const S0 = rotr(2, a) ^ rotr(13, a) ^ rotr(22, a);
        const maj = (a & b) ^ (a & c) ^ (b & c);
        const temp2 = (S0 + maj) >>> 0;
        h = g;
        g = f;
        f = e;
        e = (d + temp1) >>> 0;
        d = c;
        c = b;
        b = a;
        a = (temp1 + temp2) >>> 0;
      }
      h0 = (h0 + a) >>> 0;
      h1 = (h1 + b) >>> 0;
      h2 = (h2 + c) >>> 0;
      h3 = (h3 + d) >>> 0;
      h4 = (h4 + e) >>> 0;
      h5 = (h5 + f) >>> 0;
      h6 = (h6 + g) >>> 0;
      h7 = (h7 + h) >>> 0;
    }
    return [h0, h1, h2, h3, h4, h5, h6, h7]
      .map((x) => x.toString(16).padStart(8, "0"))
      .join("");
  }

  async function hashPassword(password, salt) {
    const data = new TextEncoder().encode(`${salt}:${password}`);
    if (global.crypto && crypto.subtle && global.isSecureContext !== false) {
      try {
        const buf = await crypto.subtle.digest("SHA-256", data);
        return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
      } catch {
        /* fall through — common on http://LAN-IP (not a secure context) */
      }
    }
    return sha256Fallback(data);
  }

  function randomSalt() {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return [...arr].map((b) => b.toString(16).padStart(2, "0")).join("");
  }

  function publicAccount(acc) {
    if (!acc) return null;
    return {
      id: acc.id,
      nickname: acc.nickname,
      createdAt: acc.createdAt,
      stats: acc.stats || emptyStats(),
      history: acc.history || [],
      authProvider: acc.authProvider || "local",
      // googleId reserved for later Google login binding
      googleId: acc.googleId || null,
    };
  }

  function emptyStats() {
    return {
      plays: 0,
      wins: 0,
      losses: 0,
      kills: 0,
      saves: 0,
      score: 0,
    };
  }

  function setSession(accountId) {
    if (!accountId) localStorage.removeItem(SESSION_KEY);
    else localStorage.setItem(SESSION_KEY, accountId);
  }

  function getSession() {
    const id = localStorage.getItem(SESSION_KEY);
    if (!id) return null;
    const acc = readAccounts().find((a) => a.id === id);
    return publicAccount(acc);
  }

  async function register(nickname, password) {
    const v = validateNickname(nickname);
    if (!v.ok) return { ok: false, error: v.error };
    if (!password || String(password).length < 4) {
      return { ok: false, error: "비밀번호는 4자 이상이에요." };
    }
    if (isNicknameTaken(v.nick)) {
      return { ok: false, error: "이미 사용 중인 닉네임이에요." };
    }
    const salt = randomSalt();
    const passwordHash = await hashPassword(password, salt);
    const acc = {
      id: `local_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
      nickname: v.nick,
      salt,
      passwordHash,
      authProvider: "local",
      googleId: null,
      createdAt: Date.now(),
      stats: emptyStats(),
      history: [],
    };
    const list = readAccounts();
    list.push(acc);
    writeAccounts(list);
    setSession(acc.id);
    return { ok: true, account: publicAccount(acc) };
  }

  async function login(nickname, password) {
    const v = validateNickname(nickname);
    if (!v.ok) return { ok: false, error: v.error };
    const acc = findByNick(v.nick);
    if (!acc) return { ok: false, error: "계정을 찾을 수 없어요." };
    if (acc.authProvider === "google" && !acc.passwordHash) {
      return { ok: false, error: "구글 로그인 계정이에요. (추후 지원)" };
    }
    const hash = await hashPassword(password, acc.salt);
    if (hash !== acc.passwordHash) return { ok: false, error: "비밀번호가 올바르지 않아요." };
    setSession(acc.id);
    return { ok: true, account: publicAccount(acc) };
  }

  function logout() {
    setSession(null);
  }

  function requireSession() {
    const s = getSession();
    if (!s) return { ok: false, error: "로그인이 필요해요." };
    return { ok: true, account: s };
  }

  function recordMatch(result) {
    const id = localStorage.getItem(SESSION_KEY);
    if (!id) return { ok: false, error: "로그인 필요" };
    const list = readAccounts();
    const idx = list.findIndex((a) => a.id === id);
    if (idx < 0) return { ok: false, error: "계정 없음" };
    const acc = list[idx];
    if (!acc.stats) acc.stats = emptyStats();
    if (!acc.history) acc.history = [];

    const kills = Number(result.kills) || 0;
    const saves = Number(result.saves) || 0;
    const score = Number(result.score) || kills * 100 + saves * 50;
    const won = Boolean(result.won);

    acc.stats.plays += 1;
    if (won) acc.stats.wins += 1;
    else acc.stats.losses += 1;
    acc.stats.kills += kills;
    acc.stats.saves += saves;
    acc.stats.score += score;

    acc.history.unshift({
      at: Date.now(),
      mode: result.mode || "solo",
      won,
      kills,
      saves,
      score,
      timeSec: Math.floor(Number(result.timeSec) || 0),
      bots: Number(result.bots) || 0,
    });
    acc.history = acc.history.slice(0, MAX_HISTORY);
    list[idx] = acc;
    writeAccounts(list);
    return { ok: true, account: publicAccount(acc) };
  }

  /**
   * Future Google login sketch:
   * - Sign in with Google → get google sub (unique)
   * - If googleId exists → login that account
   * - Else create one account bound to that googleId (1 Google = 1 nickname/id)
   */
  function googleLoginNotReady() {
    return {
      ok: false,
      error: "구글 로그인은 추후 계정 서버 연동 후 지원 예정이에요.",
    };
  }

  global.BnbAccount = {
    validateNickname,
    isNicknameTaken,
    register,
    login,
    logout,
    getSession,
    requireSession,
    recordMatch,
    googleLoginNotReady,
    MAX_WEIGHT,
  };
})(window);
