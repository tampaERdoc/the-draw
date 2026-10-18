#!/usr/bin/env python3
"""Encrypt a festival dataset for the password-protected site.

Usage:  python3 tools/encrypt.py <fest-id> "<password>"
Reads   private/<fest-id>.json   (plaintext, never committed — private/ is git-ignored)
Writes  data/<fest-id>.enc.js    (AES-256-GCM, key from PBKDF2-SHA256)
Use the SAME password for every festival so one unlock opens them all.

All datasets share ONE salt, kept in private/salt.bin. That is deliberate: the browser
derives the PBKDF2 key once (310,000 iterations is about a third of a second) and reuses
it for every dataset. Deriving per file was fine at four datasets and unusable at
twenty-seven. One shared salt still defeats precomputed-rainbow attacks, which is what a
salt is for; each dataset keeps its own random IV, which is the part that must never repeat.
"""
import sys, os, json, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
ITER = 310000
fid, pw = sys.argv[1], sys.argv[2]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# The private file stays indented and readable; what ships is compact. Indentation
# is perhaps a fifth of the plaintext and encrypts into real bytes over the wire.
raw = open(os.path.join(root, 'private', fid + '.json'), 'rb').read()
d = json.loads(raw)

# Two kinds of pure redundancy dominated the payload, so they are squeezed out here
# rather than in the private file, which stays full-fidelity for debugging.
#   members[].mbid  - 36 characters per member that the page never reads (37% of one set)
#   earnings_caveat - the same long sentence repeated on every band (15% of one set)
caveats = {}
for b in d.get('bands', []):
    for m in (b.get('members') or []):
        m.pop('mbid', None)
    c = b.get('earnings_caveat')
    if c:
        caveats[c] = caveats.get(c, 0) + 1
if caveats:
    common = max(caveats, key=caveats.get)
    if caveats[common] > 3:
        d['earningsCaveat'] = common          # the page falls back to this
        for b in d.get('bands', []):
            if b.get('earnings_caveat') == common:
                b['earnings_caveat'] = ''
plain = json.dumps(d, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
saltfile = os.path.join(root, 'private', 'salt.bin')
if not os.path.exists(saltfile):
    with open(saltfile, 'wb') as f:
        f.write(os.urandom(16))
salt = open(saltfile, 'rb').read()
iv = os.urandom(12)          # never reused: a repeated IV under one key breaks AES-GCM
key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw.encode())
ct = AESGCM(key).encrypt(iv, plain, None)
b = lambda x: base64.b64encode(x).decode()
out = {"v": 1, "iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct)}
with open(os.path.join(root, 'data', fid + '.enc.js'), 'w') as f:
    f.write('(window.FESTS_ENC=window.FESTS_ENC||{})[%s]=%s;\n' % (json.dumps(fid), json.dumps(out)))
print('wrote data/%s.enc.js (%d bytes plaintext)' % (fid, len(plain)))
