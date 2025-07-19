import requests
from datetime import datetime

README_HEADER = """# Awesome Vim AI Agents 🧠📝

> Curated list of tools and plugins that help you use AI in **Vim, Neovim**, and the **Terminal**.

_Last updated: {date}_

## 🚀 AI Tools for Vim, Neovim, and Terminal
"""

QUERIES = {
    "Vim/Neovim": "ai vim OR neovim plugin in:description language:vim stars:>10",
    "Terminal": "ai terminal shell zsh bash in:description stars:>10"
}

SEARCH_URL = "https://api.github.com/search/repositories"

def fetch_repos(tag, query):
    headers = {"Accept": "application/vnd.github+json"}
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 30,
    }
    response = requests.get(SEARCH_URL, headers=headers, params=params)
    items = response.json().get("items", [])
    results = []
    for item in items:
        name = item["full_name"]
        desc = item.get("description", "").strip()
        url = item["html_url"]
        line = f"- [{name}]({url}) - {desc} [{tag}]"
        results.append(line)
    return results

def update_readme(entries):
    with open("README.md", "w") as f:
        header = README_HEADER.format(date=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
        f.write(header + "\n")
        for entry in sorted(set(entries)):
            f.write(entry + "\n")

if __name__ == "__main__":
    all_entries = []
    for tag, query in QUERIES.items():
        entries = fetch_repos(tag, query)
        all_entries.extend(entries)
    update_readme(all_entries)
