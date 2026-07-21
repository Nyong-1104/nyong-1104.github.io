# POP data updates

## Refresh catalog

```bash
python pokemon-pop/scripts/build_catalog.py
```

## Refresh live POP/price

```bash
python pokemon-pop/scripts/fetch_live.py
```

GitHub Actions runs **hourly** (`.github/workflows/daily-pokepop.yml`) so BRG POP stays fresher.

| Field | Source |
|-------|--------|
| **BRG POP** | [break.co.kr](https://break.co.kr/pop-report) (`gate.break.co.kr`, no key) |
| **PSA / BGS / … POP** | seed / empty (not live yet) |
| **Prices** | eBay Browse medians when credentials set; else seed |

BRG column map: **10←100 · 9.5←90 · 9←85 · 8←80**.

### BRG-only test

```bash
python pokemon-pop/scripts/fetch_live.py --skip-ebay --pack sv2a-151 --langs jp,kr
```

### eBay setup

Copy `pokemon-pop/.env.example` → `.env` with Production App ID / Cert ID from [developer.ebay.com](https://developer.ebay.com).

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
