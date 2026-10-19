"""Post-pull sanity check: has an upstream change broken or undone the Scholrithm rebrand?

Run from the repo root after merging upstream: python3 branding/check.py
Exits non-zero and says what to fix. Needs `pnpm install` (reads propel) and a built @plane/blocks.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
problems = []


def read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        problems.append(f"{rel} is missing")
        return ""
    return path.read_text()


# 1. brand.css still lands: imported, and every token it sets still exists in propel
if '@import "./brand.css"' not in read("packages/tailwind-config/index.css"):
    problems.append("index.css lost the brand.css import: re-add it after the propel import")
propel = read("apps/web/node_modules/@makeplane/propel/dist/styles/variables.css")
if propel:
    ours = set(re.findall(r"--(brand-\w+):", read("packages/tailwind-config/brand.css")))
    gone = sorted(ours - set(re.findall(r"--(brand-\w+):", propel)))
    if gone:
        problems.append(f"propel no longer defines {gone}: those overrides in brand.css do nothing now")
    if 'data-theme*="dark"' not in propel:
        problems.append('propel changed its dark-mode selector: update :root[data-theme*="dark"] in brand.css')

# 2. the logo is still ours, and the built package the apps import matches
if "scholrithm" not in read("packages/blocks/src/icons/brand/plane-logo.tsx"):
    problems.append("upstream overwrote PlaneLogo: re-apply branding/scholrithm-mark.svg")
dist = ROOT / "packages/blocks/dist/icons/index.js"
if "scholrithm-mark" not in (dist.read_text() if dist.exists() else ""):
    problems.append("@plane/blocks dist is stale: pnpm turbo run build --filter=@plane/blocks")

# 3. the port override still points at services that exist upstream
local = read("docker-compose-local.yml")
for svc in re.findall(r"^  ([\w-]+):$", read("docker-compose-local.ports.yml"), re.M):
    if f"\n  {svc}:" not in local:
        problems.append(f"docker-compose-local.ports.yml overrides '{svc}', which upstream renamed or removed")

print("\n".join(f"FAIL: {p}" for p in problems) or "OK: rebrand intact")
raise SystemExit(bool(problems))
