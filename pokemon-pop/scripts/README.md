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
| **PSA / BGS / … POP** | empty (not live yet) |
| **Prices** | eBay Browse medians when credentials set; otherwise hidden (no fake seed prices) |

**Tiers**

| Tier | Rarity | Live snapshot |
|------|--------|---------------|
| A | SAR, SIR, HR, UR, SR, AR, SSR, S_2, RRR, **BWR** | POP + price shell |
| B | RR, PRISM, R, PROMO | POP + price shell |
| C | U, C, other | Catalog only (skipped in live) |

**BWR** (Black / White / Red special finish) is **not** a general rule — only three cards, listed in `scripts/bwr_cards.py`:
제크로무 ex (Black Bolt), 레시라무 ex (White Flare), 비크티니 (Red Collection).

BRG column map: **10←100 · 9.5←90 · 9←85 · 8←80**.

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

## PSA set POP links

`data/psa-sets.json` maps each pack × language to a PSA set POP URL.

```bash
python pokemon-pop/scripts/build_psa_sets.py
```

Edit `KNOWN` in that script (or fill `psa-sets.json` by hand), then rebuild `data.js`:

```bash
python pokemon-pop/scripts/build_data_js.py
```

If a URL is missing, the UI falls back to a PSA search query for that set.

## GitHub Actions

`.github/workflows/daily-pokepop.yml` runs **hourly**. Optional secrets: `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`. BRG needs none.
