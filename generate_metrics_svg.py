import os
import sys
import requests
import svgwrite
from collections import Counter
from datetime import datetime

# ================= CONFIG =================

USERNAME = "GravityZap"
TOKEN = os.getenv("GH_TOKEN")

if not TOKEN:
    print("❌ GH_TOKEN not set")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SVG_PATH = os.path.join(BASE_DIR, "svg", "github-metrics.svg")
os.makedirs(os.path.dirname(SVG_PATH), exist_ok=True)

W, H = 780, 420

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

QUERY = """
query ($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        forkCount
        languages(first: 10) {
          edges {
            size
            node { name }
          }
        }
      }
    }
  }
}
"""

# ================= DATA =================

res = requests.post(
    "https://api.github.com/graphql",
    json={"query": QUERY, "variables": {"login": USERNAME}},
    headers=HEADERS,
    timeout=30,
)

if res.status_code != 200:
    print("❌ GitHub API error:", res.text)
    sys.exit(1)

user = res.json()["data"]["user"]
repos = user["repositories"]["nodes"]

repo_count = user["repositories"]["totalCount"]
followers = user["followers"]["totalCount"]
stars = sum(r["stargazerCount"] for r in repos)
forks = sum(r["forkCount"] for r in repos)

lang_counter = Counter()
for r in repos:
    for l in r["languages"]["edges"]:
        lang_counter[l["node"]["name"]] += l["size"]

top_langs = lang_counter.most_common(5)

# ================= SVG =================

dwg = svgwrite.Drawing(SVG_PATH, size=(W, H))

# ===== DEFS =====

bg = dwg.defs.add(dwg.linearGradient(id="bg", start=(0, 0), end=(1, 1)))
bg.add_stop_color(0, "#0d1117")
bg.add_stop_color(1, "#111827")

card = dwg.defs.add(dwg.linearGradient(id="card", start=(0, 0), end=(0, 1)))
card.add_stop_color(0, "#161b22")
card.add_stop_color(1, "#0f141b")

accent = dwg.defs.add(dwg.linearGradient(id="accent", start=(0, 0), end=(1, 0)))
accent.add_stop_color(0, "#60a5fa")
accent.add_stop_color(1, "#a78bfa")

# --- glow ---
glow = dwg.defs.add(dwg.filter(id="glow", x="-20%", y="-20%", width="140%", height="140%"))
glow.feGaussianBlur(stdDeviation=8, result="blur")
glow.feMerge(["blur", "SourceGraphic"])

# --- soft shadow (compatible replacement for feDropShadow) ---
soft_shadow = dwg.defs.add(dwg.filter(id="softShadow", x="-20%", y="-20%", width="140%", height="140%"))
soft_shadow.feGaussianBlur(in_="SourceAlpha", stdDeviation=10, result="blur")
soft_shadow.feOffset(dx=0, dy=6, result="offsetBlur")
soft_shadow.feMerge(["offsetBlur", "SourceGraphic"])

# ===== BACKGROUND =====

dwg.add(dwg.rect((0, 0), (W, H), rx=26, fill="url(#bg)"))
dwg.add(dwg.circle((W - 120, -40), 180, fill="url(#accent)", opacity=0.08, filter="url(#glow)"))

# ===== HEADER =====

dwg.add(dwg.text("GitHub Metrics", insert=(40, 56), fill="#f0f6fc", font_size=28, font_weight="700"))
dwg.add(dwg.text(f"{USERNAME} · live repository overview", insert=(40, 82), fill="#8b949e", font_size=13))
dwg.add(dwg.line((40, 96), (740, 96), stroke="#1f2933", stroke_width=1))

# ===== METRIC CARDS =====

def tile(x, y, title, value):
    dwg.add(dwg.rect((x, y), (160, 82), rx=18, fill="url(#card)", filter="url(#softShadow)"))
    dwg.add(dwg.text(title.upper(), insert=(x+18, y+30), fill="#8b949e", font_size=10, letter_spacing="1.5px"))
    dwg.add(dwg.text(str(value), insert=(x+18, y+64), fill="#f0f6fc", font_size=26, font_weight="700"))

tile(40, 120, "Repositories", repo_count)
tile(220, 120, "Stars", stars)
tile(400, 120, "Forks", forks)
tile(580, 120, "Followers", followers)

# ===== LANGUAGES =====

dwg.add(dwg.text("Top languages", insert=(40, 245), fill="#c9d1d9", font_size=18, font_weight="600"))

max_size = max([s for _, s in top_langs]) if top_langs else 1
y = 275

for lang, size in top_langs:
    w = int((size / max_size) * 520)
    dwg.add(dwg.text(lang, insert=(40, y), fill="#e6edf3", font_size=13))
    dwg.add(dwg.rect((40, y + 10), (560, 12), rx=8, fill="#1f2933"))
    dwg.add(dwg.rect((40, y + 10), (w, 12), rx=8, fill="url(#accent)"))
    y += 34

# ===== FOOTER =====

dwg.add(dwg.text(
    f"updated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
    insert=(40, 395),
    fill="#6e7681",
    font_size=10
))

dwg.save()
print(f"✅ {SVG_PATH} generated successfully!")

