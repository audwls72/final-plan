#!/usr/bin/env python3
"""(tools/texify.py) 노트 안의 유니코드/ASCII 수식을 LaTeX($…$, $$…$$)로 바꾼다.
코드 블록·인라인 코드·기존 $수식$·링크 주소·::: 줄·표 구분줄은 건드리지 않는다."""
import re, sys, json

_SK, _SV = "⁰¹²³⁴⁵⁶⁷⁸⁹ⁿⁱ⁺⁻⁼⁽⁾ᵀᵏᵐˣʸᵃᵇᶜᵈᵉᶠᵍʰʲˡᵒᵖʳˢᵗᵘᵛʷᶻ", "0123456789ni+-=()Tkmxyabcdefghjloprstuvwz"
assert len(_SK) == len(_SV)
SUP = dict(zip(_SK, _SV))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓₙᵢⱼₖₘₚₛₜᵤᵥₗ", "0123456789+-=()aeoxnijkmpstuvl"))
GREEK = {"α": "\\alpha", "β": "\\beta", "γ": "\\gamma", "δ": "\\delta", "ε": "\\varepsilon", "ζ": "\\zeta",
         "η": "\\eta", "θ": "\\theta", "ι": "\\iota", "κ": "\\kappa", "λ": "\\lambda", "μ": "\\mu", "ν": "\\nu",
         "ξ": "\\xi", "π": "\\pi", "ρ": "\\rho", "σ": "\\sigma", "τ": "\\tau", "υ": "\\upsilon", "φ": "\\varphi",
         "ϕ": "\\phi", "χ": "\\chi", "ψ": "\\psi", "ω": "\\omega", "Γ": "\\Gamma", "Δ": "\\Delta", "Θ": "\\Theta",
         "Λ": "\\Lambda", "Σ": "\\Sigma", "Φ": "\\Phi", "Ψ": "\\Psi", "Ω": "\\Omega", "Π": "\\Pi", "ϵ": "\\epsilon",
         "ϑ": "\\vartheta"}
SYM = {"∫": "\\int", "∬": "\\iint", "∭": "\\iiint", "∮": "\\oint", "∑": "\\sum", "∏": "\\prod", "∂": "\\partial",
       "∇": "\\nabla", "≤": "\\le", "≥": "\\ge", "≠": "\\ne", "≈": "\\approx", "±": "\\pm", "∓": "\\mp", "×": "\\times",
       "÷": "\\div", "·": "\\cdot", "⋅": "\\cdot", "∙": "\\cdot", "∞": "\\infty", "−": "-", "→": "\\to", "←": "\\leftarrow",
       "↦": "\\mapsto", "⇒": "\\Rightarrow", "⇔": "\\Leftrightarrow", "⟹": "\\Longrightarrow", "↔": "\\leftrightarrow",
       "∈": "\\in", "∉": "\\notin", "⊂": "\\subset", "⊆": "\\subseteq", "∪": "\\cup", "∩": "\\cap", "∅": "\\emptyset",
       "∀": "\\forall", "∃": "\\exists", "¬": "\\neg", "∧": "\\land", "∨": "\\lor", "⊢": "\\vdash", "⊨": "\\models",
       "ℝ": "\\mathbb{R}", "ℕ": "\\mathbb{N}", "ℤ": "\\mathbb{Z}", "ℂ": "\\mathbb{C}", "ℚ": "\\mathbb{Q}",
       "ħ": "\\hbar", "ℏ": "\\hbar", "°": "^\\circ ", "∘": "\\circ", "⟨": "\\langle", "⟩": "\\rangle", "‖": "\\Vert",
       "∝": "\\propto", "≡": "\\equiv", "≪": "\\ll", "≫": "\\gg", "∼": "\\sim", "≅": "\\cong", "⊥": "\\perp",
       "∥": "\\parallel", "′": "'", "″": "''", "⌊": "\\lfloor", "⌋": "\\rfloor", "⌈": "\\lceil", "⌉": "\\rceil",
       "⊕": "\\oplus", "⊗": "\\otimes", "ℓ": "\\ell", "Å": "\\text{Å}", "∠": "\\angle", "△": "\\triangle",
       "⋯": "\\cdots", "…": "\\ldots", "⋮": "\\vdots", "≜": "\\triangleq", "≔": "\\coloneqq", "⊤": "\\top",
       "⊑": "\\sqsubseteq", "≺": "\\prec", "⊃": "\\supset", "⊇": "\\supseteq", "∖": "\\setminus", "↑": "\\uparrow",
       "↓": "\\downarrow", "⇐": "\\Leftarrow", "∗": "*", "√": None, "∛": None}
