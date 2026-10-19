# The Draw

A scouting database for finding Sulynn Hago a direct-support slot. "Draw" is the industry word for how many people an act actually pulls into a room, and that is what every band here is measured by: Sincere Engineer sits at 1.00×, and every other band is bigger or smaller than her.

Password-protected static site for scouting bands: audience (Instagram/Spotify), label, booking and modeled-earnings data, plus a graded support-slot target cohort benchmarked against Sincere Engineer.

Data files are encrypted (AES-256-GCM, key derived with PBKDF2-SHA256, 310k iterations) and decrypted in the browser after the password is entered, so neither this repository nor the published site exposes readable band data. The page is `noindex` so search engines don't list it.

## Datasets
| Toggle | Encrypted data file | Acts |
|---|---|---|
| Warped Tour 2026 (Orlando, Nov 14–15) | `data/warped-2026.enc.js` | 143 |
| Riot Fest 2026 (Douglass Park, Chicago, Sept 18–20) | `data/riot-2026.enc.js` | 106 |
| Fest 2026 / FEST 24 (Gainesville, Oct 23–25) | `data/fest-2026.enc.js` | 334 |
| Watchlist (bands to follow, from the earnings ranking) | `data/watchlist-2026.enc.js` | 746 |
| All Bands | *(virtual — merges every loaded dataset)* | 1,280 distinct |

The **All Bands** toggle appears automatically once two or more datasets are present. A band tracked on more than one list has a record on each; the combined view merges them into one row, keeping the most complete record and listing every source, so 1,329 records become 1,280 distinct bands.

Every record also carries **`plays_2026`** — which of the three 2026 bills that band actually plays, cross-referenced by name across all four datasets. 23 bands play more than one. It is a table column, a filter, and an ask-the-data phrase ("bands on more than one 2026 bill").

`#warped-2026`, `#riot-2026`, `#fest-2026`, `#watchlist-2026` and `#all` are deep-linkable.

## The Sincere Engineer grade
Every band with both an Instagram and a Spotify figure is graded on one scale:

- **Size index** = √((IG ÷ 42,256) × (Spotify ÷ 76,852)). **1.00 = the same draw as Sincere Engineer.** The index is turned into a weight that is 1.00 inside 0.80–1.25× and falls off from there.
- **Genre fit** scores how close the band's style is to Sulynn Hago's lane, from 1.00 (pop-punk, emo, melodic punk, power pop) down to 0.00 (hip-hop, pop, dance). The *first* tag is the band's primary style and carries the weight; a strong secondary tag can lift the score but not carry it, so "Mariachi / Punk" does not score as a punk band.
- **Grade** = weight × fit → A+ ≥ 0.85, A ≥ 0.65, A- ≥ 0.45, B ≥ 0.28, C ≥ 0.12, D below. Sincere Engineer herself lands at 1.00× and A+, which is the check that the scale is anchored.

`grade_basis` on each record states the arithmetic in words. Bands missing either figure are left ungraded rather than guessed at.

Separately, **`shortlisted`** marks the bands hand-picked as support-slot targets, with the written pitch angle in `pitch` and the original hand tier in `shortlist_tier`. Those carry a ★ and have their own chip and filter — the computed grade measures size and style, the shortlist adds judgement about reachability and the way in.

## Filtering
The lists live in a **Festivals** dropdown at the right of the masthead, grouped under "2026 festivals" and "Follow list" with All Bands pinned at the top; the button always shows which list you are in. It replaced a horizontal tab row that would not survive more than a handful of festivals.

Past the password the site opens on **All Bands** with the cursor already in the search box, since searching is nearly always the first move; a URL ending `#warped-2026`, `#riot-2026`, `#fest-2026` or `#watchlist-2026` still opens that list instead, and a phone is left unfocused so the keyboard stays down.

A search box sits in the masthead, next to the list tabs, and follows you down the page. It searches everything — band, member, label, agent, hometown — and shows a live count of what matches; clicking that count jumps to the results, as does Enter. It and the search box in the filter panel are the same search, kept in step.

Instagram followers, Spotify monthly listeners, size index and estimated earnings each get their own dual-handle **log-scale range slider**, sitting across the top of the filter panel. Each draws the distribution of the current list behind the rail, so you can see where the bands actually sit before you drag; bars outside the range dim. The pair of boxes under each slider takes a typed bound (`50k`, `1.5m`, `0.8`) and keeps that number exactly rather than snapping to the nearest slider step, and a per-slider **Reset** appears once a slider is doing something. Booking agency, record label, genre and hometown are type-to-search boxes that accept a partial match (typing "epitaph" matches every Epitaph imprint). Everything else is a dropdown, and the plain-English ask box writes to the same filters.

## Who plays in what
Every member carries one **primary instrument**, normalised. MusicBrainz mixes instruments with membership attributes in a single list, so "original" and "additional" are split off into their own field and "membranophone" reads Drums. Where someone plays several, the instrument wins over vocals — a singing guitarist is found as a guitarist — and a person in several bands gets one main instrument across all of them, decided by what they play most often.

So the search box takes the words people actually use. Typing **drummers**, **bassists**, **guitarists**, **sax** or **keys** filters to bands whose line-up includes one, and the ask box combines it: *drummers in A+ bands*, *guitarists on 4AD*. There is also an **Instrument in the band** dropdown in the filter panel.

