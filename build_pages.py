#!/usr/bin/env python3
"""Create the topic pages from data/problems.csv (run once).

It refuses to overwrite a page that already exists, so your progress is safe.
Use --force only if you really want to start over.
"""
from __future__ import annotations

import argparse
import csv
import html
import json
import sys
from pathlib import Path

TODO_ICON = "⬜"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", type=Path, default=Path("data/problems.csv"))
    p.add_argument("--pages", type=Path, default=Path("data/pages.json"), help="page list: file, title, topics")
    p.add_argument("--out", type=Path, default=Path("topics"))
    p.add_argument("--readme", default="../README.md", help="relative link back to the README")
    p.add_argument("--todo-icon", default=TODO_ICON)
    p.add_argument("--force", action="store_true", help="overwrite existing pages")
    return p.parse_args(argv)


def md_escape(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")


def difficulty_label(row: dict[str, str]) -> str:
    if not row["difficulty"]:
        return ""
    return row["difficulty"] if row["rating"] else f"~{row['difficulty']}"


def block(row: dict[str, str], icon: str) -> str:
    meta = " · ".join(x for x in (row["id"], difficulty_label(row)) if x)
    summary = f"{icon} <b>{html.escape(row['problem'], quote=False)}</b> — {html.escape(meta, quote=False)}"
    problem = f"[{md_escape(row['problem'])}]({row['link']})" if row["link"] else md_escape(row["problem"])
    lines = [
        "<details>",
        f"<summary>{summary}</summary>",
        "",
        "- [ ] Solved",
        "- **Solution:** _not added yet_",
        f"- **Problem:** {problem}",
        f"- **Tier:** {row['tier']}",
    ]
    if row["tags"]:
        lines.append(f"- **Tags:** {row['tags']}")
    if row["video"]:
        lines.append(f"- **Video / editorial:** {row['video']}")
    lines += ["", "</details>", ""]
    return "\n".join(lines)


def page_text(title: str, rows: list[dict[str, str]], readme_link: str, icon: str) -> str:
    head = [
        f"# {title}",
        "",
        f"[← Back to README]({readme_link})",
        "",
        "<!-- page-progress:start -->",
        "<!-- page-progress:end -->",
        "",
        "Easy to hard. Click a problem to open it. Tick `Solved` and paste your solution link, "
        "then run `python scripts/sync_progress.py` (or just push, the workflow does it).",
        "",
        "",
    ]
    return "\n".join(head) + "\n".join(block(r, icon) for r in rows)


def main(argv: list[str]) -> int:
    a = parse_args(argv)
    with a.csv.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pages = json.loads(a.pages.read_text(encoding="utf-8"))
    a.out.mkdir(parents=True, exist_ok=True)
    for page in pages:
        target = a.out / page["file"]
        if target.exists() and not a.force:
            print(f"skip {target} (exists)")
            continue
        chosen = [r for r in rows if r["topic"] in page["topics"]]
        chosen.sort(key=lambda r: (float(r["difficulty"] or 0), r["id"]))
        target.write_text(page_text(page["title"], chosen, a.readme, a.todo_icon), encoding="utf-8")
        print(f"wrote {target}: {len(chosen)} problems")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
