# POP data updates

MVP stores POP and PSA prices in `../data/cards.json` as manual snapshots.

## Later: GitHub Actions

1. Add a script that refreshes `pop` / `price` fields per card id.
2. Schedule a workflow (daily/weekly) to commit updated JSON.
3. Keep grader columns: PSA, BGS, CGC, BRG, TAG, ACE, AGS.

Do not put API secrets in the static site; refresh must run server-side or in Actions.
