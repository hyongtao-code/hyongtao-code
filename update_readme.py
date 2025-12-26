import os
import re
import requests

USERNAME = "hyongtao-code"

REPOS = {
    "VLLM_PRS": ("vllm-project", "vllm"),
    "DIFY_PRS": ("langgenius", "dify"),
    "CPYTHON_PRS": ("python", "cpython"),
    "CLOUDBERRY_PRS": ("apache", "cloudberry"),
}

README_PATH = "README.md"


def get_pr_count(owner: str, repo: str, username: str) -> int:
    """
    Count pull requests authored by `username` in a repo using GitHub Search API.
    This works reliably even when commits are squashed or rebased.
    """
    url = "https://api.github.com/search/issues"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pr-count-updater",
    }

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    query = f"repo:{owner}/{repo} is:pr author:{username}"
    params = {
        "q": query,
        "per_page": 1,  # we only need total_count
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"GitHub Search API error {r.status_code} for {owner}/{repo}: {r.text}"
        )

    return r.json()["total_count"]


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
        count = get_pr_count(owner, repo, USERNAME)
        print(f"{key}: {count}")
        content = replace_between_markers(content, key, count)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    update_readme()
