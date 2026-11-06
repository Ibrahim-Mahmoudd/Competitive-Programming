#!/usr/bin/env python3
"""Read the tick boxes in topics/*.md and update the icons and progress tables.

The pages are the source of truth. This script never changes your ticks or links.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

BLOCK = re.compile(r"<details>\n<summary>(?P<icon>\S+) (?P<rest>.*?)</summary>\n(?P<body>.*?)</details>", re.DOTALL)
SOLVED = re.compile(r"^- \[[xX]\] Solved", re.MULTILINE)
CORE_TAG = "**Tier:** Core"


@dataclass
class Counts:
    solved: int = 0
    total: int = 0
    core_solved: int = 0
    core_total: int = 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pages", type=Path, default=Path("data/pages.json"))
    p.add_argument("--topics-dir", type=Path, default=Path("topics"))
    p.add_argument("--readme", type=Path, default=Path("README.md"))
    p.add_argument("--todo-icon", default="⬜")
    p.add_argument("--done-icon", default="✅")
    p.add_argument("--core-label", default="Core", help="tier that counts as the main goal")
    return p.parse_args(argv)


def replace_between(text: str, name: str, content: str) -> str:
    start, end = f"<!-- {name}:start -->", f"<!-- {name}:end -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        raise SystemExit(f"marker '{name}' not found")
    return pattern.sub(lambda _: f"{start}\n{content}\n{end}", text)


def sync_page(text: str, a: argparse.Namespace) -> tuple[str, Counts]:
    c = Counts()
    core_tag = f"**Tier:** {a.core_label}"

    def fix(m: re.Match[str]) -> str:
        done = bool(SOLVED.search(m["body"]))
        c.total += 1
        c.solved += done
        if core_tag in m["body"]:
            c.core_total += 1
            c.core_solved += done
        icon = a.done_icon if done else a.todo_icon
        return f"<details>\n<summary>{icon} {m['rest']}</summary>\n{m['body']}</details>"

    return BLOCK.sub(fix, text), c


def core_cell(c: Counts) -> str:
    return f"{c.core_solved} / {c.core_total}" if c.core_total else "-"


def pct(done: int, total: int) -> str:
    return f"{round(100 * done / total) if total else 0}%"


def main(argv: list[str]) -> int:
    a = parse_args(argv)
    pages = json.loads(a.pages.read_text(encoding="utf-8"))
    rows, grand = [], Counts()
    for page in pages:
        path = a.topics_dir / page["file"]
        text, c = sync_page(path.read_text(encoding="utf-8"), a)
        line = f"**Solved:** {c.solved} / {c.total} ({pct(c.solved, c.total)})"
        if c.core_total:
            line += f" · **{a.core_label}:** {c.core_solved} / {c.core_total}"
        text = replace_between(text, "page-progress", line)
        if text != path.read_text(encoding="utf-8"):
            path.write_text(text, encoding="utf-8")
        rows.append(f"| [{page['title']}]({a.topics_dir.as_posix()}/{page['file']}) | {c.solved} / {c.total} | {core_cell(c)} | {pct(c.solved, c.total)} |")
        for f in ("solved", "total", "core_solved", "core_total"):
            setattr(grand, f, getattr(grand, f) + getattr(c, f))
    table = ["| Page | Solved | " + a.core_label + " | % |", "|---|---:|---:|---:|", *rows,
             f"| **Total** | **{grand.solved} / {grand.total}** | **{grand.core_solved} / {grand.core_total}** | **{pct(grand.solved, grand.total)}** |"]
    readme = replace_between(a.readme.read_text(encoding="utf-8"), "progress", "\n".join(table))
    a.readme.write_text(readme, encoding="utf-8")
    print(f"solved {grand.solved}/{grand.total}, {a.core_label.lower()} {grand.core_solved}/{grand.core_total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
