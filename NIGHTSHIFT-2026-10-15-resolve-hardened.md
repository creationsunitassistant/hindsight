# 2026-10-15 — auto-resolve hardened (upstream-content-safe)

Nightshift t_ae193257. Live script ~/.hermes/scripts/hindsight-fork-sync.sh (backup
.bak-nightshift-20261015). Old auto-resolve did `git checkout --theirs` on
plugin.yaml/pyproject.toml — adopts the fork's whole file, silently DROPPING any new
upstream content in them (deps/fields). The 151-test gate cannot catch pyproject
dependency drift. Proven RED on a fixture (upstream adds `newdep>=2`: old logic loses it).

New resolution: `checkout --ours` (adopt ALL upstream content) + sed only the version
line to the fork's number, with two fail-loud guards:
  1. fork commit changes those files beyond the version line -> abort (fixture B: fires
     with the exact dropped lines in the message)
  2. staged result differs from upstream beyond the version line -> abort

Verified: fixtures A/B + RED old-logic; real repo rebase via new loop rc=0, tree
byte-identical to the --theirs result (branch nightshift/20261015-resolve-hardened @
522d8af5a), plugin suite 151/151 on that tree. Repo left on main, untouched, nothing pushed.
