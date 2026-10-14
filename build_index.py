#!/usr/bin/env python3
"""Generate index.qmd and one page per section from the contributions repo (checked out at ../data by the
GitHub Action, or at the path in $CONTRIB_DIR). Runs as a Quarto pre-render step."""
import csv, html, os, re, shutil, sys, datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

here = Path(__file__).parent
data = Path(os.environ.get("CONTRIB_DIR", here.parent / "open-physics-data-terms"))
if not data.exists():
    sys.exit(f"contributions repo not found at {data}; set CONTRIB_DIR")

doi = os.environ.get("ZENODO_DOI", "10.5281/zenodo.XXXXXXX")
tag = os.environ.get("RELEASE_TAG", "main")
version = "v" + tag.lstrip("v") if tag.lower().startswith("v") else "unreleased draft"
e = html.escape

contribs = yaml.safe_load((data / "contributions.yml").read_text()) or []
# copy PDFs next to the site so links are relative
(here / "contributions").mkdir(exist_ok=True)
for c in contribs:
    src = data / c["file"]
    if src.exists():
        shutil.copy(src, here / "contributions" / src.name)


SITE_URL = "https://det-lab.github.io/open-physics-data-terms-site/"
TITLE = "Open physics data: what license and attribution terms should it carry?"
year = "2026"
EDITORS = [("Roberts", "Amy"), ("Taufer", "Michela"), ("Walker", "Jessica")]
COLL_KEY = f"roberts{year}openphysicsdata"

def split_name(c):
    """family, given. Uses cite_name 'Family, Given' from the yml when present."""
    cn = c.get("cite_name")
    if cn and "," in cn:
        fam, giv = [x.strip() for x in cn.split(",", 1)]
        return fam, giv
    parts = c["name"].split()
    return parts[-1], " ".join(parts[:-1])

def initials(given):
    return " ".join(g[0] + "." for g in given.replace("-", " ").split())

def apa_names(pairs, eds=False):
    out = [f"{f}, {initials(g)}" for f, g in pairs]
    joined = out[0] if len(out) == 1 else ", ".join(out[:-1]) + (", & " if len(out) > 2 else " & ") + out[-1]
    return joined + (" (Eds.)" if eds else "")

def apa_in_names(pairs):
    out = [f"{initials(g)} {f}" for f, g in pairs]
    return out[0] if len(out) == 1 else ", ".join(out[:-1]) + (", & " if len(out) > 2 else " & ") + out[-1]

def bib_names(pairs):
    return " and ".join(f"{f}, {g}" for f, g in pairs)

def citebox(entries, label="Cite as", open_default="apa"):
    on = ' class="on"'
    btns = "".join(f'<button type="button"{on if k == open_default else ""} data-fmt="{k}">{n}</button>'
                   for k, n in [("apa", "APA"), ("bibtex", "BibTeX"), ("biblatex", "biblatex"), ("ris", "RIS")])
    boxes = []
    for k, v in entries.items():
        hid = "" if k == open_default else " hidden"
        if k == "apa":
            boxes.append(f'<div class="cite" data-fmt="apa"{hid}>{v}</div>')
        else:
            boxes.append(f'<pre class="cite" data-fmt="{k}"{hid}>{e(v)}</pre>')
    return (f'<div class="citebox"><div class="citebar"><span class="citelabel">{label}</span>'
            f'<span class="citefmt" role="group" aria-label="citation format">{btns}</span></div>' + "".join(boxes) + "</div>")

