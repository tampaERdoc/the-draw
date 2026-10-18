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
plain = open(os.path.join(root, 'private', fid + '.json'), 'rb').read()
json.loads(plain)  # validate
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
