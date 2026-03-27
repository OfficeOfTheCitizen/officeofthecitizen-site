#!/usr/bin/env python3
import html
import re
import subprocess
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path("/Users/babatunde/Documents/Claude/Projects/Codex-Office of the Citizen")

DOCS = [
    {
        "source": Path("/Users/babatunde/Library/CloudStorage/GoogleDrive-tunde.apalowo@gmail.com/My Drive/Office of the Citizen/2_archive-methodology-v1.3"),
        "output": ROOT / "archive/methodology/index.html",
        "title": "Archive Methodology | Office of the Citizen",
        "description": "Full editorial methodology and operating standard for The 100 Archive Project.",
        "kicker": "Archive Methodology",
        "current": "Methodology",
        "route": "/archive/methodology/",
    },
    {
        "source": Path("/Users/babatunde/Library/CloudStorage/GoogleDrive-tunde.apalowo@gmail.com/My Drive/Office of the Citizen/accountability-index-v1.1"),
        "output": ROOT / "archive/accountability-index/index.html",
        "title": "Accountability Index | Office of the Citizen",
        "description": "Full instrument specification and scoring manual for the Accountability Index.",
        "kicker": "Accountability Index",
        "current": "Accountability Index",
        "route": "/archive/accountability-index/",
    },
    {
        "source": Path("/Users/babatunde/Library/CloudStorage/GoogleDrive-tunde.apalowo@gmail.com/My Drive/Office of the Citizen/governance-diagnostics-v1.0"),
        "output": ROOT / "archive/governance-diagnostics/index.html",
        "title": "Governance Diagnostics | Office of the Citizen",
        "description": "Full Layer 3 structural pathology methodology and diagnostic standards.",
        "kicker": "Governance Diagnostics",
        "current": "Governance Diagnostics",
        "route": "/archive/governance-diagnostics/",
    },
]

MENU_ITEMS = [
    ("Home", "/"),
    ("Archive", "/archive/"),
    ("Methodology", "/archive/methodology/"),
    ("Accountability Index", "/archive/accountability-index/"),
    ("Governance Diagnostics", "/archive/governance-diagnostics/"),
    ("Policy", "/policy/electricity/"),
    ("Constitution", "/constitution/"),
    ("Projects", "/projects/"),
    ("About", "/about/"),
]

LABEL_HEADINGS = {
    "THE RULE",
    "IMPORTANT",
    "NOTE",
    "PRINCIPLE",
    "WORKED EXAMPLE",
    "PATTERN FINDING",
    "STRUCTURAL DIAGNOSIS",
    "FORMAL FINDING THRESHOLD",
}


def run_textutil(source: Path) -> str:
    return subprocess.check_output(
        ["textutil", "-convert", "html", "-stdout", str(source)],
        text=True,
    )


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "section"


def normalize_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def element_text(el) -> str:
    return normalize_text(" ".join(el.stripped_strings))


def clean_node(el):
    soup = BeautifulSoup(str(el), "lxml")
    node = soup.find(["p", "table", "ul", "ol"])
    if node is None:
        return None
    for tag in list(node.find_all(True)):
        if tag.name in {"span", "font"}:
            tag.unwrap()
            continue
        tag.attrs = {}
    node.attrs = {}
    return node


def inner_html(node) -> str:
    return "".join(str(child) for child in node.contents).strip()


def is_all_boldish(node) -> bool:
    if node.name != "p":
        return False
    if not node.find(["b", "strong"]):
        return False
    plain_chunks = []
    for child in node.contents:
        if isinstance(child, str):
            plain_chunks.append(child.strip())
    return not any(chunk for chunk in plain_chunks)


def render_table(node) -> str:
    node["class"] = "doc-table"
    return f'<div class="table-wrap">{str(node)}</div>'


def render_list(node) -> str:
    node["class"] = "doc-list"
    if node.name == "ol":
        existing = node.get("class", [])
        node["class"] = existing + ["doc-list-ordered"]
    return str(node)


def render_paragraph(node, chapter_number: str) -> str:
    text = element_text(node)
    if not text:
        return ""

    if re.match(rf"^{re.escape(chapter_number)}\.\d+", text):
        section_id = slugify(f"{chapter_number}-{text}")
        return f'<h3 class="doc-h3" id="{section_id}">{inner_html(node)}</h3>'

    if text in LABEL_HEADINGS:
        return f'<div class="note">{html.escape(text)}</div>'

    if is_all_boldish(node) and len(text) <= 85 and not text.endswith("."):
        return f'<h4 class="doc-h4">{inner_html(node)}</h4>'

    if len(text) <= 120 and re.match(r"^(Dimension|Criterion|Layer|Status|Classification|Score|Instrument|Output|Tier)\b", text):
        return f'<h4 class="doc-h4">{inner_html(node)}</h4>'

    return f'<p class="doc-p">{inner_html(node)}</p>'