FUNCS = {"sin", "cos", "tan", "cot", "sec", "csc", "log", "ln", "exp", "det", "lim", "max", "min", "sup", "inf",
         "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "gcd", "deg", "dim", "ker", "arg", "mod", "Pr", "lg"}
OPNAME = {"div", "curl", "grad", "rank", "tr", "sgn", "Vol", "Area", "proj", "span", "Re", "Im", "Var"}
TYPEKW = {"num", "bool", "Top", "Bottom"}
UNITS = {"B", "b", "nm", "mm", "cm", "km", "um", "pm", "fm", "eV", "keV", "MeV", "GeV", "Hz", "kHz", "MHz", "GHz", "ms",
         "ns", "us", "mol", "rad", "kg", "KB", "MB", "GB", "TB", "kB", "Kb", "C", "K", "m", "s", "J", "W", "V", "A",
         "T", "N", "Pa", "F", "H", "nF", "uF", "mA", "mV", "kV", "kW", "Wb", "lm", "cd", "dB", "sr", "L"}
STOP = {"is", "in", "of", "to", "or", "on", "if", "at", "as", "by", "be", "an", "it", "we", "no", "so", "do",
        "the", "and", "for", "not", "are", "with", "from", "that", "this", "then", "when", "where", "has", "all",
        "can", "per", "via", "vs", "let", "be", "its", "one", "two", "each", "any", "our"}

STRONG = set("".join(SUP) + "".join(SUB) + "".join(GREEK) + "".join(k for k in SYM if k not in "°′″…·") + "√∛")
MATHCH = set("".join(SUP) + "".join(SUB) + "".join(GREEK) + "".join(SYM) + "√∛")
ALLOWED = re.compile(r"[A-Za-z0-9 \t+\-/=<>()\[\]{},.^_'!:;?~%" + re.escape("".join(MATHCH)) + r"\\]")
LETTER = re.compile(r"[A-Za-z]")


def split_words(seg):
    """seg를 영어 단어(3자 이상 소문자, 불용어) 기준으로 끊어 조각 리스트로."""
    out, cur = [], ""
    for tok in re.split(r"([A-Za-z]+)", seg):
        if re.fullmatch(r"[A-Za-z]+", tok):
            low = tok.lower()
            word = (tok in STOP or low in STOP or
                    (len(tok) >= 3 and tok.islower() and tok not in FUNCS and tok not in OPNAME) or
                    (len(tok) >= 4 and tok[0].isupper() and tok[1:].islower() and tok not in OPNAME))
            if word:
                out.append(cur); out.append(None); cur = ""; continue
        cur += tok
    out.append(cur)
    return out


LEAD = set(" \t,.;:!?=<>≤≥≈≠×·→⇒⇔↔∈/^_*'") | {"\\"}
TRAIL = set(" \t,.;:!?=<>≤≥≈≠×·→⇒⇔↔∈+-−/*^_")


def trim(p):
    """앞뒤 군더더기 제거 + 괄호 짝 맞추기. (시작오프셋, 끝오프셋) 반환."""
    s, e = 0, len(p)
    changed = True
    while changed and s < e:
        changed = False
        while s < e and p[s] in LEAD: s += 1; changed = True
        while e > s and p[e - 1] in TRAIL: e -= 1; changed = True
        # 괄호 짝
        st = []
        cut_s, cut_e = None, None
        for i in range(s, e):
            c = p[i]
            if c in "([{⟨":
                st.append(i)
            elif c in ")]}⟩":
                if st: st.pop()
                elif cut_s is None and cut_e is None:
                    if all(ch in TRAIL or ch in ")]}⟩" for ch in p[i:e]): cut_e = i   # 끝쪽 → 앞에서 자름
                    else: cut_s = i + 1  # 앞쪽 → 그 뒤부터
        if cut_e is not None:
            e = cut_e; changed = True; continue
        if cut_s is not None:
            s = cut_s; changed = True; continue
        if st:
            if st[0] == s: s = st[0] + 1
            else: e = st[0]
            changed = True; continue
    return s, e


BIGO = re.compile(r"(?<![A-Za-z])[OΘΩo]\([^()]*(\([^()]*\))?[^()]*\)")


def is_math(p):
    if not re.search(r"[A-Za-z0-9" + re.escape("".join(GREEK)) + "ℝℏħ]", p): return False
    if any(c in STRONG for c in p): return True
    if BIGO.search(p): return True
    if re.search(r"[0-9]\s?°", p): return True
    if re.fullmatch(r"[0-9\s+\-−/×·()=.]+", p) and "=" in p and re.search(r"[0-9]\s*[+\-−/×·]\s*[0-9(]", p) and re.search(r"[0-9)]\s*=\s*[0-9(\-−]", p): return True
    if re.search(r"[A-Za-z0-9)\]}][_^][A-Za-z0-9{(]", p): return True
    if re.search(r"[=<>]", p) and re.search(r"[A-Za-z]", p) and not re.search(r"[A-Za-z]{3,}\s*=\s*[A-Za-z]{3,}", p):
        # 등식: 좌우에 피연산자, 영어 단어 아님
        if re.fullmatch(r"[\sA-Za-z0-9+\-*/=<>()\[\]{},.^_'′″]+", p) and re.search(r"[\w′)]\s*[=<>]+\s*[\w(\-]", p):
            words = re.findall(r"[A-Za-z]{2,}", p)
            if all(w in FUNCS or w in OPNAME or w.isupper() or len(w) <= 2 for w in words):
                return True
    return False


def _conv_seg(seg):
    toks = re.split(r"([A-Za-z]+)", seg)
    cur, parts = "", []
    for tok in toks:
        if re.fullmatch(r"[A-Za-z]+", tok):
            low = tok.lower()
            nxt = seg[seg.find(tok) + len(tok): seg.find(tok) + len(tok) + 1]
            word = (tok in STOP or low in STOP or
                    (len(tok) >= 3 and tok.islower() and tok not in FUNCS and tok not in OPNAME and tok not in UNITS and tok not in TYPEKW and nxt != "(") or
                    (len(tok) >= 4 and tok[0].isupper() and tok[1:].islower() and tok not in OPNAME and tok not in TYPEKW))
            if word:
                parts.append(("m", cur)); parts.append(("w", tok)); cur = ""; continue
        cur += tok
    parts.append(("m", cur))
    rebuilt = ""
    for kind, p in parts:
        if kind == "w" or not p:
            rebuilt += p; continue
        s, e = trim(p)
        core = p[s:e]
        if core and is_math(core) and "\x00" not in core:
            if core[0] == "(" and find_group(core, 0, "(", ")") == len(core) - 1 and re.search(r"[=<>≤≥≈]", core):
                rebuilt += p[:s] + "($" + tex(core[1:-1]) + "$)" + p[e:]
            else:
                rebuilt += p[:s] + "$" + tex(core) + "$" + p[e:]
        else:
            rebuilt += p
    return rebuilt


def find_group(s, i, open_, close_):
    d = 0
    for j in range(i, len(s)):
        if s[j] == open_: d += 1
        elif s[j] == close_:
            d -= 1
            if d == 0: return j
    return -1


def tex(p):
    """수식 조각 p를 LaTeX 문자열로."""
    out = []
    i, n = 0, len(p)
    prev_word = False  # 직전 토큰이 글자/숫자 → 공백 사이엔 \, 삽입
    pend_space = False

    def emit(t, word):
        nonlocal prev_word, pend_space
        if pend_space and prev_word and word and not t.startswith(("\\sin", "\\cos", "\\tan", "\\log", "\\ln", "\\exp", "\\det", "\\lim", "\\max", "\\min", "\\,")) and not re.search(r"\\(sin|cos|tan|log|ln|exp|det|lim|max|min) $", out[-1] if out else ""):
            out.append("\\,")
        elif out and out[-1] and (out[-1][-1].isalpha() and t[:1].isalpha() and out[-1].rstrip()[-1:].isalpha()
                                  and out[-1].lstrip().startswith("\\")):
            out.append(" ")
        out.append(t); prev_word = word; pend_space = False

    while i < n:
        c = p[i]
        if c in " \t":
            pend_space = True; i += 1; continue
        if c in SUP:
            j = i
            while j < n and p[j] in SUP: j += 1
            emit("^{" + tex("".join(SUP[x] for x in p[i:j]).replace("-", "−")) + "}", True); i = j; continue
        if c in SUB:
            j = i
            while j < n and p[j] in SUB: j += 1
            emit("_{" + tex("".join(SUB[x] for x in p[i:j]).replace("-", "−")) + "}", True); i = j; continue
        if c in "^_" and i + 1 < n:
            if p[i + 1] == "{":
                j = find_group(p, i + 1, "{", "}")
                if j > 0:
                    emit(c + "{" + tex(p[i + 2:j]) + "}", True); i = j + 1; continue
            if p[i + 1] == "(":
                j = find_group(p, i + 1, "(", ")")
                if j > 0:
                    emit(c + "{" + tex(p[i + 2:j]) + "}", True); i = j + 1; continue
            m = re.match(r"[A-Za-z]+|[0-9]+|-?[0-9]+|.", p[i + 1:])
            tok = m.group(0)
            if re.fullmatch(r"[A-Za-z]{3,}|[A-Z][A-Za-z]+", tok) and tok not in FUNCS:
                emit(c + "{\\mathrm{" + tok + "}}", True)
            else:
                emit(c + "{" + tex(tok) + "}", True)
            i += 1 + len(tok); continue
        if c in "√∛":
            root = "\\sqrt" if c == "√" else "\\sqrt[3]"
            j = i + 1
            if j < n and p[j] == "(":
                k = find_group(p, j, "(", ")")
                if k > 0:
                    emit(root + "{" + tex(p[j + 1:k]) + "}", True); i = k + 1; continue
            if j < n and p[j] == "{":
                k = find_group(p, j, "{", "}")
                if k > 0:
                    emit(root + "{" + tex(p[j + 1:k]) + "}", True); i = k + 1; continue
            m = re.match(r"[0-9.]+|[A-Za-z]|[" + "".join(GREEK) + "]", p[j:])
            if m:
                emit(root + "{" + tex(m.group(0)) + "}", True); i = j + len(m.group(0)); continue
            emit(root + "{}", True); i += 1; continue
        if c in GREEK:
            t = GREEK[c]
            m = re.match(r"[0-9]+", p[i + 1:])
            if m:
                emit(t + "_{" + m.group(0) + "}", True); i += 1 + len(m.group(0)); continue
            emit(t, True); i += 1; continue
        if c in SYM:
            emit(SYM[c], c in "ℝℕℤℂℚħℏ∞∅ℓ"); i += 1; continue
        mh = re.match(r"0x[0-9a-fA-F]+", p[i:])
        if mh:
            emit("\\mathtt{" + mh.group(0) + "}", True); i += len(mh.group(0)); continue
        if c.isdigit() or (c == "." and i + 1 < n and p[i + 1].isdigit()):
            m = re.match(r"[0-9]*\.?[0-9]+(,[0-9]{3})*(\.[0-9]+)?", p[i:])
            num = m.group(0)
            emit(num.replace(",", "{,}"), True); i += len(num); continue
        if c.isalpha() and c.isascii():
            m = re.match(r"[A-Za-z]+", p[i:]); w = m.group(0)
            j = i + len(w)
            if w in UNITS and out and re.search(r"[0-9]\s*$|\\circ\s*$", out[-1]) and (len(w) > 1 or not re.search(r"(lg|log|ln)", "".join(out[-3:]))):
                emit("\\,\\mathrm{" + w + "}", True); i = j; continue
            if w in TYPEKW:
                emit("\\mathtt{" + w + "}", True); i = j; continue
            if w in FUNCS:
                emit("\\" + w + " ", True)
            elif w in OPNAME or (len(w) >= 2 and (w.isupper() or w[0].isupper())):
                if len(w) == 2 and w[0].isupper() and w[1].islower() is False and False:
                    pass
                emit("\\mathrm{" + w + "}", True)
            elif len(w) == 1:
                d = re.match(r"[0-9]+", p[j:])
                if d and not (i > 0 and p[i - 1].isdigit()):
                    emit(w + "_{" + d.group(0) + "}", True); i = j + len(d.group(0)); continue
                emit(w, True)
            elif len(w) >= 3 and j < n and p[j] == "(":
                emit("\\operatorname{" + w + "}", True)
            else:
                emit(w, True)
            i = j; continue
        if c == "," and i + 1 < n and p[i + 1] == " ":
            emit(",\\ ", False); i += 2
            while i < n and p[i] == " ": i += 1
            continue
        if c == "%":
            emit("\\bmod ", False); i += 1; continue
        if c == "~":
            emit("\\sim ", False); i += 1; continue
        if c == "*":
            emit("\\ast ", False); i += 1; continue
        if c in "{}":
            emit("\\" + c, False); i += 1; continue
        if c == "\\":
            m = re.match(r"\\[A-Za-z]+|\\.", p[i:])
            if not m:
                emit("\\backslash ", False); i += 1; continue
            emit(m.group(0), False); i += len(m.group(0)); continue
        if c == "|":
            emit("\\vert ", False); i += 1; continue
        emit(c, c in ")]'"); i += 1
    s = "".join(out)
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("- -", "--")
    return s


PREFIX = re.compile(r"^(\s*(?:#{1,6}\s+|>\s*|(?:[-*+]|\d+[.)])\s+|\[[ xX]\]\s+|\*\*\(?\d+\)?\*\*\s*|\(\d+\)\s+)*)")


def conv_text(text, display_ok=False):
    pre = PREFIX.match(text).group(1)
    return pre + _conv(text[len(pre):])


def _conv(text):
    keep = []
    def K(m):
        keep.append(m.group(0)); return f"\x00{len(keep)-1}\x00"
    t = re.sub(r"`+[^`\n]*?`+", K, text)
    t = re.sub(r"\$\$.*?\$\$|(?<![\\$])\$(?!\$)[^$\n]+?(?<!\\)\$", K, t)
    t = re.sub(r"\]\([^)]*\)", K, t)
    t = re.sub(r"</?[A-Za-z][^<>\n]*>", K, t)
    t = re.sub(r"https?://\S+", K, t)
    t = re.sub(r"\b[A-Za-z0-9]+(?:_[A-Za-z0-9]+){2,}\b|\b[A-Za-z][A-Za-z0-9]{2,}_[A-Za-z0-9]{2,}\b|\b[a-z]+[A-Z][A-Za-z]*\b|\b[A-Z]+_[A-Z0-9_]{2,}\b|\b[A-Z][a-z]+[A-Z]\w*\b|\b\w+\.(?:c|h|o|s|so|a|txt|py|java|scala|md)\b|\b\w+\(\)", K, t)
    res, pos = [], 0
    for m in re.finditer(ALLOWED.pattern + "+", t):
        seg = m.group(0)
        res.append(t[pos:m.start()]); pos = m.end()
        SEP = r"((?<=[^\s:]):(?=\s)|(?<=[^\s.0-9])\.(?=\s)|(?<=[0-9])\.(?=\s+[A-Za-z(]))"
        bits = re.split(SEP, seg)
        res.append("".join(_conv_seg(x) if k_ % 2 == 0 else x for k_, x in enumerate(bits))); continue
        pieces = split_words(seg)
        # pieces: 문자열 / None(=단어). 원문 위치를 따라가며 재조립
        rebuilt, cursor = "", 0
        toks = re.split(r"([A-Za-z]+)", seg)
        # 다시 단순하게: split_words와 같은 규칙으로 순회
        cur = ""
        parts = []
        for tok in toks:
            if re.fullmatch(r"[A-Za-z]+", tok):
                low = tok.lower()
                word = (tok in STOP or low in STOP or
                        (len(tok) >= 3 and tok.islower() and tok not in FUNCS and tok not in OPNAME) or
                        (len(tok) >= 4 and tok[0].isupper() and tok[1:].islower() and tok not in OPNAME))
                if word:
                    parts.append(("m", cur)); parts.append(("w", tok)); cur = ""; continue
            cur += tok
        parts.append(("m", cur))
        for kind, p in parts:
            if kind == "w" or not p:
                rebuilt += p; continue
            s, e = trim(p)
            core = p[s:e]
            if core and is_math(core) and "\x00" not in core:
                rebuilt += p[:s] + "$" + tex(core) + "$" + p[e:]
            else:
                rebuilt += p
        res.append(rebuilt)
    res.append(t[pos:])
    t = "".join(res)
    t = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], t)
    return t


TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")


def convert(src):
    for _ in range(5):
        new = _convert_once(src)
        if new == src: break
        src = new
    return src


def _convert_once(src):
    lines = src.split("\n")
    out, in_code, fence, in_disp = [], False, "", False
    prev_blank = True
    for idx, ln in enumerate(lines):
        m = re.match(r"^\s*(`{3,}|~{3,})", ln)
        if m:
            if not in_code: in_code, fence = True, m.group(1)
            elif m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence): in_code = False
            out.append(ln); prev_blank = False; continue
        if ln.count("$$") % 2 == 1:
            in_disp = not in_disp; out.append(ln); continue
        if in_disp:
            out.append(ln); continue
        if in_code or TABLE_SEP.match(ln) or ln.lstrip().startswith(":::") or ln.startswith("    "):
            out.append(ln); prev_blank = not ln.strip(); continue
        # 2칸 들여쓴 '식 한 줄' 블록 → $$ $$
        if re.match(r"^  \S", ln) and not re.match(r"^  (([-*+]|\d+\.)\s|\|)", ln):
            body = ln.strip()
            c = conv_text(body)
            if re.fullmatch(r"\$[^$]+\$[.,]?", c):
                out.append("$$" + c.rstrip(".,")[1:-1] + "$$"); prev_blank = False; continue
            out.append("  " + c); prev_blank = False; continue
        out.append(conv_text(ln)); prev_blank = not ln.strip()
    return "\n".join(out)


if __name__ == "__main__":
    import glob, os
    for f in sys.argv[1:]:
        s = open(f, encoding="utf-8").read()
        open(f.replace("/orig/", "/out/"), "w", encoding="utf-8").write(convert(s))
