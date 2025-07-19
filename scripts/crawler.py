import requests
from datetime import datetime

README_HEADER = """# Awesome Vim AI Agents 🧠🎯

> A curated list of AI-powered Vim/Neovim tools and plugins.

_Last updated: {date}_

## 🚀 Plugins & Tools
"""

GITHUB_QUERY = "vim+neovim+ai+plugin in:description stars:>10"
SEARCH_URL = "https://api.github.com/search/repositories"

def fetch_github_plugins():
    headers = {"Accept": "application/vnd.github+json"}
    params = {
        "q": GITHUB_QUERY,
        "sort": "stars",
        "order": "desc",
        "per_page": 20
    }
    response = requests.get(SEARCH_URL, headers=headers, params=params)
    items = response.json().get("items", [])
    results = []
    for item in items:
        name = item["full_name"]
        desc = item.get("description", "").strip()
        url = item["html_url"]
        results.append(f"- [{name}]({url}) - {desc}")
    return results

def update_readme(plugins):
    with open("README.md", "w") as f:
        header = README_HEADER.format(date=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))
        f.write(header + "\n")
        f.write("\n".join(plugins))

if __name__ == "__main__":
    plugins = fetch_github_plugins()
    update_readme(plugins)
