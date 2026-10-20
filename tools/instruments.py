# -*- coding: utf-8 -*-
"""Give every person one main instrument, and stop membership attributes posing as roles.

MusicBrainz puts everything in one list, so a member reads
["original", "membranophone", "background vocals"] - of which only two are instruments
and one is a word nobody says out loud. This splits that list three ways:

  member_attrs    original, additional, founder - facts about the membership, not the job
  instrument      ONE primary, normalised: Drums, not "membranophone"
  instruments     the rest, same normalisation

A person in several bands gets one main instrument across all of them, decided by what
they play most often. That is what makes "drummers in A+ bands" a question the site can
answer.
"""
import collections, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Not instruments. These describe the membership, and they outnumbered every real
# instrument in the raw data.
ATTRS = {'original', 'additional', 'founder', 'guest', 'live', 'session', 'touring',
         'co-founder', 'member'}

# Everything that means the same instrument, said differently.
CANON = [
    ('Vocals',      r'^(lead |backing |background |additional |guest )?(vocal|voice|singer|scream)'),
    # Bass must be tested BEFORE guitar: "bass guitar" contains "guitar", and testing
    # guitar first filed 557 bassists as guitarists.
    ('Bass',        r'bass(?! drum)|contrabass|double bass|upright bass'),
    # Steel guitar before guitar for the same reason as bass: "steel guitar" contains
    # "guitar", so the other order filed every steel player as a plain guitarist.
    # "Pedal Steel" and "Lap Steel" also arrive from Discogs credits with no "guitar"
    # after them, and requiring the word dropped those people to no instrument at all.
    ('Steel guitar',r'(pedal|lap)[ -]?steel|steel guitar|dobro'),
    ('Guitar',      r'(^|\b)(electric |acoustic |rhythm |lead |slide |12.string |baritone )?guitar'),
    ('Drums',       r'drum|membranophone|percussion set|kit'),
    ('Percussion',  r'percussion|idiophone|tambourine|conga|bongo|timbale|vibraphone|marimba|cowbell'),
    ('Keys',        r'keyboard|piano|organ|rhodes|wurlitzer|harpsichord|mellotron|clavinet'),
    ('Synth',       r'synth|moog|sampler|drum machine|sequencer'),
    ('Programming', r'program|electronic|laptop|beats|production'),
    ('Turntables',  r'turntable|^dj\b|scratch'),
    ('Horns',       r'trumpet|trombone|saxophon|\bsax\b|horn|tuba|cornet|flugelhorn|brass'),
    ('Strings',     r'violin|viola|cello|fiddle|string section|harp\b'),
    ('Woodwind',    r'flute|clarinet|oboe|bassoon|recorder'),
    ('Harmonica',   r'harmonica|harp \(mouth'),
    ('Banjo',       r'banjo'),
    ('Mandolin',    r'mandolin'),
    ('Ukulele',     r'ukulele'),
    ('Accordion',   r'accordion|melodeon'),
]
# When someone plays several, this is the order of what they are known for. A singing
# drummer is a drummer; a drummer who also sings backing vocals is still a drummer.
RANK = ['Vocals', 'Guitar', 'Bass', 'Drums', 'Keys', 'Synth', 'Horns', 'Strings',
        'Woodwind', 'Banjo', 'Mandolin', 'Steel guitar', 'Accordion', 'Harmonica',
        'Ukulele', 'Turntables', 'Programming', 'Percussion']

def canon(role):
    r = (role or '').strip().lower()
    if not r or r in ATTRS:
        return None
    for name, pat in CANON:
        if re.search(pat, r):
            return name
    return None

def split_roles(roles):
    """-> (primary instrument or '', other instruments, membership attributes)"""
    attrs, insts = [], []
    for r in roles or []:
        rl = (r or '').strip().lower()
        if not rl:
            continue
        if rl in ATTRS:
            attrs.append(rl.title())
            continue
        c = canon(rl)
        if c and c not in insts:
            insts.append(c)
    if not insts:
        return '', [], attrs
    # keep MusicBrainz's own order, but let RANK break ties on what someone is known for
    primary = sorted(insts, key=lambda i: (RANK.index(i) if i in RANK else 99,
                                           insts.index(i)))[0]
    # a frontperson who also plays guitar reads better as Guitar/Vocals than Vocals alone,
    # so vocals only wins outright when it is the only thing listed
    if primary == 'Vocals' and len(insts) > 1:
        rest = [i for i in insts if i != 'Vocals']
        primary = sorted(rest, key=lambda i: (RANK.index(i) if i in RANK else 99,
                                              insts.index(i)))[0]
    return primary, [i for i in insts if i != primary], attrs

def main():
    # pass one: what does each person play, across every band they are in
    plays = collections.defaultdict(collections.Counter)
    for fid in IDS:
        p = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(p):
            continue
        for b in json.load(open(p, encoding='utf-8'))['bands']:
            for m in (b.get('members') or []):
                pr, _, _ = split_roles(m.get('roles'))
                if pr:
                    plays[m['name'].lower()][pr] += 1

    main_of = {k: c.most_common(1)[0][0] for k, c in plays.items()}

    # pass two: write it onto every member record
    stats = collections.Counter()
    for fid in IDS:
        p = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        for b in d['bands']:
            for m in (b.get('members') or []):
                pr, rest, attrs = split_roles(m.get('roles'))
                # no instrument listed for this band, but we know what they play elsewhere
                if not pr and m['name'].lower() in main_of:
                    pr = main_of[m['name'].lower()]
                    m['instrument_source'] = 'their role in another band'
                m['instrument'] = pr
                m['instruments'] = rest
                m['member_attrs'] = attrs
                stats['members'] += 1
                if pr:
                    stats[pr] += 1
                else:
                    stats['(none)'] += 1
            b['instruments'] = sorted({m['instrument'] for m in (b.get('members') or [])
                                       if m.get('instrument')})
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

    print('member entries: %d | with a primary instrument: %d (%.0f%%)'
          % (stats['members'], stats['members'] - stats['(none)'],
             100 * (stats['members'] - stats['(none)']) / max(stats['members'], 1)))
    for k, v in stats.most_common():
        if k not in ('members', '(none)'):
            print('   %-13s %4d' % (k, v))

if __name__ == '__main__':
    main()
