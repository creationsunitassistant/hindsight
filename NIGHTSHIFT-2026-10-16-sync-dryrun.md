# Sync dry-run Oct 16 (nightshift t_02d10993)

Cron `hindsight-fork-sync` (8906c9ad863d) fires Mon Oct 19 09:00.
Dry-run proved it will ABORT: rebasing main (3 fork commits) onto
upstream/main (32 ahead, tip 9a499b175) conflicts on THREE files:

- `plugin.yaml`, `pyproject.toml` — version-bump class (upstream 1.2.3 vs
  fork 1.3.0) → script auto-resolves these
- `tests/test_provider.py` — NOT in the allowlist → script aborts loudly
  ("manual work needed") → Telegram alert, plugin drifts.

Upstream did NOT adopt on_pre_compress; the 3-commit delta stays.

## Fix pre-baked here (this branch)

`nightshift/20261016-sync-dryrun` = upstream/main + 3 fork commits,
resolutions:
- version files: upstream content + fork 1.3.0 (script's own policy)
- test_provider.py: keep BOTH sides (upstream's 2 observation_scopes
  tests + fork's on_pre_compress section) — both appended at EOF, no
  semantic overlap
- plugin suite: **153 passed** (151 + 2 new upstream), same gate the
  cron runs. main was NOT touched.

## To apply (Luc's call — one command)

    cd /Users/macoffice/prs/hindsight
    git switch main && git reset --hard nightshift/20261016-sync-dryrun
    git push --force-with-lease origin main
    hermes plugins install "https://github.com/creationsunitassistant/hindsight#hindsight-integrations/hermes" --force --ref "$(git rev-parse HEAD)" --yes-deps

After the reset, Monday's cron sees BEHIND=0 → "up to date" → clean exit.
Without it, Monday aborts with the exact conflict reproduced here.

## Known limits

- If upstream moves again before Monday AND you applied the reset, cron
  rebases again — future test-file conflicts may recur (structural:
  upstream co-develops the plugin dir). Real fix: upstream our PRs.
