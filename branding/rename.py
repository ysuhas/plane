"""Replace the product name "Plane" with "Scholrithm" in user-facing strings.

Re-run after every upstream merge: new upstream strings come in saying "Plane", and a merge
conflict in any file below is resolved by taking upstream's side and running this again.

    python3 branding/rename.py           # apply
    python3 branding/rename.py --check   # list what is still unrenamed; exit 1 if anything

Scope: locale JSON values (every locale), plus UI strings in apps/web, apps/admin, apps/space and
packages/constants/src/metadata.ts. Keys, placeholders, tags and plural forms are never touched.
The new name stays Latin in every locale, as the i18n skill requires for brand marks.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "Scholrithm"

# Standalone word only: not PlaneLogo, plane_pro or plane.so. ASCII lookarounds instead of \b so
# "Planeで" and "使用Plane" in CJK text still match.
PLANE = re.compile(r"(?<![A-Za-z0-9_])Plane(?![A-Za-z0-9_])")

# English strings that stay "Plane" because they describe the upstream vendor, not this product:
# who receives telemetry, vendor docs/changelog/marketing, and Plane's commercial plan names.
# Matched against English text; the locale pass resolves them to key paths and skips the same
# keys in every language.
KEEP = [
    r"collect anonymous usage",
    r"anonymously collect usage",
    r"anonymized data",
    r"marketing communications",
    r"Join [\d,]+\+ teams",
    r"pun intended",
    r"accelerated the software development",
    r"Plane (One|Pro|Business|Enterprise|Cloud|Free)\b",
    r"Powered by Plane Pages",
    r"Open Plane documentation",
    r"New at Plane",
    r"teams switch to Plane",
    r"Compare Plane with the tools",
]
KEEP_RE = re.compile("|".join(KEEP))

# Exact rewrites that a plain word swap would get wrong; applied before the word swap.
LITERALS = [
    ('alt="Plane" fallback="P"', f'alt="{NAME}" fallback="{NAME[0]}"'),
    ("Work in plane happens best", f"Work in {NAME} happens best"),
]

LOCALES = "packages/i18n/src/locales/"
CODE_PREFIXES = ("apps/web/", "apps/admin/", "apps/space/")
CODE_FILES = {"packages/constants/src/metadata.ts"}
CODE_EXT = (".ts", ".tsx")
CODE_JSON = {
    "apps/web/manifest.json",
    "apps/web/public/manifest.json",
    "apps/web/public/site.webmanifest.json",
    "apps/admin/public/site.webmanifest.json",
    "apps/space/public/site.webmanifest.json",
}
# Plane's own pricing pages describe its commercial plans, not this product.
CODE_SKIP_PARTS = ("/billing/", "/license/", ".test.", ".spec.", "/tests/", "/e2e/")
SKIP_LINE = re.compile(r"^\s*(//|\*|/\*|\{/\*)|^\s*import |Copyright \(c\)|@plane/")
# A file importing a `Plane` identifier (e.g. an icon) is code, not prose: leave it for a human.
IMPORTS_PLANE = re.compile(r"import[^;]*(?<![A-Za-z0-9_])Plane(?![A-Za-z0-9_])[^;]*from")


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return out.splitlines()


def swap(text: str) -> str:
    for old, new in LITERALS:
        text = text.replace(old, new)
    return PLANE.sub(NAME, text)


def json_paths(lines: list[str]):
    """Yield (dotted key path, line) per line. Locale files are canonical 2-space JSON, so nesting is the indent."""
    path: list[str] = []
    for line in lines:
        m = re.match(r'(\s*)"([^"]+)":', line)
        if m:
            level = len(m.group(1)) // 2
            path = path[: level - 1] + [m.group(2)]
            yield ".".join(path), line
        else:
            yield None, line


def keep_paths(files: list[str]) -> set[tuple[str, str]]:
    """(file relative to its locale dir, key path) for every English string we must leave alone."""
    keep = set()
    for f in files:
        if f.startswith(LOCALES + "en/"):
            rel = f[len(LOCALES + "en/") :]
            for p, line in json_paths((ROOT / f).read_text(encoding="utf8").splitlines()):
                if p and KEEP_RE.search(line):
                    keep.add((rel, p))
    return keep


def locale_edit(f: str, keep: set[tuple[str, str]]) -> str:
    rel = f[len(LOCALES) :].split("/", 1)[1]
    lines = (ROOT / f).read_text(encoding="utf8").splitlines(keepends=True)
    out = []
    for (p, _), line in zip(json_paths([l.rstrip("\n") for l in lines]), lines):
        if (rel, p) in keep:
            out.append(line)
            continue
        head, sep, value = line.partition('": ')  # values only; keys never contain the capitalised name
        out.append(head + sep + PLANE.sub(NAME, value) if sep else PLANE.sub(NAME, line))
    return "".join(out)


def code_edit(text: str) -> str:
    out = []
    for line in text.splitlines(keepends=True):
        out.append(line if SKIP_LINE.search(line) or KEEP_RE.search(line) else swap(line))
    return "".join(out)


def main() -> int:
    check = "--check" in sys.argv
    files = tracked()
    keep = keep_paths(files)
    changed: dict[str, list[str]] = {"locales": [], "code": []}
    manual: list[str] = []

    for f in files:
        if f.startswith(LOCALES) and f.endswith(".json"):
            scope, edit = "locales", lambda f=f: locale_edit(f, keep)
        elif (
            (f.startswith(CODE_PREFIXES) and f.endswith(CODE_EXT) or f in CODE_FILES or f in CODE_JSON)
            and not any(part in f for part in CODE_SKIP_PARTS)
        ):
            text = (ROOT / f).read_text(encoding="utf8")
            if IMPORTS_PLANE.search(text):
                manual.append(f)
                continue
            scope, edit = "code", lambda text=text: code_edit(text)
        else:
            continue
        old = (ROOT / f).read_text(encoding="utf8")
        new = edit()
        if new != old:
            changed[scope].append(f)
            if not check:
                (ROOT / f).write_text(new, encoding="utf8")

    for scope, fs in changed.items():
        print(f"{scope}: {len(fs)} files {'still to rename' if check else 'updated'}")
        if check:
            for f in fs[:10]:
                print(f"  {f}")
    for f in manual:
        print(f"REVIEW BY HAND (imports a 'Plane' identifier): {f}")
    return int(check and any(changed.values()))


if __name__ == "__main__":
    raise SystemExit(main())
