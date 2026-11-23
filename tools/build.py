#!/usr/bin/env python3
"""Encrypt/decrypt the study-site payload.

  python3 build.py encrypt content.json data.enc  PASSWORD
  python3 build.py decrypt data.enc content.json  PASSWORD

AES-256-GCM, key = PBKDF2-HMAC-SHA256(password, salt, 250000). Matches the WebCrypto code in index.html.
"""
import base64, json, os, sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITER = 250_000

def key(pw, salt):
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(pw.encode())

def encrypt(src, dst, pw):
    data = json.dumps(json.load(open(src, encoding="utf-8")), ensure_ascii=False).encode()
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(key(pw, salt)).encrypt(iv, data, None)
    b = lambda x: base64.b64encode(x).decode()
    json.dump({"v": 1, "iter": ITER, "salt": b(salt), "iv": b(iv), "ct": b(ct)}, open(dst, "w"))

def decrypt(src, dst, pw):
    e = json.load(open(src))
    d = lambda k: base64.b64decode(e[k])
    data = AESGCM(key(pw, d("salt"))).decrypt(d("iv"), d("ct"), None)
    json.dump(json.loads(data), open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    mode, src, dst, pw = sys.argv[1:5]
    {"encrypt": encrypt, "decrypt": decrypt}[mode](src, dst, pw)
    print(mode, "ok")
