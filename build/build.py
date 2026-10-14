#!/usr/bin/env python3
"""Builds every post from content/day-NN.txt so all 30 share one format.

Usage: python3 build/build.py [day ...]     (no args = all days)
Writes posts/day-NN/{carousel.html,carousel.pdf,caption.txt} and reports any slide that overflows.
"""
import html, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SERIES = "Microsoft Fabric · 30 Days"
AUTHOR = "Keshav Maheshwari"
ROLE = "Data Engineer | Databricks · AWS & Azure · Streaming · Applied AI"
TOTAL = 30
GUIDE = "Slides 1 to 4 cover the big picture. Slides 5 to 7 are where it gets practical. Slide 8 is the summary."
BASE_TAGS = "#MicrosoftFabric #DataEngineering"
BANNED = ["plain english", "for beginners", "explained simply", "dp-600", "ai-102", "microsoft certified", "certification exam"]


def parse(path):
    d, cap, in_cap = {}, [], False
    for line in path.read_text().splitlines():
        if in_cap:
            cap.append(line)
        elif line.strip() == "caption:":
            in_cap = True
        elif line.strip() and not line.startswith("#"):
            k, _, v = line.partition(":")
            d[k.strip()] = v.strip()
    d["caption"] = "\n".join(cap).strip()
    return d


def fmt(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r'<b class="w">\1</b>', s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"\^(.+?)\^", r'<span class="amberc">\1</span>', s)
    return s


def items(s):
    return [x.strip() for x in s.split("||") if x.strip()] if s else []


def kv(s):
    k, _, v = s.partition("::")
    return k.strip(), v.strip()


def rows_kv(lst, icon=None):
    out = []
    for i, it in enumerate(lst, 1):
        k, v = kv(it)
        ic = icon or str(i)
        out.append(f'<div class="row"><span class="ic">{ic}</span><span class="k">{fmt(k)}</span><span class="v">{fmt(v)}</span></div>')
    return "\n".join(out)


def rows_text(lst):
    return "\n".join(f'<div class="row"><span class="ic">{i}</span><span class="v">{fmt(t)}</span></div>' for i, t in enumerate(lst, 1))


def rows_col(lst):
    return "\n".join('<div class="row col"><span class="k">%s</span><span class="v">%s</span></div>' % tuple(map(fmt, kv(t))) for t in lst)


def slide(tag, body, amber=False):
    return f'<section class="slide">\n<span class="tag{" amber" if amber else ""}">{tag}</span>\n{body}\n</section>'