def contrib_cite(c):
    fam, giv = split_name(c)
    key = f"{re.sub(r'[^a-z]', '', fam.lower())}{year}"
    title = c.get("title") or f"Contribution by {c['name']}"
    pdf = SITE_URL + f'contributions/{Path(c["file"]).name}'
    pdoi = c.get("doi") or doi
    apa = (f'{apa_names([(fam, giv)])} ({year}). {e(title)}. In {apa_in_names(EDITORS)} (Eds.), '
           f'<em>{TITLE}</em> {e(version)}. Zenodo. <code>doi:{e(pdoi)}</code>')
    bibtex = f"""@incollection{{{key},
  author    = {{{bib_names([(fam, giv)])}}},
  title     = {{{title}}},
  booktitle = {{{TITLE}}},
  editor    = {{{bib_names(EDITORS)}}},
  year      = {{{year}}},
  publisher = {{Zenodo}},
  doi       = {{{pdoi}}},
  url       = {{{pdf}}},
  note      = {{{version}}}
}}"""
    biblatex = f"""% biblatex (biber); needs the @collection entry {COLL_KEY} from the site footer.
@incollection{{{key},
  author   = {{{bib_names([(fam, giv)])}}},
  title    = {{{title}}},
  crossref = {{{COLL_KEY}}},
  url      = {{{pdf}}},
  urldate  = {{{datetime.date.today().isoformat()}}}
}}"""
    ris = "\n".join([
        "TY  - CHAP", f"AU  - {fam}, {giv}", f"TI  - {title}", f"T2  - {TITLE}",
        *[f"ED  - {f}, {g}" for f, g in EDITORS],
        f"PY  - {year}", "PB  - Zenodo", f"DO  - {pdoi}", f"UR  - {pdf}", f"N1  - {version}", "ER  - "])
    return citebox({"apa": apa, "bibtex": bibtex, "biblatex": biblatex, "ris": ris}, label="Cite")

def contrib_li(c):
    tag = "from a call" if c.get("kind") == "call" else "written page"
    pdf = f'contributions/{Path(c["file"]).name}'
    label = e(c.get("title") or "PDF")
    link = f'<a href="{e(pdf)}">{label}</a>' if (data / c["file"]).exists() else '<span class="muted">PDF pending</span>'
    lic = c.get("licenses") or {}
    lictags = "".join(f' <span class="tag lic">{e(str(k))}: {e(str(v))}</span>' for k, v in lic.items())
    return (f'<li><div class="who">{e(c["name"])} <span class="aff">— {e(c["affiliation"])}</span> '
            f'<span class="tag">{tag}</span>{lictags}</div>'
            f'<div class="desc">{e(c["descriptor"])}</div>'
            f'<div class="links"><span class="ttl">{link}</span></div>'
            f'<details class="citedetails"><summary>Cite this page</summary>{contrib_cite(c)}</details></li>')


import re

# ---- sections -> pages -------------------------------------------------------
def slug_and_title(f):
    slug = re.sub(r"^\d+-", "", f.stem)
    body = f.read_text().strip()
    m = re.match(r"^##?\s+(.+)$", body, re.M)
    title = m.group(1).strip() if m else slug.replace("-", " ").capitalize()
    body = body[m.end():].strip() if m else body
    return slug, title, body

pages = []  # (slug, title, body_markdown)
secdir = data / "sections"
if secdir.exists():
    for f in sorted(secdir.glob("*.md")):
        if f.name == "README.md":
            continue
        pages.append(slug_and_title(f))

oq = (data / "open-questions.md").read_text().splitlines()
oq_items = [l.split(". ", 1)[1] for l in oq if l[:1].isdigit()]
if oq_items:
    pages.append(("open-questions", "Open questions",
                  "Questions the discussion left open.\n\n" + "\n".join(f"1. {q}" for q in oq_items)))

EYEBROW = "SESAPS 2026 · Kennesaw, GA · Nov 12–14 · moderated discussion"

def nav(current):
    items = [("index", "Contributions")] + [(sl, t) for sl, t, _ in pages]
    out = []
    for sl, t in items:
        href = "index.html" if sl == "index" else f"{sl}.html"
        out.append(f'<span class="here">{e(t)}</span>' if sl == current else f'<a href="{href}">{e(t)}</a>')
        
    return '<nav class="sitenav">' + " · ".join(out) + "</nav>"

