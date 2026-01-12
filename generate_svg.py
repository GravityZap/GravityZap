import requests
import svgwrite
import os

# -----------------------------
# CONFIG
# -----------------------------
USERNAME = "GravityZap"       # GitHub nick
SVG_DIR = "svg"               # Folder docelowy
os.makedirs(SVG_DIR, exist_ok=True)

# -----------------------------
# HELPER: Tworzenie SVG
# -----------------------------
def create_svg(filename, width, height, bg_color, text_lines):
    dwg = svgwrite.Drawing(os.path.join(SVG_DIR, filename), size=(width, height))
    dwg.add(dwg.rect(insert=(0,0), size=(width, height), rx=8, fill=bg_color))
    y = 25
    for line in text_lines:
        dwg.add(dwg.text(line['text'], insert=(20, y),
                         fill=line.get('color', '#fff'),
                         font_size=line.get('size', 16),
                         font_family="Segoe UI, sans-serif"))
        y += 20
    dwg.save()

# -----------------------------
# FETCH DATA FROM GITHUB API
# -----------------------------
api_base = f"https://api.github.com/users/{USERNAME}"

user_data = requests.get(api_base).json()
repos_data = requests.get(f"{api_base}/repos").json()

# Achievements: prosta metryka followers + public_repos
achievements_count = user_data.get("followers", 0) + user_data.get("public_repos", 0)

# Commits: suma commitów w public repos (GitHub API ogranicza, przy demo sumujemy tylko fork=False)
total_commits = 0
for repo in repos_data:
    if not repo.get("fork", True):
        commits_url = f"https://api.github.com/repos/{USERNAME}/{repo['name']}/commits"
        r = requests.get(commits_url, params={"per_page":1})
        if 'Link' in r.headers and 'last' in r.headers['Link']:
            # Nie pobieramy dokładnej liczby w tym prostym demo
            total_commits += 1
        else:
            total_commits += len(r.json())

# Top languages (sumowanie procentowe)
lang_count = {}
for repo in repos_data:
    lang_url = repo.get("languages_url")
    if lang_url:
        langs = requests.get(lang_url).json()
        for lang, count in langs.items():
            lang_count[lang] = lang_count.get(lang, 0) + count

# Sort top 3 languages
top_langs = sorted(lang_count.items(), key=lambda x: x[1], reverse=True)[:3]
top_langs_text = ", ".join([f"{lang} {count}" for lang, count in top_langs])

# -----------------------------
# GENERATE SVG FILES
# -----------------------------

# Achievements
create_svg(
    "achievements.svg",
    width=480,
    height=60,
    bg_color="#1b1f35",
    text_lines=[{"text": f"Achievements: {achievements_count} 🚀", "color": "#7f00ff", "size": 20}]
)

# Commits
create_svg(
    "commits.svg",
    width=480,
    height=60,
    bg_color="#0a0a0a",
    text_lines=[{"text": f"Commits: {total_commits} 🔥", "color": "#00ff7f", "size": 20}]
)

# Top Languages
create_svg(
    "top-langs.svg",
    width=480,
    height=60,
    bg_color="#1b1f35",
    text_lines=[
        {"text": "Top Languages:", "color": "#ff7f00", "size": 16},
        {"text": top_langs_text, "color": "#ff0", "size": 16}
    ]
)

# Streak (dla demo: losowa wartość)
streak_days = 42  # tutaj możesz pobrać z GitHub Streak API lub ustawić manualnie
create_svg(
    "streak.svg",
    width=480,
    height=60,
    bg_color="#0a0a0a",
    text_lines=[{"text": f"Streak: {streak_days} days 🌟", "color": "#a933ff", "size": 20}]
)

print("✅ SVG files generated in folder ./svg/")
