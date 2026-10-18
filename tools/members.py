#!/usr/bin/env python3
"""Attach band members to every record, and record who else each person plays with.

Sources, in order of precedence:
  1. MusicBrainz "member of band" relationships (name, instrument, years, current/former)
  2. names the supplied earnings workbook attributes to a band, for bands MusicBrainz
     has no lineup for — these are usually the frontperson only, and are marked as such
  3. MANUAL below, for people MusicBrainz does not list (touring members, mostly)

Run after any dataset rebuild, before encrypting. tools/copy.py calls it.
"""
import json, os, re, unicodedata, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = '/home/claude/people/members_raw.json'
IDS = ('warped-2026', 'riot-2026', 'fest-2026', 'watchlist-2026')

# People MusicBrainz does not credit — touring members and similar. band -> [(person, role)]
MANUAL = {
    'Propagandhi': [('Sulynn Hago', 'guitar (touring)')],
    'Sulynn Hago': [('Sulynn Hago', 'guitar, songwriter')],
}

def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    s = s.replace('&', ' and '); s = re.sub(r'^(the|a)\s+', '', s)
    return re.sub(r'[^a-z0-9]+', '', s)

def pkey(s):
    """A person key: initials and punctuation shouldn't split one person into two."""
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '', s)

PLACEHOLDER = re.compile(
    r'\((?:per member|each|[^)]*(?:members|alumni|residuals|cohort))|'
    r'\b(?:alumni|residuals|estate|per member|non-\w+ members)\b', re.I)

def is_placeholder(name, band):
    if not name: return True
    if PLACEHOLDER.search(name): return True
    if norm(name) == norm(band): return True                 # the row just restates the band
    if norm(name).startswith(norm(band)[:12]) and len(norm(band)) > 8: return True
    return False

def build():
    raw = json.load(open(RAW, encoding='utf-8')) if os.path.exists(RAW) else {}
    stats = collections.Counter()
    for fid in IDS:
        p = os.path.join(ROOT, 'private', fid + '.json')
        d = json.load(open(p, encoding='utf-8'))
        for b in d['bands']:
            k = norm(b['name'])
            out, seen = [], set()
            r = raw.get(k) or {}
            # MusicBrainz: backward on a group means "this person is in this band"
            for m in r.get('members', []):
                if m.get('dir') != 'backward' or not m.get('name'): continue
                if pkey(m['name']) in seen: continue
                seen.add(pkey(m['name']))
                out.append({'name': m['name'], 'mbid': m.get('mbid'),
                            'roles': [x for x in (m.get('roles') or []) if x],
                            'begin': m.get('begin') or '', 'end': m.get('end') or '',
                            'current': not m.get('ended'), 'source': 'MusicBrainz'})
            # forward on a person record means this act IS a person, who plays in other bands
            plays_in = [m['name'] for m in r.get('members', [])
                        if m.get('dir') == 'forward' and m.get('name')]
            # the earnings workbook, for anyone MusicBrainz missed
            for m in (b.get('earnings_members') or []):
                nm = (m.get('name') or '').strip()
                if is_placeholder(nm, b['name']) or pkey(nm) in seen: continue
                seen.add(pkey(nm))
                out.append({'name': nm, 'mbid': None, 'roles': [], 'begin': '', 'end': '',
                            'current': True, 'source': 'Earnings workbook'})
            for nm, role in MANUAL.get(b['name'], []):
                if pkey(nm) in seen: continue
                seen.add(pkey(nm))
                out.append({'name': nm, 'mbid': None, 'roles': [role], 'begin': '', 'end': '',
                            'current': True, 'source': 'Added by hand'})
            out.sort(key=lambda m: (not m['current'], m['begin'] or '9999', m['name']))
            b['members'] = out
            b['member_names'] = ', '.join(m['name'] for m in out)
            b['member_count'] = len(out)
            b['member_source'] = ('MusicBrainz' if any(m['source'] == 'MusicBrainz' for m in out)
                                  else ('Earnings workbook only' if out else 'Not found'))
            b['plays_in'] = plays_in
            stats[fid] += len(out)
            if out: stats[fid + '_bands'] += 1
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    return stats

if __name__ == '__main__':
    st = build()
    people = collections.defaultdict(set)
    for fid in IDS:
        d = json.load(open(os.path.join(ROOT, 'private', fid + '.json'), encoding='utf-8'))
        for b in d['bands']:
            for m in b.get('members', []):
                people[pkey(m['name'])].add(b['name'])
    multi = {k: v for k, v in people.items() if len(v) > 1}
    for fid in IDS:
        print('%-16s %5d members across %d bands' % (fid, st[fid], st[fid + '_bands']))
    print('distinct people: %d  |  in more than one band: %d' % (len(people), len(multi)))
