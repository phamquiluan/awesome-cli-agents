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

def parse_existing_repos():
    """Parse existing repositories from README.md between AUTO-GENERATED markers."""
    repos = {}
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract content between markers
        match = re.search(f"{MARKER_START}(.*?){MARKER_END}", content, re.DOTALL)
        if not match:
            return repos
        
        auto_content = match.group(1)
        
        # Parse repository entries using regex
        # Format: - [owner/repo](url) - description [tag] (stars)
        pattern = r'- \[([^\]]+)\]\([^\)]+\) - ([^[]*) \[([^\]]+)\] \([^)]+\)'
        
        for match in re.finditer(pattern, auto_content):
            full_name = match.group(1)
            description = match.group(2).strip()
            tag = match.group(3)
            
            repos[full_name] = {
                'description': description,
                'tag': tag,
                'full_name': full_name
            }
    except FileNotFoundError:
        pass
    
    return repos

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
        "sort": "updated",  # Sort by last updated instead of stars
        "order": "desc",
        "per_page": 30,
    }
    resp = requests.get(SEARCH_URL, headers=HEADERS, params=params)
    if resp.status_code != 200:
        print(f"API request failed with status {resp.status_code}: {resp.text}")
        return []
    
    try:
        items = resp.json().get("items", [])
    except requests.exceptions.JSONDecodeError:
        print(f"Failed to parse JSON response: {resp.text}")
        return []
    
    results = []

    for item in items:
        full_name = item["full_name"]
        if full_name in blocked:
            continue  # Skip blocked repositories

        desc = (item.get("description") or "").strip().replace("\n", " ")
        url = item["html_url"]
        stars = item.get("stargazers_count", 0)
        updated_at = item.get("updated_at", "")
        star_str = format_star_count(stars)

        if len(desc) > 200:
            continue

        results.append({
            'full_name': full_name,
            'url': url,
            'description': desc,
            'tag': tag,
            'stars': stars,
            'star_str': star_str,
            'updated_at': updated_at
        })
    return results

def fetch_repo_details(full_name):
    """Fetch detailed information for a specific repository."""
    url = f"https://api.github.com/repos/{full_name}"
    resp = requests.get(url, headers=HEADERS)
    
    if resp.status_code != 200:
        print(f"Failed to fetch details for {full_name}: {resp.status_code}")
        return None
    
    try:
        data = resp.json()
        return {
            'full_name': full_name,
            'url': data.get('html_url', ''),
            'description': (data.get('description') or '').strip().replace('\n', ' '),
            'stars': data.get('stargazers_count', 0),
            'updated_at': data.get('updated_at', '')
        }
    except requests.exceptions.JSONDecodeError:
        print(f"Failed to parse JSON for {full_name}")
        return None

def merge_and_sort_repos(existing_repos, new_repos):
    """Merge existing and new repositories, prioritizing new data, and sort by updated_at."""
    # Create a dictionary to store all repositories
    all_repos = {}
    
    # Add existing repositories, fetch their updated_at if needed
    for full_name, repo_data in existing_repos.items():
        details = fetch_repo_details(full_name)
        if details:
            all_repos[full_name] = {
                'full_name': full_name,
                'url': details['url'],
                'description': details['description'],
                'tag': repo_data['tag'],
                'stars': details['stars'],
                'star_str': format_star_count(details['stars']),
                'updated_at': details['updated_at']
            }
    
    # Add new repositories (these will override existing ones if there are duplicates)
    for repo in new_repos:
        all_repos[repo['full_name']] = repo
    
    # Sort by updated_at (most recent first)
    sorted_repos = sorted(all_repos.values(), 
                         key=lambda x: x.get('updated_at', ''), 
                         reverse=True)
    
    return sorted_repos

def generate_autosection(repos):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    section = f"_Last updated: {timestamp}_\n\n## 🚀 AI Tools for Vim, Neovim, and Terminal\n\n"
    
    entries = []
    for repo in repos:
        entry = f"- [{repo['full_name']}]({repo['url']}) - {repo['description']} [{repo['tag']}] ({repo['star_str']})"
        entries.append(entry)
    
    section += "\n".join(entries)
    return section

def update_readme(repos):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    new_auto = f"{MARKER_START}\n{generate_autosection(repos)}\n{MARKER_END}"
    updated = re.sub(f"{MARKER_START}.*?{MARKER_END}", new_auto, content, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)

if __name__ == "__main__":
    # Parse existing repositories from README
    existing_repos = parse_existing_repos()
    print(f"Found {len(existing_repos)} existing repositories")
    
    # Fetch new repositories from search queries
    blocklist = load_blocklist()
    new_repos = []
    for tag, query in QUERIES.items():
        repos = fetch_repos(tag, query, blocklist)
        new_repos.extend(repos)
    
    print(f"Found {len(new_repos)} new repositories from search")
    
    # Merge existing and new repositories, sort by updated_at
    all_repos = merge_and_sort_repos(existing_repos, new_repos)
    print(f"Total repositories after merge: {len(all_repos)}")
    
    # Only update README if we have repositories
    if all_repos:
        update_readme(all_repos)
        print("README updated successfully")
    else:
        print("No repositories found. README not updated.")
