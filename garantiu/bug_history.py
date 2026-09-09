import re

import git

BUG_COMMIT_PATTERN = re.compile(
    r"\b(fix|fixes|fixed|closes|resolve|resolves|bug|corrige|corrigido)\b",
    re.IGNORECASE,
)


def get_bug_fix_commits(repo_path: str) -> list[dict]:
    """
    Scans the full commit history and returns commits whose message matches
    BUG_COMMIT_PATTERN, as {"hash": str, "message": str, "files": list[str]}.
    """
    repo = git.Repo(repo_path)
    results = []
    for commit in repo.iter_commits():
        if BUG_COMMIT_PATTERN.search(commit.message):
            results.append({
                "hash": commit.hexsha,
                "message": commit.message.strip(),
                "files": list(commit.stats.files.keys()),
            })
    return results


def build_bug_history(repo_path: str) -> dict:
    """Returns {file_path: count_of_bug_fix_commits_touching_it}."""
    history: dict = {}
    for commit in get_bug_fix_commits(repo_path):
        for path in commit["files"]:
            history[path] = history.get(path, 0) + 1
    return history