Every band carries its line-up, and every person in it is a link. Search any member's name in the search box and a strip above the table names them with the number of bands they're in; the table underneath narrows to those bands. Clicking a person opens their record — every band they play in, with grade and size index — and clicking a band from there opens the band. Inside a band, the **Line-up** group lists each member as a chip with instrument and years where MusicBrainz has them; former members are dimmed. A back link returns you to the band you came from.

The person index spans **all four lists at once**, not just the tab you're on, so searching a Watchlist member while looking at Warped still finds them; a band on another list is marked "other list" and clicking it jumps to All Bands and opens it there. The ask box understands names too — "who plays with Sulynn Hago" returns Propagandhi and Sulynn Hago.

Line-ups come from MusicBrainz `member of band` relations where MusicBrainz has the artist, and otherwise from the people the earnings workbook attributes to that band — usually the frontperson only. Each line-up says which. Where a band was matched to MusicBrainz by name alone rather than through the catalogue-verified Spotify work, `people/verify.py` re-checks the identity: it compares MusicBrainz's own Spotify link against the one read directly from Spotify, and where there is no link to compare, re-runs the search to see whether more than one artist carries that name. Sixteen bands failed that check and carry no line-up rather than somebody else's. Current/former status is MusicBrainz's, and it is not always right about reunions — Keith Morris reads as a former Circle Jerk because the entry ends at the original run. A handful of touring members MusicBrainz doesn't credit are added by hand in `tools/members.py`. Line-up and its source are columns in every export.

## Estimated earnings
The earnings columns come from a supplied punk/indie earnings ranking workbook and are **modeled estimates, not reported or audited figures**. The source derives each from touring tier, venue capacity, catalog ownership, songwriting splits and label structure, and states error bars of ±40% for ranks 1–300 and ±60% for 301–803; ranks 804–1000 are "cohort positions" describing a place in the scene economy rather than a real individual. The workbook ranks **people**, not bands, so a band may contribute several rows: `est_income_top_member` is the highest single estimate and `est_income_members_sum` adds only the members the workbook lists. Every detail view carries the caveat and the per-member breakdown; the table column is asterisked.

## The number line
The hero is an instrument, not a picture. Drag anywhere on it to set a floor and the band grid underneath becomes everything at or above that mark, closest to the line first — the smallest bands that still clear the bar are usually the reachable ones. The segmented control switches what the line measures: **size vs Sincere Engineer**, **Instagram followers** or **Spotify monthly listeners**. Her own figure stays marked in teal on all three, so the benchmark travels with you.

Setting a floor widens the grade chip to All, since A+ bands cluster near 1.00× and dragging right would otherwise empty the grid; the chips still narrow from there. **Use in the filters below** pushes the floor into the matching slider and jumps to the full table. Arrow keys move the handle when it has focus, Shift for bigger steps, Escape to clear.

## Building an export
Tick bands on the cards or in the table. The tick travels with the band, so a selection survives switching lists and filtering; the bar at the foot of the table says how many of the picked bands are currently hidden by filters. **Select these N** takes everything the current filters show.

| Button | What you get |
|---|---|
| Download Excel | A real `.xlsx` — 22 columns, autofilter on, thousands separators and `0.00×` already applied, plus an **About this export** sheet recording the benchmark, how the grade is derived, and the earnings caveat. SheetJS is loaded from cdnjs on first use. |
| Download Word | A briefing to read rather than a grid to calculate in: grouped by grade, one block per band with the audience figures, label, booking and the written pitch. Opens in Word as a `.doc`. |
| CSV | Same columns as the Excel sheet, UTF-8 with a BOM so Excel keeps the accents. No dependency — this is the fallback if cdnjs is unreachable. |
| Copy | Puts the table on the clipboard as both rich HTML and tab-separated text, so it pastes as a formatted table into Word or email and as cells into Excel. |

Selections live in `sessionStorage` and clear when the tab closes.

## Adding a dataset
1. Put the plaintext dataset at `private/<id>.json` — same shape as the existing ones:
   `{label, title, kicker, subtitle, cohortLede, generated, benchmark, examples[], notes, bands[]}`.
   Each band:
   `name, entity_type, grade, grade_score, grade_basis, shortlisted, shortlist_tier, pitch, genre, genre_source,
   plays_2026[], plays_2026_text, plays_count, day, hometown, status, instagram_handle,
   instagram_followers, instagram_source, ig_socialblade, ig_hypeauditor, ig_hypeauditor_date, instagram_url,
   spotify_listeners, spotify_followers, spotify_url, spotify_name, spotify_verification,
   size_vs_sincere_engineer, label, label_note, label_source, agency, agent, booking_notes, booking_evidence,
   booking_source, flags, poster_row, predicted_set_time, earnings_rank, est_income_top_member, est_income_members_sum, earnings_confidence,
   earnings_error_band, earnings_members[], earnings_caveat, earnings_source, follower_source_date, watchlist`
   Numeric fields must be `null` (not `""`) when unknown, or range filters will treat them as zero.
   (`private/` is git-ignored and never pushed.)
2. `python3 tools/encrypt.py <id> "<the same password>"` → writes `data/<id>.enc.js`.
3. Add `{id:'<id>', label:'…'}` to `FEST_REGISTRY` near the top of the script in `index.html`.
4. Commit and push `data/<id>.enc.js`.
5. Re-run the cross-reference so the new bands pick up their 2026 festival flags and grades.

Filter options are derived from the data, so new labels, agencies, genres and record types appear on their own. Any filter with more than 25 options renders as a type-to-search box instead of a dropdown.

## Changing the password
Re-run step 2 for every dataset with the new password, then push.
