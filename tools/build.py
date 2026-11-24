#!/usr/bin/env python3
"""FINAL QUEST site tool. All content is AES-256-GCM encrypted; key = PBKDF2-HMAC-SHA256(password, salt, 250000).
One salt (stored in data.enc) is shared by data.enc and every notes/<sid>.enc so one key opens everything.

  python3 tools/build.py decrypt  data.enc /tmp/content.json PW     # main content -> plaintext JSON
  python3 tools/build.py encrypt  /tmp/content.json data.enc PW     # plaintext JSON -> data.enc (keeps existing salt)
  python3 tools/build.py notes    SID /tmp/notes_dir PW             # add/replace notes: every <chapterId>.md in dir
  python3 tools/build.py rmnote   SID CHAPTER_ID PW                 # remove one note
  python3 tools/build.py pdf      SID FILE.pdf "제목" PW              # add/replace a PDF (id = file name without .pdf)
  python3 tools/build.py rmpdf    SID PDF_ID PW                     # remove a PDF
  python3 tools/build.py rekey    OLD_PW NEW_PW                     # change password (new salt for everything)

Run from the repo root. Never commit plaintext.
"""
import re
import base64, glob, json, os, sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

ITER = 250_000
B = lambda x: base64.b64encode(x).decode()
U = base64.b64decode

def key(pw, salt):
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(pw.encode())

def seal(obj, k, salt):
    iv = os.urandom(12)
    ct = AESGCM(k).encrypt(iv, json.dumps(obj, ensure_ascii=False).encode(), None)
    return {"v": 1, "iter": ITER, "salt": B(salt), "iv": B(iv), "ct": B(ct)}

def unseal(path, k):
    e = json.load(open(path))
    return json.loads(AESGCM(k).decrypt(U(e["iv"]), U(e["ct"]), None))

def salt_of(path="data.enc"):
    return U(json.load(open(path))["salt"])

def write(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    json.dump(obj, open(path, "w"))

def decrypt(src, dst, pw):
    json.dump(unseal(src, key(pw, salt_of(src))), open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def encrypt(src, dst, pw):
    salt = salt_of(dst) if os.path.exists(dst) else os.urandom(16)
    write(dst, seal(json.load(open(src, encoding="utf-8")), key(pw, salt), salt))

def notes(sid, mddir, pw):
    salt = salt_of(); k = key(pw, salt)
    path = f"notes/{sid}.enc"
    cur = unseal(path, k) if os.path.exists(path) else {}
    for f in sorted(glob.glob(os.path.join(mddir, "*.md"))):
        cur[os.path.splitext(os.path.basename(f))[0]] = open(f, encoding="utf-8").read()
    _save_notes(sid, cur, k, salt)

def rmnote(sid, cid, pw):
    salt = salt_of(); k = key(pw, salt)
    cur = unseal(f"notes/{sid}.enc", k); cur.pop(cid, None)
    _save_notes(sid, cur, k, salt)

def _save_notes(sid, cur, k, salt):
    write(f"notes/{sid}.enc", seal(cur, k, salt))
    data = unseal("data.enc", k)
    data.setdefault("notesAvailable", {})[sid] = sorted(cur)
    data.setdefault("notesVer", {})[sid] = os.urandom(4).hex()
    data.pop("notes", None)
    write("data.enc", seal(data, k, salt))
    print(sid, "notes:", sorted(cur))

# PDFs: raw binary file = iv(12) || AES-GCM(ciphertext+tag)
def pdf(sid, path, title, pw):
    salt = salt_of(); k = key(pw, salt)
    pid = os.path.splitext(os.path.basename(path))[0]
    raw = open(path, "rb").read()
    out = f"pdfs/{sid}/{pid}.bin"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    iv = os.urandom(12)
    open(out, "wb").write(iv + AESGCM(k).encrypt(iv, raw, None))
    data = unseal("data.enc", k)
    lst = [x for x in data.setdefault("pdfs", {}).setdefault(sid, []) if x["id"] != pid]
    lst.append({"id": pid, "title": title, "size": len(raw), "ver": os.urandom(4).hex()})
    data["pdfs"][sid] = sorted(lst, key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", x["id"])])
    write("data.enc", seal(data, k, salt))
    print(sid, "pdf:", pid, f"{len(raw)/1e6:.1f}MB")

def rmpdf(sid, pid, pw):
    salt = salt_of(); k = key(pw, salt)
    p = f"pdfs/{sid}/{pid}.bin"
    if os.path.exists(p): os.remove(p)
    data = unseal("data.enc", k)
    data.setdefault("pdfs", {})[sid] = [x for x in data["pdfs"].get(sid, []) if x["id"] != pid]
    write("data.enc", seal(data, k, salt))

def rekey(old, new):
    ok = key(old, salt_of()); salt = os.urandom(16); nk = key(new, salt)
    for p in ["data.enc"] + glob.glob("notes/*.enc"):
        write(p, seal(unseal(p, ok), nk, salt))
    for p in glob.glob("pdfs/*/*.bin"):
        b = open(p, "rb").read(); raw = AESGCM(ok).decrypt(b[:12], b[12:], None)
        iv = os.urandom(12); open(p, "wb").write(iv + AESGCM(nk).encrypt(iv, raw, None))

if __name__ == "__main__":
    cmd, *a = sys.argv[1:]
    {"decrypt": decrypt, "encrypt": encrypt, "notes": notes, "rmnote": rmnote, "pdf": pdf, "rmpdf": rmpdf, "rekey": rekey}[cmd](*a)
    print(cmd, "ok")
