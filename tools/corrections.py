#!/usr/bin/env python3
"""Corrections that must survive every rebuild, and the audit that finds more.

Two failure modes put wrong numbers on the site, and both look like data:

1. A MusicBrainz url-rel can point at an ABANDONED Spotify profile. Right band,
   dead profile. Refused reads 12 monthly listeners that way, Godspeed You! Black
   Emperor 13. The pages really do say that, so nothing downstream catches it.
2. A MusicBrainz url-rel can point at the wrong Instagram account entirely, or at a
   member's personal account.

Where the figure is demonstrably impossible for that band it is removed and the record
says why. Where it is merely suspect it is flagged, not deleted - the tell is an
Instagram following wildly out of proportion to monthly listeners, which is a hint,
not a verdict.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Figures removed outright: these artists are far too large for the number shown, so the
# linked profile cannot be theirs. Removing beats publishing a number we know is wrong.
BAD_SPOTIFY = {
    'Refused':                     'MusicBrainz links an abandoned Spotify profile reading 12 monthly listeners. Figure removed rather than published.',
    'Godspeed You! Black Emperor': 'MusicBrainz links an abandoned Spotify profile reading 13 monthly listeners. Figure removed rather than published.',
    'H2O':                         'Linked Spotify profile reads 164 monthly listeners against 11,968 Instagram followers. Figure removed as implausible for this band.',
}
BAD_INSTAGRAM = {
    'Motionless In White': 'MusicBrainz handle @miwband reads 33,720 with no display name - not this band’s main account. Figure removed.',
    'Wend':                'MusicBrainz handle @wordproof_band bears no relation to the band name. Figure removed.',
    'Smoker Dad':          'Handle @smokerdad displays as “Big Daddy Smokes” and is categorised Tobacco & Smoking. Identity unconfirmed, figure removed.',
    'Mayday Parade':       'MusicBrainz handle @maydayparadeband resolves to an account named “saved” with 0 posts and 72 followers. Not this band. Figure removed.',
    'Hause Plants':        'Handle @hauseplants displays as “gui”, a personal account unrelated to the band. Figure removed.',
}

# Figures kept but marked uncertain: single-sourced, or two trackers disagreeing past the
# 8% tolerance. Deleting these would discard a real reading; publishing them silently
# would overstate what we know. So they stay, carrying the doubt on the record.
DOUBTFUL = {
    'The 2 Lips':     'Single-sourced at 107,464, high for this band\u2019s profile. Unverified.',
    'Haute & Freddy': 'Social Blade 262,140 against HypeAuditor 194,338 \u2014 26% apart. Uncertain.',
    'Hail The Sun':   'Social Blade 125,276 against HypeAuditor 114,214 \u2014 8.8% apart, past tolerance.',
    'Aubory Bugg':    'Social Blade 155,708 against HypeAuditor 116,998 \u2014 25% apart. Uncertain.',
    'Womack Sisters': 'Social Blade 295,113 against HypeAuditor 233,283 \u2014 26% apart. Uncertain.',
    'Thee Sinseers':  'Social Blade 188,405 against HypeAuditor 164,019 \u2014 15% apart. Uncertain.',
}

def audit(b):
    """Instagram out of all proportion to Spotify: a hint that one of them is wrong."""
    ig, sp = b.get('instagram_followers'), b.get('spotify_listeners')
    if isinstance(ig, (int, float)) and isinstance(sp, (int, float)) and sp:
        if ig > sp * 20 and ig > 2000:
            return ('Instagram following is %dx the monthly listeners, which usually means one '
                    'of the two linked profiles is not this band. Both figures unverified.'
                    % round(ig / sp))
    return ''

def main():
    removed = flagged = 0
    for fid in IDS:
        p = os.path.join(ROOT, 'private', fid + '.json')
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        for b in d.get('bands', []):
            note = BAD_SPOTIFY.get(b.get('name'))
            if note and b.get('spotify_listeners') is not None:
                b['spotify_listeners'] = None
                b['spotify_verification'] = 'figure withdrawn'
                b['flags'] = (b.get('flags', '') + ' ' + note).strip()
                b['grade'] = ''; b['size_vs_sincere_engineer'] = None; b['grade_score'] = None
                removed += 1
            note = BAD_INSTAGRAM.get(b.get('name'))
            if note and b.get('instagram_followers') is not None:
                b['instagram_followers'] = None
                b['ig_socialblade'] = None
                b['flags'] = (b.get('flags', '') + ' ' + note).strip()
                b['grade'] = ''; b['size_vs_sincere_engineer'] = None; b['grade_score'] = None
                removed += 1
            note = DOUBTFUL.get(b.get('name'))
            if note and note not in (b.get('flags') or ''):
                b['flags'] = (b.get('flags', '') + ' ' + note).strip()
                flagged += 1
            a = audit(b)
            if a and a not in (b.get('flags') or ''):
                b['flags'] = (b.get('flags', '') + ' ' + a).strip()
                flagged += 1
        json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print('corrections: %d figures withdrawn, %d records flagged for review' % (removed, flagged))

if __name__ == '__main__':
    main()
