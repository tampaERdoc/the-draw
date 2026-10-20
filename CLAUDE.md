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
(Discogs line-ups, only for bands MusicBrainz missed) → `tools/discogs_instruments.py`
(instruments for those, from release credits) → `tools/hand_members.py` (line-ups read
by hand) → `tools/instruments.py` (one primary instrument per member) → `tools/copy.py`
(headlines, pitches, and it calls `tools/redact.py`) → `tools/corrections.py` →
`tools/encrypt.py` across every dataset in `tools/datasets.py` → commit → push.

`discogs_instruments.py` must stay ahead of `instruments.py`: it writes `roles`, not
`instrument`, so that `instruments.py` still normalises them and still propagates a
person's instrument to the other bands they play in.

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

## The ten-minute cache, and why the page reloads itself

Pages serves `index.html` with `cache-control: max-age=600`. Those headers cannot be
changed from here, so twice a shipped change looked like it had never shipped and the
next twenty minutes went into proving the deploy had worked.

The page now checks for itself. `deploy.py` writes a timestamp to `build.txt` and
rewrites the matching `const BUILD=` in `index.html`; on load the page fetches
`build.txt` with the cache bypassed and reloads once if the two differ, guarded by a
`sessionStorage` key so a stale CDN edge cannot loop it.

So a report of "I don't see it" is worth verifying against the live URL before changing
any code, and a change to the deploy script must keep stamping both.

## Where line-ups come from, and what is exhausted

In order of what has already been tried for the 3,018 bands:

- **MusicBrainz** - 5,439 member entries, 59% carrying an instrument. The good source.
- **Discogs** - 2,080 entries. Tried against every band MusicBrainz missed and now
  exhausted; re-running it reports nothing left to try. Its artist endpoint gives names
  only, so 97% of those people arrived with no instrument. `dg_credits.py` fills them
  from release `extraartists` roles, which is the one place Discogs keeps instruments.
- **Hand research** via WebSearch and WebFetch, in `work/hand/result_*.json`, globbed
  by `tools/hand_members.py`. Roughly a 50% hit rate on bands both databases missed,
  over the slices in `work/ung/`.

  **Run one slice per turn, not several in parallel.** The web-search budget is 200
  calls *per turn, shared by every agent in that turn*, not per agent. Six agents
  dispatched together starved each other: the first two did real work and the last
  managed ten bands before the budget was gone. The budget, not the method, is the
  binding constraint, so parallelism buys nothing here and costs coverage.
- **Bandcamp scraping is a dead end.** It answers plain `curl` from this container with
  a ~3KB bot-challenge interstitial, not the page. Do not build another scraper for it
  and do not try to defeat the challenge; WebFetch reaches those pages instead.

### Harvesting a festival's own artist pages

`fest2/harvest_bios.py` walks every artist page a festival publishes and
`fest2/bios.py` reads names and instruments out of the prose. Festival sites answer
plain curl, so this costs no search budget. Two loaders consume it: `bios_to_hand.py`
writes line-ups for bands that have none, and `tools/bio_instruments.py` fills blank
instruments on line-ups that already exist.

Measured yield, and the trap:

| site | pages | line-ups | in our dataset |
|---|---|---|---|
| Hopscotch | 100 | 32 | 99% |
| Fest | 329 | 62 | 87% |
| Treefort | 188 | 51 | **11%** |

**Always check the overlap before trusting a yield.** Treefort's `/lineup/` serves the
NEXT festival, and its performer pages are replaced each year rather than archived, so
a 2026 act is a 404 and there is no archive to crawl. Harvesting it looked like 51
line-ups and was really about 7. Hopscotch and Fest keep their pages up and match
almost exactly.

Of the other sites in `datasets.py`, Sled Island, Levitation, Bumbershoot, Shaky Knees
and Riot Fest all answer curl but publish no per-artist bio pages - they are Shopify or
Next.js storefronts, or they key pages by event rather than artist. Bandcamp answers
with a bot challenge. Not worth another attempt at any of them.

Any normalizer that maps a role to an instrument must test **Bass before Guitar**.
"bass guitar" contains "guitar", and the other order silently filed 557 bassists as
guitarists.

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
