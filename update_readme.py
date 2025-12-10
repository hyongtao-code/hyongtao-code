import requests
import re
import os

USERNAME = "hyongtao-code"

REPOS = {
    "CLOUDBERRY_COMMITS": ("apache", "cloudberry"),
    "VLLM_COMMITS": ("vllm-project", "vllm"),
    "DIFY_COMMITS": ("langgenius", "dify"),
}

README_PATH = "README.md"


def get_commit_count(owner, repo, username):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?author={username}&per_page=1"
    r = requests.get(url)
    
    if "Link" not in r.headers:
        return len(r.json())

    link = r.headers["Link"]
    m = re.search(r'&page=(\d+)>; rel="last"', link)
    if not m:
        return len(r.json())

    return int(m.group(1))


def update_readme():
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    for placeholder, (owner, repo) in REPOS.items():
        count = get_commit_count(owner, repo, USERNAME)
        print(f"{placeholder}: {count}")
        content = content.replace(f"{{{{{placeholder}}}}}", str(count))

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    update_readme()
