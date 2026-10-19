# The Draw — how this site is deployed

Read this before changing anything here.

## Where it lives

| | |
|---|---|
| Live site | https://thedraw.tampaerdoc.com |
| Repo | `tampaERdoc/the-draw` (GitHub Pages, branch `main`, root) |
| Old URL | `tampaerdoc.github.io/the-draw` — still works, redirects |
| Site password | `doghouse` |

## One command

```
python3 tools/deploy.py "what changed"
```

That runs the whole chain and pushes. Pages redeploys itself; the change is
live in about a minute.

## Why the one command matters

**The site reads `data/*.enc.js`, not `private/*.json`.** The private JSON is
the source; the `.enc.js` files are AES-encrypted builds of it, and they are
what ships. So:

- Editing `private/*.json` and pushing publishes **nothing**.
- Editing `index.html` without re-encrypting publishes a new page over
  **stale data**.

Neither mistake announces itself. `deploy.py` always runs every step in order,
whichever file was touched, which is the point of it.

The chain: `tools/members.py` (MusicBrainz line-ups) → `tools/discogs_members.py`
(Discogs line-ups, only for bands MusicBrainz missed) → `tools/instruments.py`
(one primary instrument per member) → `tools/copy.py` (headlines, pitches,
and it calls `tools/redact.py`) → `tools/corrections.py` → `tools/encrypt.py`
across every dataset in `tools/datasets.py` → commit → push.

`tools/datasets.py` is the single list of datasets. Adding a festival means adding
one line there and one `private/<id>.json`; nothing else needs to know.

## Two things that must survive every rebuild

1. **Sulynn Hago's earnings estimate stays out.** Builders regenerate the band
   arrays from source, which puts it back. `tools/redact.py` strips it again,
   and `deploy.py` refuses to push if it reappears.
2. **`CNAME` stays in the repo.** It holds `thedraw.tampaerdoc.com` and is how
   Pages knows the custom domain. Delete it and the github.io URL starts
   redirecting to a name Pages no longer answers for — the site goes dark.
   `deploy.py` refuses to push without it. Only add it when DNS already
   resolves; adding it first takes the site down until DNS catches up.

## GoDaddy

Nothing to do. DNS was set once — a CNAME record, `thedraw` →
`tampaerdoc.github.io` — and content changes never touch it. It only matters
again if the domain itself changes. Note that saving a DNS record there
requires a 6-digit SMS code, so Jason has to do that part.

GitHub repository *settings* (renaming, Pages options such as Enforce HTTPS)
can't be changed from a Claude session — the egress proxy blocks settings
writes with `403: Repository settings writes are not permitted through this
proxy`. Pushes are fine. Settings changes have to be done by hand.

## Rebuilding data from scratch

Builders live outside the repo in `/home/claude/{warped,riot,fest,rank}_data/`
and `/home/claude/people/`. `people/fetch.py` pulls MusicBrainz line-ups
(~1 hour for 1,263 bands) and `people/verify.py` identity-checks the bands
matched by name alone. Neither needs re-running for an ordinary edit.
