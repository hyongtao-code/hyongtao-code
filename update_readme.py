import os
import re
import time
import requests

USERNAME = "hyongtao-code"

REPOS = {
    "DIFY_PRS": ("langgenius", "dify"),
    "VLLM_PRS": ("vllm-project", "vllm"),
    "CPYTHON_PRS": ("python", "cpython"),
    "CLOUDBERRY_PRS": ("apache", "cloudberry"),
}

README_PATH = "README.md"
API = "https://api.github.com"


def github_get(url: str, params: dict | None = None) -> dict:
    """
    Small helper with optional auth + basic retry for rate limits / transient failures.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "commit-count-updater",
    }
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    last_exc = None
    for attempt in range(1, 4):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=20)

            # Basic rate limit handling
            if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                reset = r.headers.get("X-RateLimit-Reset")
                if reset and reset.isdigit():
                    wait_s = max(0, int(reset) - int(time.time())) + 1
                    print(f"Rate limited. Sleeping {wait_s}s...")
                    time.sleep(wait_s)
                    continue

            r.raise_for_status()
            return r.json()

        except Exception as e:
            last_exc = e
            print(f"Request failed (attempt {attempt}/3): {e}")
            time.sleep(1.5 * attempt)

    raise RuntimeError(f"GitHub request failed after retries: {last_exc}")


def get_merged_pr_count(owner: str, repo: str, username: str) -> int:
    """
    Count merged PRs created by `username` in `owner/repo`.
    Uses Search API total_count.
    """
    q = f"repo:{owner}/{repo} is:pr is:merged author:{username} -is:draft"
    data = github_get(f"{API}/search/issues", params={"q": q, "per_page": 1})
    return int(data.get("total_count", 0))


def update_readme_inplace(path: str, counts: dict[str, int]) -> None:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace the **...** immediately before the marker <!--KEY-->
    # Example cell: **{{DIFY_PRS}}** <!--DIFY_PRS--> ▸ [View](...)
    for key, value in counts.items():
        marker = f"<!--{key}-->"
        # **anything** <!--KEY-->  -> **value** <!--KEY-->
        pattern = rf"\*\*[^*]+\*\*\s*{re.escape(marker)}"
        repl = f"**{value}** {marker}"

        new_content, n = re.subn(pattern, repl, content)
        if n == 0:
            raise RuntimeError(
                f"Marker not found or pattern mismatch for {key}. "
                f"Make sure README contains something like: **...** <!--{key}-->"
            )
        content = new_content

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main():
    counts = {}
    for key, (owner, repo) in REPOS.items():
        c = get_merged_pr_count(owner, repo, USERNAME)
        counts[key] = c
        print(f"{key} ({owner}/{repo}): {c}")

    update_readme_inplace(README_PATH, counts)


if __name__ == "__main__":
    main()
