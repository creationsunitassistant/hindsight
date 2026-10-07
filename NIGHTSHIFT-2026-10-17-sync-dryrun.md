# Sync dry-run Oct 17 (nightshift t_42e20ddc) — SUPERSEDES 2026-10-16

Upstream moved 32 -> 84 ahead since the Oct 16 dry-run (tip now 5331da2f4,
+52 commits). The Oct 16 branch/apply block is OBSOLETE: applying it would
leave main 52 behind and Monday's cron would rebase again (abort risk).

`nightshift/20261017-sync-dryrun` = upstream/main@5331da2f4 + the same 3
fork commits (on_pre_compress + 2 hardening), rebased 2026-10-17 01:30.

- Rebase was CLEAN — zero conflicts. Upstream's 52 new commits never touched
  `hindsight-integrations/hermes/`, so the old conflict classes (version bump,
  test_provider.py) did not recur. Upstream has still NOT adopted
  on_pre_compress; the 3-commit delta stays.
- Fork version policy kept: plugin.yaml `version: 1.3.0`.
- Plugin suite gate (same command the cron runs): **153 passed in 5.97s**.
- Verified `git rev-list --count nightshift/20261017-sync-dryrun..upstream/main`
  = 0, so after the reset below Monday's cron sees BEHIND=0 -> "up to date"
  -> clean exit. main was NOT touched; nothing pushed.

## To apply (Luc's call — one command)

    cd /Users/macoffice/prs/hindsight
    git switch main && git reset --hard nightshift/20261017-sync-dryrun
    git push --force-with-lease origin main
    hermes plugins install "https://github.com/creationsunitassistant/hindsight#hindsight-integrations/hermes" --force --ref "$(git rev-parse HEAD)" --yes-deps

## Without it

Monday Oct 19 09:00 cron rebases main (still 84 behind) and hits the SAME
test_provider.py conflict as Oct 16 (script allowlist = version files only)
-> aborts loudly -> Telegram alert, plugin drifts.

## Known limits

- If upstream lands plugin-dir commits before Monday AND you applied the
  reset, cron rebases those; new conflicts may recur (structural: upstream
  co-develops the plugin dir). Real fix: upstream our PRs.
- Insurance bundle: /Volumes/MacWork/HERMES_ARCHIVES/nightshift-bundles/20261017/
