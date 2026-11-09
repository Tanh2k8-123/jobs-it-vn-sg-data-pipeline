"""Check publishable Markdown links without contacting external websites."""

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

LINK = re.compile(r'!?\[[^\]]*\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)')


def markdown_content(path: Path) -> str:
    lines = []
    fence = None
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            delimiter = marker[1]
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return "\n".join(lines)


def heading_anchors(path: Path) -> set[str]:
    anchors = set()
    for title in re.findall(r"^#{1,6}\s+(.+)$", markdown_content(path), re.M):
        title = re.sub(r"\s+#+\s*$", "", title)
        base = re.sub(r"[^\w\s-]", "", title.lower()).replace(" ", "-")
        anchor, suffix = base, 0
        while anchor in anchors:
            suffix += 1
            anchor = f"{base}-{suffix}"
        anchors.add(anchor)
    return anchors


def check_documents(root: Path, names: set[str]) -> list[str]:
    root = root.resolve()
    errors = [
        f"Local study material must remain untracked: {name}"
        for name in sorted(names)
        if name.startswith("local-learning/")
    ]
    for name in sorted(names):
        page = root / name
        if page.suffix != ".md" or not page.is_file():
            continue
        for match in LINK.finditer(markdown_content(page)):
            target = match[1].strip("<>")
            if target.startswith(("https://", "http://", "mailto:")):
                continue
            filename, _, anchor = target.partition("#")
            destination = (page.parent / unquote(filename)).resolve() if filename else page
            if not destination.is_relative_to(root):
                errors.append(f"{name}: link leaves the repository: {target}")
                continue
            relative = destination.relative_to(root).as_posix()
            published = relative in names or (
                destination.is_dir()
                and any(relative == "." or item.startswith(relative + "/") for item in names)
            )
            if not destination.exists() or not published:
                errors.append(f"{name}: target is missing or excluded from Git: {target}")
            elif anchor and destination.suffix == ".md":
                if unquote(anchor) not in heading_anchors(destination):
                    errors.append(f"{name}: heading does not exist: {target}")
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
        )
    except (OSError, subprocess.CalledProcessError):
        print("Run this check from a Git checkout with Git installed.", file=sys.stderr)
        return 2
    names = {name for name in output.decode("utf-8").split("\0") if name}
    errors = check_documents(root, names)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    pages = sum(name.endswith(".md") for name in names)
    print(f"Documentation passed: {pages} public Markdown files; no local-only study files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