def render_nodes(nodes, chapter_number: str) -> str:
    rendered = []
    i = 0
    while i < len(nodes):
        node = clean_node(nodes[i])
        i += 1
        if node is None:
            continue
        text = element_text(node)
        if node.name == "p" and not text:
            continue
        if node.name == "table":
            rendered.append(render_table(node))
            continue
        if node.name in {"ul", "ol"}:
            rendered.append(render_list(node))
            continue
        rendered.append(render_paragraph(node, chapter_number))
    return "\n".join(block for block in rendered if block)


def build_menu(current: str) -> str:
    links = []
    for label, href in MENU_ITEMS:
        aria = ' aria-current="page"' if label == current else ""
        links.append(f'          <a href="{href}"{aria}>{label}</a>')
    return "\n".join(links)


def parse_document(config: dict) -> dict:
    soup = BeautifulSoup(run_textutil(config["source"]), "lxml")
    body = soup.body

    elements = []
    for child in body.children:
        if getattr(child, "name", None) in {"p", "table", "ul", "ol"}:
            elements.append(child)

    nonempty_paras = [el for el in elements if el.name == "p" and element_text(el)]
    if len(nonempty_paras) < 5:
        raise RuntimeError(f"Unexpected document front matter for {config['source']}")

    hero_title = element_text(nonempty_paras[0])
    hero_subtitle = element_text(nonempty_paras[1])
    hero_descriptor = element_text(nonempty_paras[2])
    meta_line = element_text(nonempty_paras[3])
    hero_intro = element_text(nonempty_paras[4])

    intro_el = nonempty_paras[4]
    intro_idx = elements.index(intro_el)
    remaining = elements[intro_idx + 1 :]

    contents_index = next(
        (idx for idx, el in enumerate(remaining) if el.name == "p" and element_text(el).upper() == "CONTENTS"),
        None,
    )
    if contents_index is None:
        raise RuntimeError(f"Could not find contents section in {config['source']}")

    preface_nodes = remaining[:contents_index]
    after_contents = remaining[contents_index + 1 :]

    toc_lines = []
    body_start = 0
    for idx, el in enumerate(after_contents):
        text = element_text(el)
        if re.match(r"^CHAPTER\s+\d+", text):
            body_start = idx
            break
        if el.name == "p" and re.match(r"^Chapter\s+\d+", text, re.I):
            toc_lines.append(text)
    chapter_nodes = after_contents[body_start:]

    preface = None
    meaningful_preface = [el for el in preface_nodes if element_text(el)]
    if meaningful_preface:
        first = clean_node(meaningful_preface[0])
        first_text = element_text(first)
        if first and first.name == "p" and len(first_text) <= 120:
            preface_title = first_text
            preface_content = meaningful_preface[1:]
        else:
            preface_title = "Front Matter"
            preface_content = meaningful_preface
        preface = {
            "id": "section-preface",
            "title": preface_title,
            "content": render_nodes(preface_content, "0"),
        }

    sections = []
    i = 0
    while i < len(chapter_nodes):
        chapter_marker = chapter_nodes[i]
        marker_text = element_text(chapter_marker)
        match = re.match(r"^CHAPTER\s+(\d+)", marker_text)
        if not match:
            i += 1
            continue
        chapter_number = match.group(1)
        i += 1

        while i < len(chapter_nodes):
            chapter_title = element_text(chapter_nodes[i])
            if chapter_title:
                break
            i += 1
        if i >= len(chapter_nodes):
            break

        title_text = element_text(chapter_nodes[i])
        i += 1

        subtitle = ""
        if i < len(chapter_nodes):
            candidate = chapter_nodes[i]
            candidate_text = element_text(candidate)
            if (
                candidate.name == "p"
                and candidate_text
                and not re.match(r"^\d+(?:\.\d+)+", candidate_text)
                and not re.match(r"^CHAPTER\s+\d+", candidate_text)
                and len(candidate_text) <= 180
            ):
                subtitle = candidate_text
                i += 1

        content_nodes = []
        while i < len(chapter_nodes):
            t = element_text(chapter_nodes[i])
            if chapter_nodes[i].name == "p" and re.match(r"^CHAPTER\s+\d+", t):
                break
            content_nodes.append(chapter_nodes[i])
            i += 1

        sections.append(
            {
                "id": f"chapter-{chapter_number}-{slugify(title_text)}",
                "number": chapter_number,
                "title": title_text,
                "subtitle": subtitle,
                "content": render_nodes(content_nodes, chapter_number),
            }
        )

    meta_parts = [normalize_text(part) for part in re.split(r"\s*·\s*", meta_line) if normalize_text(part)]
    meta_items = []
    labels = ["Version", "Year", "Office", "Scope"]
    for idx, part in enumerate(meta_parts[:4]):
        label = labels[idx] if idx < len(labels) else f"Field {idx + 1}"
        meta_items.append((label, part))

    return {
        "hero_title": hero_title,
        "hero_subtitle": hero_subtitle,
        "hero_descriptor": hero_descriptor,
        "hero_intro": hero_intro,
        "meta_items": meta_items,
        "preface": preface,
        "sections": sections,
    }


