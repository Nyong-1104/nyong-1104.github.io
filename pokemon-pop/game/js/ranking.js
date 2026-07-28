/**
 * Ranking store for pokePOP minigame only.
 * Score = kills / saves based (not blocks).
 */
(function (global) {
  const cfg = global.BnbConfig;

  function storageKey() {
    return `${cfg.STORAGE_PREFIX}rank:${cfg.BOARD_ID}`;
  }

  function readLocal() {
    try {
      const raw = localStorage.getItem(storageKey());
      const list = raw ? JSON.parse(raw) : [];
      return Array.isArray(list) ? list : [];
    } catch {
      return [];
    }
  }

  function writeLocal(list) {
    localStorage.setItem(storageKey(), JSON.stringify(list.slice(0, cfg.MAX_LOCAL_ENTRIES)));
  }

  function getNickname() {
    return (localStorage.getItem(cfg.NICK_KEY) || "").trim();
  }

  function setNickname(name) {
    const clean = String(name || "")
      .trim()
      .slice(0, 12);
    if (clean) localStorage.setItem(cfg.NICK_KEY, clean);
    return clean;
  }

  function sortEntries(list) {
    return list
      .slice()
      .sort(
        (a, b) =>
          b.score - a.score ||
          (b.kills || 0) - (a.kills || 0) ||
          (b.saves || 0) - (a.saves || 0) ||
          a.timeSec - b.timeSec ||
          a.at - b.at
      );
  }

  async function fetchRemote() {
    if (!cfg.API_BASE) return null;
    const url = `${cfg.API_BASE.replace(/\/$/, "")}/rankings/${encodeURIComponent(cfg.BOARD_ID)}`;
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("rank fetch failed");
    const data = await res.json();
    return Array.isArray(data) ? data : data.entries || [];
  }

  async function postRemote(entry) {
    if (!cfg.API_BASE) return null;
    const url = `${cfg.API_BASE.replace(/\/$/, "")}/rankings/${encodeURIComponent(cfg.BOARD_ID)}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(entry),
    });
    if (!res.ok) throw new Error("rank submit failed");
    return res.json();
  }

  async function list() {
    try {
      const remote = await fetchRemote();
      if (remote) return sortEntries(remote).slice(0, cfg.MAX_LOCAL_ENTRIES);
    } catch {
      /* fall back to local */
    }
    return sortEntries(readLocal());
  }

  async function submit(entry) {
    const kills = Number(entry.kills) || 0;
    const saves = Number(entry.saves) || 0;
    const row = {
      name: entry.name || "Guest",
      score: Number(entry.score) || kills * 100 + saves * 50,
      kills,
      saves,
      timeSec: Math.floor(Number(entry.timeSec) || 0),
      won: Boolean(entry.won),
      at: Date.now(),
    };

    const local = sortEntries([row, ...readLocal()]).slice(0, cfg.MAX_LOCAL_ENTRIES);
    writeLocal(local);

    let remoteOk = false;
    try {
      await postRemote(row);
      remoteOk = Boolean(cfg.API_BASE);
    } catch {
      remoteOk = false;
    }

    return { entry: row, remoteOk, list: await list() };
  }

  function modeLabel() {
    return cfg.API_BASE ? "온라인 랭킹 준비됨" : "이 기기 랭킹 (로컬)";
  }

  global.BnbRanking = {
    list,
    submit,
    getNickname,
    setNickname,
    modeLabel,
  };
})(window);
