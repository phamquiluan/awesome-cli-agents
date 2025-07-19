import requests
from datetime import datetime
import re

MARKER_START = "<!-- AUTO-GENERATED-START -->"
MARKER_END = "<!-- AUTO-GENERATED-END -->"

QUERIES = {
    "Vim/Neovim": "vim OR neovim ai plugin stars:>10",
    "Terminal": "ai terminal cli OR shell OR zsh OR bash stars:>10",
}

SEARCH_URL = "https://api.github.com/search/repositories"
HEADERS = {"Accept": "application/vnd.github+json"}

def format_star_count(stars):
    if stars >= 1000:
        return f"{stars // 1000}k⭐"
    return f"{stars}⭐"

def fetch_repos(tag, query):
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
    }
    resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    items = resp.json().get("items", [])
    results = []
    for item in items:
        name = item["full_name"]
        desc = item.get("description", "").strip()
        url = item["html_url"]
        stars = item.get("stargazers_count", 0)
        star_str = format_star_count(stars)
        results.append(f"- [{name}]({url}) - {desc} [{tag}] ({star_str})")
    return results

def generate_autosection(entries):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    section = f"_Last updated: {timestamp}_\n\n## 🚀 AI Tools for Vim, Neovim, and Terminal\n\n"
    section += "\n".join(sorted(set(entries)))
    return section

def update_readme(entries):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    new_auto = f"{MARKER_START}\n{generate_autosection(entries)}\n{MARKER_END}"
    updated = re.sub(f"{MARKER_START}.*?{MARKER_END}", new_auto, content, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)

if __name__ == "__main__":
    all_entries = []
    for tag, query in QUERIES.items():
        all_entries += fetch_repos(tag, query)
    update_readme(all_entries)
