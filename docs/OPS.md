# Ops Runbook

## Scheduler

**Decision:** Option (a) — Push-mirror to GitHub.com and run GitHub Actions there.

Rationale: This repo lives on Gitea (`/Users/rjl/Code/gitea/lowcarboncontracts`).
GitHub Actions cron only runs on github.com. The recommended default is to maintain
a push-mirror from Gitea to a public GitHub repo so the `.github/workflows/` files
execute on GitHub's free hosted runners.

### One-time setup
1. Create a public repo on GitHub (e.g. `github.com/<your-handle>/cfd-visualiser`).
2. Add it as a second remote and push: `git remote add github <url> && git push github main`.
3. Configure Gitea push-mirroring under Settings -> Repository -> Mirroring (or
   push manually after each local commit with `git push github main`).
4. Add the four secrets (see Secrets section below) to the GitHub repo under
   Settings -> Secrets and variables -> Actions.

The CI workflow (`ci.yml`) runs on every push; the daily workflow (`daily.yml`)
runs on `schedule: cron: '30 6 * * *'` (06:30 UTC) and on `workflow_dispatch`.

---

## Analytics

**Chosen:** Cloudflare Web Analytics (OPS-05).

Why: Free, cookieless, no PII, no consent banner required, no third-party domain
under EU/UK tracker lists. The beacon script loads from
`static.cloudflareinsights.com` with the `data-cf-beacon` token substituted into
`dist/**/*.html` at deploy time (sed step in `daily.yml`). If the secret
`CF_WEB_ANALYTICS_TOKEN` is unset the placeholder string `__CF_WEB_ANALYTICS_TOKEN__`
remains in the HTML and the beacon silently no-ops — no 404s, no user tracking.

Alternatives considered and rejected:

| Option | Reason rejected |
|--------|-----------------|
| Plausible Cloud | €9/mo — violates zero-cost constraint |
| Self-hosted Plausible | Requires a live VM — violates zero-cost constraint |
| Google Analytics | Fails OPS-05: third-party cookies, tracker status, consent banner required |
| No analytics | Accepted fallback if CF token is never provisioned |

---

## Secrets (GitHub Actions)

Set these under GitHub repo Settings -> Secrets and variables -> Actions -> New repository secret.

| Secret | Source | Scope / Notes |
|--------|--------|---------------|
| `CF_API_TOKEN` | Cloudflare dashboard -> My Profile -> API Tokens -> Create Token (Custom: Account > Cloudflare Pages > Edit, scoped to one account) | Rotate every 90 days |
| `CF_ACCOUNT_ID` | Cloudflare dashboard sidebar (any zone or account page) -> Account ID | Read-only identifier |
| `PIPELINE_HC_URL` | Healthchecks.io -> Projects -> your check -> copy the Ping URL | Ping URL (UUID in path — keep private) |
| `CF_WEB_ANALYTICS_TOKEN` | Cloudflare dashboard -> Analytics & Logs -> Web Analytics -> Add a site -> copy token from beacon snippet | Site identifier; substituted into HTML at deploy |

See `.env.example` for the local-dev equivalent.

---

## Failure Playbook

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| Healthchecks.io alert email | Daily run missed or failed | Check GitHub Actions `daily-rebuild` log; look at exit code |
| Exit 1 in pipeline | Fetch failed (LCCC URL 5xx / 404 / HTML response) | Check LCCC portal; if URL changed, update `pipeline/fetch.py::LCCC_URL` |
| Exit 2 in pipeline | Schema drift — column added/removed/renamed | Inspect `data/raw/<today>.csv.gz` vs yesterday; update Pandera schema in a new plan |
| Exit 3 in pipeline | DuckDB write error | Check disk space; run `PRAGMA integrity_check` locally on `data/cfd.duckdb` |
| Exit 5 in pipeline | chart/meta build error | Likely DuckDB aggregate returned NaN; inspect with `duckdb data/cfd.duckdb` |
| Exit 7 in pipeline | OG card build failed | Check matplotlib availability; inspect `src/data/chart-3c.json` for empty records |
| Deploy failed | CF token expired or project deleted | Rotate token in Cloudflare dashboard and update GitHub secret; recreate project if needed |
| Cron disabled | GitHub 60-day inactivity (unlikely — see Keepalive) | Run `gh workflow enable daily.yml` then `gh workflow run daily.yml` |

---

## Keepalive — GitHub 60-day Inactivity Rule

GitHub disables scheduled workflows after 60 consecutive days without repository
activity. This project satisfies the rule **intrinsically**: every successful daily
run commits `data/raw/YYYY-MM-DD.csv.gz` (plus `data/cfd.duckdb` and
`src/data/*.json` deltas) to `main`, which resets the 60-day clock. No separate
`last_build.txt` touch file is created — the data archive itself *is* the activity
signal.

**Rescue path** (if LCCC is offline for 60+ consecutive days — unlikely but possible):
Healthchecks.io will alert long before the 60-day mark. If the workflow is
ever auto-disabled, run:

```bash
gh workflow enable daily.yml
gh workflow run daily.yml
```

Document any such incident in an ops incident log.

---

## Archive Retention (Phase 2 deferral — RESEARCH Open Q6)

Raw archives accumulate at ~3 MB/day gzipped (~1 GB/year). v1 commits every
archive without rotation as a known limitation. Rotation to Cloudflare R2
with a monthly pruning job is deferred to Phase 2.

---

## Editorial Label Glossary (Phase 2 deferral — RESEARCH Open Q7)

The raw `Allocation_round` value `"Investment Contract"` is retained as the
canonical key and displayed verbatim in v1 UI. A glossary entry in the captions
content provides a one-line public gloss. Re-labelling is deferred to Phase 2
so it can be validated against real-world reader feedback.

---

## First-Run Deployment Checklist

1. Push repo to GitHub (see Scheduler section above).
2. Create Cloudflare Pages project named `cfd-visualiser` via:
   Cloudflare dashboard -> Workers & Pages -> Create application -> Pages -> Direct Upload.
3. Enable Cloudflare Web Analytics:
   Cloudflare dashboard -> Analytics & Logs -> Web Analytics -> Add a site -> select `cfd-visualiser`.
   Copy the token from the beacon snippet and set it as `CF_WEB_ANALYTICS_TOKEN` in GitHub secrets.
4. Set up Healthchecks.io:
   healthchecks.io -> Add Check -> name `cfd-daily-pipeline` -> schedule: every 1 day, grace: 2h.
   Add email notification for your address. Copy the Ping URL and set it as `PIPELINE_HC_URL`.
5. Set `CF_API_TOKEN` and `CF_ACCOUNT_ID` in GitHub secrets (see Secrets section).
6. Trigger the daily workflow manually via GitHub Actions -> daily-rebuild -> Run workflow.
7. Confirm the workflow completes green and the site appears at
   `https://cfd-visualiser.pages.dev` (or your custom domain).
8. Walk the post-deploy checklist in Plan 01-05 Task 4.
