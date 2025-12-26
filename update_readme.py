import os
import re
import requests

USERNAME = "hyongtao-code"

REPOS = {
    "VLLM_COMMITS": ("vllm-project", "vllm"),
    "DIFY_COMMITS": ("langgenius", "dify"),
    "CPYTHON_COMMITS": ("python", "cpython"),
    "CLOUDBERRY_COMMITS": ("apache", "cloudberry"),
}

README_PATH = "README.md"


def get_commit_count(owner: str, repo: str, username: str) -> int:
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "commit-count-updater",
    }

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    params = {
        "author": username,
        "per_page": 1,
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)

    if r.status_code != 200:
        raise RuntimeError(
            f"GitHub API error {r.status_code} for {owner}/{repo}: {r.text}"
        )

    # No pagination → 0 or 1 commit
    if "Link" not in r.headers:
        return len(r.json())

    link = r.headers["Link"]
    m = re.search(r"[?&]page=(\d+)>; rel=\"last\"", link)
    if not m:
        return len(r.json())

    return int(m.group(1))


def replace_between_markers(content: str, key: str, value: int) -> str:
    """
    Replace content between:
      <!--KEY_START--> ... <!--KEY_END-->
    """
    pattern = re.compile(
        rf"(<!--{re.escape(key)}_START-->)(.*?)(<!--{re.escape(key)}_END-->)",
        re.DOTALL,
    )

    if not pattern.search(content):
        raise RuntimeError(
            f"Marker for {key} not found in README.md "
            f"(expected <!--{key}_START--> ... <!--{key}_END-->)"
        )

    return pattern.sub(rf"\g<1>{value}\g<3>", content)


def update_readme() -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    for key, (owner, repo) in REPOS.items():
        count = get_commit_count(owner, repo, USERNAME)
        print(f"{key}: {count}")
        content = replace_between_markers(content, key, count)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    update_readme()
