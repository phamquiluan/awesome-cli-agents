import requests
import re
import os
from datetime import datetime

MARKER_START = "<!-- AUTO-GENERATED-START -->"
MARKER_END = "<!-- AUTO-GENERATED-END -->"
BLOCKLIST_FILE = os.path.join(os.path.dirname(__file__), "block-list.txt")

QUERIES = {
    "Vim/Neovim": "vim OR neovim ai plugin stars:>10",
    "Copilot": "vim OR terminal OR cli copilot stars:>10",
    "Terminal": "ai terminal cli OR shell OR zsh OR bash stars:>10",
}

SEARCH_URL = "https://api.github.com/search/repositories"
HEADERS = {"Accept": "application/vnd.github+json"}

def load_blocklist():
    try:
        with open(BLOCKLIST_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def format_star_count(stars):
    return f"{stars // 1000}k⭐" if stars >= 1000 else f"{stars}⭐"

def fetch_repos(tag, query, blocked):
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
        full_name = item["full_name"]
        if full_name in blocked:
            continue  # Skip blocked repositories

        desc = item.get("description", full_name).strip().replace("\n", " ")
        url = item["html_url"]
        stars = item.get("stargazers_count", 0)
        star_str = format_star_count(stars)

        if len(desc) > 200:
            continue

        results.append(f"- [{full_name}]({url}) - {desc} [{tag}] ({star_str})")
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
    blocklist = load_blocklist()
    all_entries = []
    for tag, query in QUERIES.items():
        all_entries += fetch_repos(tag, query, blocklist)
    update_readme(all_entries)