def build_html(n, d):
    s = []
    title = "<br>".join(fmt(x.strip()) for x in d["title"].split("|"))
    sub = "<br>".join(fmt(x.strip()) for x in d["sub"].split("|"))
    pills = "".join(f'<span class="pill">{fmt(p)}</span>' for p in items(d["pills"]))
    s.append(slide(f"Day {n} of {TOTAL}", f'<h1>{title}</h1>\n<p class="cover-sub">{sub}</p>\n<div>{pills}</div>'))

    pr = items(d["p_rows"])
    s.append(slide("The problem", f'<h2>{fmt(d["p_h"])}</h2>\n<div class="body{" tight" if len(pr) > 4 else ""}">\n{rows_kv(pr)}\n</div>\n<p class="lead">{fmt(d["p_end"])}</p>', True))

    leads = "\n".join(f'<p class="lead">{fmt(x)}</p>' for x in items(d["s_leads"]))
    s.append(slide("The simple version", f'<h2>{fmt(d["s_h"])}</h2>\n{leads}\n<div class="body">\n{rows_kv(items(d["s_rows"]), "✓")}\n</div>'))

    m = f'<h2>{fmt(d["m_h"])}</h2>\n'
    if d.get("m_tiles"):
        m += '<div class="grid">\n' + "\n".join('<div class="tile"><b>%s</b><span>%s</span></div>' % tuple(map(fmt, kv(t))) for t in items(d["m_tiles"])) + "\n</div>\n"
    if d.get("m_rows"):
        mr = items(d["m_rows"])
        m += f'<div class="steps{" tight" if len(mr) > 4 else ""}">\n{rows_text(mr)}\n</div>\n'
    if d.get("m_bar"):
        m += '<div class="bar lake"><b>%s</b>%s</div>\n' % tuple(map(fmt, kv(d["m_bar"])))
    for c in items(d.get("m_caps", "")):
        m += '<div class="bar cap"><b>%s</b> · %s</div>\n' % tuple(map(fmt, kv(c)))
    s.append(slide(d.get("m_tag", "How it works"), m))

    s.append(slide("For engineers", f'<h2>{fmt(d["e_h"])}</h2>\n<div class="body">\n{rows_col(items(d["e_rows"]))}\n</div>', True))

    li = lambda key: "".join(f"<li>{fmt(x)}</li>" for x in items(d[key]))
    ck, cv = kv(d["h_catch"])
    s.append(slide("The honest part", f'<h2>{fmt(d["h_h"])}</h2>\n<div class="split">\n<div class="box yes"><h3>{fmt(d.get("h_yes_t", "Good fit"))}</h3><ul>{li("h_yes")}</ul></div>\n<div class="box no"><h3>{fmt(d.get("h_no_t", "Think twice"))}</h3><ul>{li("h_no")}</ul></div>\n</div>\n<p class="quote"><b class="w">{fmt(ck)}:</b> {fmt(cv)}</p>'))

    real = d.get("r_kind", "real") == "real"
    rr = items(d["r_rows"])
    r = f'<h2>{fmt(d["r_h"])}</h2>\n'
    if d.get("r_lead"):
        r += f'<p class="lead">{fmt(d["r_lead"])}</p>\n'
    r += f'<div class="steps{" tight" if len(rr) > 4 and d.get("r_lead") else ""}">\n{rows_text(rr)}\n</div>\n'
    if d.get("r_end"):
        r += f'<p class="lead">{fmt(d["r_end"])}</p>'
    s.append(slide("From real work" if real else "Watch out", r, True))

    lab, rest = kv(d["z_next"])
    top, teaser = kv(rest)
    s.append(slide("Save this", f'<h2>{fmt(d["z_h"])}</h2>\n<div class="body">\n{rows_text(items(d["z_rows"]))}\n</div>\n<p class="big">{fmt(lab)}: <em>{fmt(top)}</em>.<br>{fmt(teaser)}</p>'))

    body = "\n\n".join(s)
    return f'''<!doctype html><html><head><meta charset="utf-8"><title>Day {n}</title><link rel="stylesheet" href="../../assets/carousel.css"></head>
<body data-series="{SERIES}" data-day="{n}" data-total="{TOTAL}" data-author="{AUTHOR}" data-role="{html.escape(ROLE)}">

{body}

<script src="../../assets/carousel.js"></script></body></html>
'''


def build_caption(n, d):
    lab, rest = kv(d["z_next"])
    top, _ = kv(rest)
    parts = [f'Microsoft Fabric, Day {n} of {TOTAL}: {d["cap_title"]}.', d["caption"], GUIDE, f"{lab}: {top}.", d["q"], f'{BASE_TAGS} {d["tags"]}']
    return "\n\n".join(p for p in parts if p) + "\n"


def chrome(*args):
    return subprocess.run([CHROME, "--headless=new", "--disable-gpu", *args], capture_output=True, text=True, timeout=120).stdout


def main():
    days = [int(a) for a in sys.argv[1:]] or sorted(int(p.stem.split("-")[1]) for p in (ROOT / "content").glob("day-*.txt"))
    problems = 0
    for n in days:
        d = parse(ROOT / "content" / f"day-{n:02d}.txt")
        out = ROOT / "posts" / f"day-{n:02d}"
        out.mkdir(parents=True, exist_ok=True)
        page, cap = build_html(n, d), build_caption(n, d)
        low = (page + cap).lower()
        bad = [b for b in BANNED if b in low]
        (out / "carousel.html").write_text(page)
        (out / "caption.txt").write_text(cap)
        (out / "title.txt").write_text(f"Microsoft Fabric, Day {n} of {TOTAL}: {d['topic']}\n")
        url = (out / "carousel.html").as_uri()
        chrome("--no-pdf-header-footer", f"--print-to-pdf={out/'carousel.pdf'}", url)
        dom = chrome("--window-size=4320,2700", "--dump-dom", url + "#check")
        m = re.search(r"<title>(.*?)</title>", dom)
        res = m.group(1) if m else "NO RESULT"
        flag = "" if res == "OK" and not bad and len(cap) <= 3000 else "  <-- FIX"
        problems += bool(flag)
        print(f"day {n:02d}: layout={res} caption={len(cap)} chars banned={bad or 'none'}{flag}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
