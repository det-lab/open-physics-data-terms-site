#!/usr/bin/env python3
"""Generate index.qmd and one page per section from the contributions repo (checked out at ../data by the
GitHub Action, or at the path in $CONTRIB_DIR). Runs as a Quarto pre-render step."""
import csv, html, os, shutil, sys
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
            f'<div class="links"><span class="ttl">{link}</span><br>received {e(str(c.get("received") or "—"))} · '
            f'approved {e(str(c.get("approved") or "—"))} · CC BY 4.0</div></li>')


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

TITLE = "Open physics data: what license and attribution terms should it carry?"
EYEBROW = "SESAPS 2026 · Kennesaw, GA · Nov 12–14 · moderated discussion"

def nav(current):
    items = [("index", "Contributions")] + [(sl, t) for sl, t, _ in pages]
    out = []
    for sl, t in items:
        href = "index.html" if sl == "index" else f"{sl}.html"
        out.append(f'<span class="here">{e(t)}</span>' if sl == current else f'<a href="{href}">{e(t)}</a>')
        
    return '<nav class="sitenav">' + " · ".join(out) + "</nav>"

def header(current, compact):
    if compact:
        return (f'<header class="compact"><div class="eyebrow">{EYEBROW}</div>'
                f'<p class="sitetitle"><a href="index.html">{TITLE}</a></p>{nav(current)}</header>')
    return f"""<header>
<div class="eyebrow">{EYEBROW}</div>
<h1>{TITLE}</h1>
<p class="lede">Public-access rules now require physics collaborations to plan data releases, but none say what license the data should carry, who must be credited, or what a user may build from it. This site collects what collaborations across physics have actually done, and the questions still open.</p>
<p class="meta">Organized by Amy Roberts (CU Denver, SuperCDMS), Michela Taufer (UT Knoxville), and Jessica Walker (UT Knoxville). Contributions are licensed CC BY 4.0 and archived at Zenodo with each release.</p>
{nav(current)}
</header>"""

FOOTER = f"""<footer>
Cite as: Roberts, A., Taufer, M., Walker, J., and contributors (2026). <em>{TITLE}</em> {e(version)}. Zenodo. <code>doi:{e(doi)}</code><br>
Source and contributions: <a href="https://github.com/det-lab/open-physics-data-terms"><code>github.com/det-lab/open-physics-data-terms</code></a>
</footer>"""

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
<p>One-page perspectives from people who have released data, used someone else's, or written the policy. Each is the contributor's own words, approved by them before posting.<span class="sn-ref">1</span><span class="sidenote">1. Pages drafted by the organizers from a 20-minute call are marked as such; the contributor edited and approved the text.</span></p>
<ul class="contrib">
{"".join(contrib_li(c) for c in contribs)}
</ul>"""
write_page("index.qmd", TITLE, "index", index_body, compact=False)

# remove stale generated pages, then write current ones
for old in here.glob("*.qmd"):
    if old.name != "index.qmd":
        old.unlink()
for slug, title, body in pages:
    write_page(f"{slug}.qmd", f"{title} · Open physics data terms", slug, f"<h2>{e(title)}</h2>\n\n{body}", compact=True)

print(f"wrote index.qmd + {len(pages)} section pages: {[p[0] for p in pages]}; {len(contribs)} contributions")