def header(current, compact=False):
    return f"""<header>
<div class="eyebrow">{EYEBROW}</div>
<h1><a href="index.html">{TITLE}</a></h1>
<p class="lede">Public-access rules now require physics collaborations to plan data releases, but none say what license the data should carry, who must be credited, or what a user may build from it. This site collects what collaborations across physics have actually done, and the questions still open.</p>
<p class="meta">Organized by Amy Roberts (CU Denver, SuperCDMS), Michela Taufer (UT Knoxville), and Jessica Walker (UT Knoxville). Contributions are licensed CC BY 4.0, kept at <a href="https://github.com/det-lab/open-physics-data-terms">github.com/det-lab/open-physics-data-terms</a>, and archived at Zenodo with each release.</p>
{nav(current)}
</header>"""

apa = f'{apa_names(EDITORS, eds=True)}. ({year}). <em>{TITLE}</em> {e(version)}. Zenodo. <code>doi:{e(doi)}</code>'
bibtex = f"""@misc{{{COLL_KEY},
  editor    = {{{bib_names(EDITORS)}}},
  title     = {{{TITLE}}},
  year      = {{{year}}},
  publisher = {{Zenodo}},
  doi       = {{{doi}}},
  url       = {{{SITE_URL}}},
  note      = {{{version}}}
}}"""
biblatex = f"""% biblatex (biber). Cite a single contribution as @incollection with
% crossref = {{{COLL_KEY}}}; each contribution's entry is under "Cite this page".
@collection{{{COLL_KEY},
  editor    = {{{bib_names(EDITORS)}}},
  title     = {{{TITLE}}},
  date      = {{{year}}},
  version   = {{{version}}},
  publisher = {{Zenodo}},
  doi       = {{{doi}}},
  url       = {{{SITE_URL}}},
  urldate   = {{{datetime.date.today().isoformat()}}}
}}"""
ris = "\n".join(["TY  - GEN", *[f"ED  - {f}, {g}" for f, g in EDITORS], f"TI  - {TITLE}", f"PY  - {year}",
                  "PB  - Zenodo", f"DO  - {doi}", f"UR  - {SITE_URL}", f"N1  - {version}", "ER  - "])
FOOTER = "<footer>" + citebox({"apa": apa, "bibtex": bibtex, "biblatex": biblatex, "ris": ris}, label="Cite the collection") + """</footer>
<script>
document.querySelectorAll('.citebox').forEach(box => box.querySelectorAll('.citefmt button').forEach(b => b.addEventListener('click', () => {
  box.querySelectorAll('.citefmt button').forEach(x => x.classList.toggle('on', x === b));
  box.querySelectorAll('.cite').forEach(c => c.hidden = c.dataset.fmt !== b.dataset.fmt);
})));
</script>"""

def write_page(path, pagetitle, current, body, compact):
    (here / path).write_text(f"""---
pagetitle: "{pagetitle}"
---

<div class="page">
{header(current, compact)}

{body}

{FOOTER}
</div>
""")

index_body = f"""<h2>Contributions</h2>
<p>One-page perspectives from people who have released data, used someone else's, or written the policy. Each is the contributor's own words, approved by them before posting; pages the organizers drafted from a 20-minute call are marked, and the contributor edited and approved the text.</p>
<ul class="contrib">
{"".join(contrib_li(c) for c in contribs)}
</ul>"""
write_page("index.qmd", TITLE, "index", index_body, False)

# remove stale generated pages, then write current ones
for old in here.glob("*.qmd"):
    if old.name != "index.qmd":
        old.unlink()
for slug, title, body in pages:
    write_page(f"{slug}.qmd", f"{title} · Open physics data terms", slug, f"<h2>{e(title)}</h2>\n\n{body}", True)

print(f"wrote index.qmd + {len(pages)} section pages: {[p[0] for p in pages]}; {len(contribs)} contributions")
