#!/usr/bin/env python3
"""One command that takes an edit all the way to thedraw.tampaerdoc.com.

    python3 tools/deploy.py "what changed"

The site reads data/<id>.enc.js, NOT private/<id>.json. Editing the private
JSON and pushing therefore publishes nothing, and editing index.html without
re-encrypting publishes a new page over stale data. That mismatch is silent
and it is the failure this script exists to prevent: it always runs the whole
chain in order, whichever file you touched.

  1. tools/members.py   attach line-ups, member_names, plays_in
  2. tools/copy.py      headlines and pitches -> then calls tools/redact.py,
                        which re-applies the removals a rebuild would undo
                        (Sulynn Hago's earnings estimate, above all)
  3. tools/encrypt.py   re-encrypt all four datasets with the site password
  4. git commit + push  GitHub Pages redeploys on its own, live in ~1 minute

GoDaddy needs nothing. The DNS record is set once and does not change when
the site's content does; it only matters if the domain itself changes.
Do not delete the CNAME file — removing it un-sets the custom domain and
sends the github.io URL redirecting at a name Pages no longer answers for.
"""
import json, os, sys, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datasets import IDS
PASSWORD = 'doghouse'
ATTR = ('Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>')

def run(*cmd, **kw):
    r = subprocess.run(cmd, cwd=ROOT, **kw)
    if r.returncode:
        sys.exit('FAILED: %s' % ' '.join(cmd))
    return r

def check_redactions():
    """Never ship an earnings figure that was taken down on request."""
    bad = []
    for fid in IDS:
        for b in json.load(open(os.path.join(ROOT, 'private', fid + '.json'), encoding='utf-8'))['bands']:
            if b.get('name') == 'Sulynn Hago' and (b.get('est_income_top_member') or b.get('earnings_members')):
                bad.append(fid)
    if bad:
        sys.exit('REFUSING TO PUSH: Sulynn Hago earnings present in %s' % ', '.join(bad))

def main():
    msg = ' '.join(sys.argv[1:]).strip()
    if not msg:
        sys.exit('usage: python3 tools/deploy.py "what changed"')

    print('1/4 line-ups');   run(sys.executable, 'tools/members.py')
    run(sys.executable, 'tools/discogs_members.py')
    run(sys.executable, 'tools/discogs_instruments.py')
    run(sys.executable, 'tools/bio_instruments.py')
    run(sys.executable, 'tools/hand_members.py')
    run(sys.executable, 'tools/instruments.py', stdout=subprocess.DEVNULL)
    print('2/4 copy + redactions'); run(sys.executable, 'tools/copy.py')
    run(sys.executable, 'tools/corrections.py')
    check_redactions()
    print('3/4 encrypting')
    for fid in IDS:
        run(sys.executable, 'tools/encrypt.py', fid, PASSWORD, stdout=subprocess.DEVNULL)
        print('    ', fid)

    # stamp the build so a cached browser can tell it is behind and reload itself
    import time as _t
    build = _t.strftime('%Y%m%d-%H%M%S')
    with open(os.path.join(ROOT, 'build.txt'), 'w') as f:
        f.write(build + '\n')
    idx = os.path.join(ROOT, 'index.html')
    html = open(idx, encoding='utf-8').read()
    import re as _re
    html = _re.sub(r"const BUILD='[^']*'", "const BUILD='%s'" % build, html, count=1)
    open(idx, 'w', encoding='utf-8').write(html)
    print('     build', build)

    if not os.path.exists(os.path.join(ROOT, 'CNAME')):
        sys.exit('REFUSING TO PUSH: CNAME is missing — the custom domain would break.')

    print('4/4 pushing')
    run('git', 'add', '-A')
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=ROOT).returncode == 0:
        print('nothing changed; nothing to push'); return
    run('git', '-c', 'user.name=Jason Wilson', '-c', 'user.email=tampaerdoc@gmail.com',
        'commit', '-q', '-m', msg + '\n\n' + ATTR)
    run('git', 'push', '-q', 'origin', 'main')
    print('\nlive in about a minute: https://thedraw.tampaerdoc.com')

if __name__ == '__main__':
    main()
