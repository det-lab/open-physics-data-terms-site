#!/usr/bin/env python3
"""Generate index.qmd from the contributions repo (checked out at ../data by the
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
version = os.environ.get("RELEASE_TAG", "v0.1").lstrip("v")
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
    link = f'<a href="{e(pdf)}">PDF</a>' if (data / c["file"]).exists() else '<span class="muted">PDF pending</span>'
    return (f'<li><div class="who">{e(c["name"])} <span class="aff">— {e(c["affiliation"])}</span> '
            f'<span class="tag">{tag}</span></div>'
            f'<div class="desc">{e(c["descriptor"])}</div>'
            f'<div class="links">{link} · received {e(str(c.get("received") or "—"))} · '
            f'approved {e(str(c.get("approved") or "—"))} · CC BY 4.0</div></li>')

sections = ""
secdir = data / "sections"
if secdir.exists():
    sections = "\n\n".join(f.read_text().strip() for f in sorted(f for f in secdir.glob("*.md") if f.name != "README.md"))

oq = (data / "open-questions.md").read_text().splitlines()
oq_items = [l.split(". ", 1)[1] for l in oq if l[:1].isdigit()]

page = f"""---
pagetitle: "Open physics data: what license and attribution terms should it carry?"
---

<div class="page">
<header>
<div class="eyebrow">SESAPS 2026 · Kennesaw, GA · Nov 12–14 · moderated discussion</div>
<h1>Open physics data: what license and attribution terms should it carry?</h1>
<p class="lede">Public-access rules now require physics collaborations to plan data releases, but none say what license the data should carry, who must be credited, or what a user may build from it. This page collects what collaborations across physics have actually done, and the questions still open.</p>
<p class="meta">Organized by Amy Roberts (CU Denver, SuperCDMS) and Michela Taufer (UT Knoxville). Contributions and catalog are licensed CC BY 4.0 and archived at Zenodo with each release.</p>
</header>

<h2>Contributions</h2>
<p>One-page perspectives from people who have released data, used someone else's, or written the policy. Each is the contributor's own words, approved by them before posting.<span class="sn-ref">1</span><span class="sidenote">1. Pages drafted by the organizers from a 20-minute call are marked as such; the contributor edited and approved the text.</span></p>
<ul class="contrib">
{"".join(contrib_li(c) for c in contribs)}
</ul>

{sections}

<h2>Open questions</h2>
<p>Questions the discussion left open, kept as a list without owners or ranking.</p>
<ol class="oq">
{"".join(f"<li>{e(q)}</li>" for q in oq_items)}
</ol>

<footer>
Cite as: Roberts, A., Taufer, M., and contributors (2026). <em>Open physics data: what license and attribution terms should it carry?</em> v{e(version)}. Zenodo. <code>doi:{e(doi)}</code><br>
Source and contributions: <a href="https://github.com/det-lab/open-physics-data-terms"><code>github.com/det-lab/open-physics-data-terms</code></a>
</footer>
</div>
"""
(here / "index.qmd").write_text(page)
print(f"wrote index.qmd: {len(contribs)} contributions, {len(list(secdir.glob('*.md'))) if secdir.exists() else 0} sections")
