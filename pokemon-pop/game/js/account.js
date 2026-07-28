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

  async function hashPassword(password, salt) {
    const data = new TextEncoder().encode(`${salt}:${password}`);
    const buf = await crypto.subtle.digest("SHA-256", data);
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
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