def render_page(config: dict, doc: dict) -> str:
    toc_items = []
    if doc["preface"]:
        toc_items.append(
            f'                <li><a href="#{doc["preface"]["id"]}"><span>{html.escape(doc["preface"]["title"])}</span></a></li>'
        )
    for section in doc["sections"]:
        toc_items.append(
            f'                <li><a href="#{section["id"]}"><span>Chapter {section["number"]} — {html.escape(section["title"])}</span></a></li>'
        )

    meta_html = "\n".join(
        f"              <dl><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></dl>"
        for label, value in doc["meta_items"]
    )

    preface_html = ""
    if doc["preface"]:
        preface_html = f"""
          <section class="section" id="{doc["preface"]["id"]}">
            <div class="note">Front Matter</div>
            <h2 class="doc-h2">{html.escape(doc["preface"]["title"])}</h2>
            {doc["preface"]["content"]}
          </section>
"""

    sections_html = []
    for section in doc["sections"]:
        subtitle_html = f'\n            <p class="section-subtitle">{html.escape(section["subtitle"])}</p>' if section["subtitle"] else ""
        sections_html.append(
            f"""          <section class="section" id="{section["id"]}">
            <div class="note">Chapter {section["number"]}</div>
            <h2 class="doc-h2">{html.escape(section["title"])}</h2>{subtitle_html}
            {section["content"]}
          </section>"""
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(config["title"])}</title>
  <meta
    name="description"
    content="{html.escape(config["description"])}"
  >
  <link rel="stylesheet" href="/archive/assets/archive-doc.css">
</head>
<body>
  <div class="progress" aria-hidden="true"><span id="progressBar"></span></div>
  <div class="shell">
    <header class="site-header">
      <a class="wordmark" href="/" aria-label="Office of the Citizen homepage">
        <img src="/officeofthecitizen-logo.png" alt="Office of the Citizen">
      </a>
      <div class="menu" data-menu>
        <button class="menu-button" type="button" aria-label="Open navigation" aria-expanded="false" aria-controls="site-menu">
          <span class="menu-icon" aria-hidden="true"></span>
        </button>
        <nav class="menu-panel" id="site-menu" aria-label="Site">
{build_menu(config["current"])}
        </nav>
      </div>
    </header>

    <div class="page-scroll">
      <div class="grid">
        <aside class="sidebar" aria-label="Section navigation">
          <div class="toc-card">
            <h2>Contents</h2>
            <div class="toc-group">
              <div class="toc-group-label">Document Sections</div>
              <ul class="toc-list toc-main">
{chr(10).join(toc_items)}
              </ul>
            </div>
          </div>
        </aside>

        <main class="main">
          <header class="hero" id="hero-overview">
            <div class="kicker">{html.escape(config["kicker"])}</div>
            <h1 class="title">
              <span class="title-main">{html.escape(doc["hero_title"])}</span>
            </h1>
            <div class="hero-subdeck">
              <p class="subtitle">{html.escape(doc["hero_subtitle"])} · {html.escape(doc["hero_descriptor"])}</p>
            </div>
            <div class="meta" aria-label="Document metadata">
{meta_html}
            </div>
            <div class="download-bar">
              <a class="button secondary" href="#{doc["preface"]["id"] if doc["preface"] else doc["sections"][0]["id"]}">Begin Reading</a>
            </div>
            <p class="doc-p" style="margin-top:20px;">{html.escape(doc["hero_intro"])}</p>
          </header>
{preface_html}
{chr(10).join(sections_html)}
          <footer class="footer">
            <div class="brandline">Source Authority</div>
            <div>{html.escape(doc["hero_title"])} · {html.escape(doc["hero_subtitle"])} · {html.escape(doc["meta_items"][0][1]) if doc["meta_items"] else ""}</div>
          </footer>
        </main>
      </div>
    </div>
  </div>
  <script src="/archive/assets/archive-doc.js"></script>
</body>
</html>
"""


def main() -> None:
    for config in DOCS:
        doc = parse_document(config)
        config["output"].parent.mkdir(parents=True, exist_ok=True)
        config["output"].write_text(render_page(config, doc))
        print(f"Built {config['output']}")


if __name__ == "__main__":
    main()
