# POP data updates

## Refresh catalog

```bash
python pokemon-pop/scripts/build_catalog.py
```

## Refresh live POP/price

```bash
python pokemon-pop/scripts/fetch_live.py
```

GitHub Actions runs **hourly** (`.github/workflows/daily-pokepop.yml`).

| Field | Source |
|-------|--------|
| **BRG POP** | [break.co.kr](https://break.co.kr/pop-report) (`gate.break.co.kr`, no key) |
| **PSA POP** | GemRate set dumps → `gemrate_pop.py` (`source: gemrate`) |
| **BGS / CGC / …** | empty (not live yet) |
| **Prices** | eBay Browse medians when credentials set; otherwise hidden (no fake seed prices) |

**Tiers**

| Tier | Rarity | Live snapshot |
|------|--------|---------------|
| A | SAR, SIR, HR, UR, SR, AR, SSR, S_2, RRR, **BWR** | POP + price shell |
| B | RR, PRISM, R, PROMO | POP + price shell |
| C | U, C, other | Catalog only (skipped in live) |

**BWR** (Black / White / Red special finish) is **not** a general rule — only three cards, listed in `scripts/bwr_cards.py`:
제크로무 ex (Black Bolt), 레시라무 ex (White Flare), 비크티니 (Red Collection).

BRG column map: **10←100 · 9←90(+85) · 8←80 · ≤7←rest**. PSA rightmost column is **≤7**, not full total.

### BRG-only test

```bash
python pokemon-pop/scripts/fetch_live.py --skip-ebay --pack sv2a-151 --langs jp,kr
```

### eBay setup (required for real prices)

1. Create a Production keyset at [developer.ebay.com](https://developer.ebay.com) (App ID + Cert ID).
2. Local: copy `pokemon-pop/.env.example` → `pokemon-pop/.env` and fill:

```env
EBAY_CLIENT_ID=...
EBAY_CLIENT_SECRET=...
EBAY_FETCH_LIMIT=200
```

3. GitHub Actions (hourly job): repo **Settings → Secrets and variables → Actions** → add:

- `EBAY_CLIENT_ID`
- `EBAY_CLIENT_SECRET`

Until these secrets exist, the site shows **—** for prices (seed placeholders are not shown).

```bash
python pokemon-pop/scripts/fetch_live.py --ebay-limit 5 --pack sv2a-151 --langs jp --force
```

Flags: `--pack`, `--langs`, `--skip-brg`, `--skip-ebay`, `--seed-only`, `--dry-run`, `--ebay-limit`.

## GemRate PSA POP

Daily VPS cron (KST 00:05) runs Playwright → dump+CSV → `pop.PSA`.
Fetches **one set page per minute** (`--sleep 60`) so midnight traffic is spaced, not a burst.
See `pokemon-pop/scripts/vps/README.md`.

```bash
# local: fetch + apply (needs Playwright Chromium)
pip install -r pokemon-pop/scripts/requirements-gemrate.txt
python -m playwright install chromium
python pokemon-pop/scripts/fetch_gemrate.py

# one pack / apply-only
python pokemon-pop/scripts/fetch_gemrate.py --pack m1s-mega-symphonia --langs jp,kr
python pokemon-pop/scripts/gemrate_pop.py --pack sv2a-151 --langs jp,kr,en
```

`GEMRATE_SETS` (`gemrate_pop.py`):

| Pack | JP | KR | EN |
|------|----|----|-----|
| `sv2a-151` | fetch | fetch | fetch |
| `m1l-mega-brave` | fetch | fetch | fetch (`Pokemon Meg EN-Mega Evolution`) |
| `m1s-mega-symphonia` | fetch | fetch | **reuse** Brave EN dump (same GemRate page) |
| `sv10-rocket-glory` | fetch | fetch | fetch (`Pokemon Dri EN-Destined Rivals`) |
| `sv11b-black-bolt` | fetch | fetch | fetch (`Pokemon Blk EN-Black Bolt`) |
| `sv11w-white-flare` | fetch | fetch | fetch (`Pokemon Wht EN-White Flare`) |

`fetch_live.py` restores previous GemRate PSA (`source: gemrate`) so hourly BRG refresh does not wipe them.

## GitHub Actions

`.github/workflows/daily-pokepop.yml` runs **hourly**. Optional secrets: `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`. BRG needs none.
