#!/usr/bin/env python3
"""노트 MD를 사이트·PDF에 올리기 전에 자동으로 고치는 필터 (원본 노트는 그대로 둔다).

1. 표 바로 윗줄이 문장이면 빈 줄을 넣는다 (pandoc·marked가 표로 인식하게).
2. **굵게** → <strong>굵게</strong>  (닫는 ** 앞이 ')' 이고 뒤가 한글이면 CommonMark가 굵게 처리를 못 함).
3. LaTeX가 든 인라인 수식의 안쪽 앞뒤 공백 제거: `$\\lambda = $` → `$\\lambda =$` (닫는 $ 앞 공백이면 수식이 안 됨).
   백슬래시가 없는 `$`는 건드리지 않는다 (달러 금액 보호).
코드 블록(```)과 인라인 코드(`...`) 안은 절대 건드리지 않는다.

usage: python3 tools/mdfix.py in.md [out.md]   (out 생략 시 덮어씀)
"""
import re, sys

TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")

def _blank_before_tables(lines):
    out = []
    for i, ln in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if ln.lstrip().startswith("|") and TABLE_SEP.match(nxt) and "|" in nxt:
            prev = out[-1] if out else ""
            if prev.strip() and not prev.lstrip().startswith("|"):
                out.append("")
        out.append(ln)
    return out

BOLD = re.compile(r"(?<!\*)\*\*(?!\*)(?=\s*\S)(.+?)(?<=\S)\s*(?<!\*)\*\*(?!\*)")
MATH = re.compile(r"(?<![\$\\])\$(?!\$)([^$\n]+?)(?<![\\])\$(?!\$)")

def _inline(text):
    # protect inline code
    codes = []
    def keep(m):
        codes.append(m.group(0)); return f"\x00C{len(codes)-1}\x00"
    text = re.sub(r"`+[^`\n]*?`+", keep, text)
    # math: trim inner spaces only when it looks like LaTeX
    maths = []
    def mfix(m):
        inner = m.group(1)
        if "\\" in inner or re.search(r"[\^_{}]", inner) or re.fullmatch(r"\s*[=≈<>+\-−×·]+\s*", inner) \
                or (re.match(r"\s*[=≈<>]|.*[=≈<>+]\s*$", inner) and not re.search(r"\d{1,3},\d{3}", inner)):
            inner = inner.strip()
        maths.append("$" + inner + "$"); return f"\x00M{len(maths)-1}\x00"
    text = MATH.sub(mfix, text)
    # 짝이 안 맞는 '***굵게**' (여는 별 3개, 닫는 별 2개) → '**굵게**'
    if text.count("***") == 1 and not re.search(r"\*\*\*\s*$", text):
        text = text.replace("***", "**", 1)
    text = BOLD.sub(lambda m: "<strong>" + m.group(1).strip() + "</strong>", text)
    text = re.sub(r"\x00M(\d+)\x00", lambda m: maths[int(m.group(1))], text)
    text = re.sub(r"\x00C(\d+)\x00", lambda m: codes[int(m.group(1))], text)
    return text

def fix(src):
    lines = src.split("\n")
    out, buf, in_code, fence = [], [], False, ""
    def flush():
        if buf:
            out.extend(_inline(l) for l in _blank_before_tables(buf)); buf.clear()
    for ln in lines:
        m = re.match(r"^\s*(`{3,}|~{3,})", ln)
        if m and (not in_code or m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence)):
            if not in_code:
                flush(); in_code, fence = True, m.group(1)
            else:
                in_code = False
            out.append(ln); continue
        (out if in_code else buf).append(ln)
    flush()
    return "\n".join(out)

if __name__ == "__main__":
    s = open(sys.argv[1], encoding="utf-8").read()
    open(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1], "w", encoding="utf-8").write(fix(s))
