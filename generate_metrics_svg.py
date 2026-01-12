import os
import sys
import requests
import svgwrite
from collections import Counter

USERNAME = "GravityZap"
SVG_PATH = "svg/github-metrics.svg"

# Pobranie tokena z env
TOKEN = os.getenv("GH_TOKEN")
if not TOKEN:
    print("❌ Error: GH_TOKEN environment variable is not set.")
    print("Set it locally: export GH_TOKEN=ghp_xxxxxxxxxxxx")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ---------- GraphQL ----------
QUERY = """
query ($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(privacy: PUBLIC, isFork: false, first: 100) {
      totalCount
      nodes {
        stargazerCount
        forkCount
        languages(first: 5) {
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

# ---------- Request ----------
try:
    res = requests.post(
        "https://api.github.com/graphql",
        json={"query": QUERY, "variables": {"login": USERNAME}},
        headers=HEADERS,
        timeout=30,
    )
    if res.status_code == 401:
        print("❌ Error 401: Unauthorized. Check your GH_TOKEN.")
        sys.exit(1)
    res.raise_for_status()
except requests.exceptions.RequestException as e:
    print(f"❌ HTTP request failed: {e}")
    sys.exit(1)

data = res.json().get("data", {}).get("user")
if not data:
    print("❌ Error: No user data returned. Check username and token permissions.")
    sys.exit(1)

# ---------- Metrics ----------
repos = data["repositories"]["nodes"]
repo_count = data["repositories"]["totalCount"]
followers = data["followers"]["totalCount"]

stars = sum(r["stargazerCount"] for r in repos)
forks = sum(r["forkCount"] for r in repos)

lang_counter = Counter()
for r in repos:
    for l in r["languages"]["edges"]:
        lang_counter[l["node"]["name"]] += l["size"]

top_langs = lang_counter.most_common(5)

# ---------- SVG ----------
os.makedirs("svg", exist_ok=True)
dwg = svgwrite.Drawing(SVG_PATH, size=("600px", "320px"))
dwg.add(dwg.rect((0, 0), ("600px", "320px"), rx=16, fill="#0d1117"))

def label(y, text, value):
    dwg.add(dwg.text(text, insert=(30, y), fill="#8b949e", font_size=14))
    dwg.add(dwg.text(str(value), insert=(260, y), fill="#c9d1d9", font_size=14))

label(50, "Public Repositories", repo_count)
label(80, "Stars", stars)
label(110, "Forks", forks)
label(140, "Followers", followers)

dwg.add(dwg.text("Top Languages", insert=(30, 180), fill="#58a6ff", font_size=16))

y = 210
for lang, size in top_langs:
    dwg.add(dwg.text(f"{lang}", insert=(40, y), fill="#c9d1d9", font_size=13))
    dwg.add(dwg.rect((180, y - 12), (min(size / 500, 300), 8), rx=4, fill="#7f00ff"))
    y += 22

dwg.save()
print(f"✅ {SVG_PATH} generated successfully!")
