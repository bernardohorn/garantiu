import re

import git

BUG_COMMIT_PATTERN = re.compile(
    r"\b(fix|fixes|fixed|closes|resolve|resolves|bug|corrige|corrigido)\b",
    re.IGNORECASE,
)


def get_bug_fix_commits(repo_path: str, ref: str = "HEAD") -> list[dict]:
    """
    Scans history reachable from ref and returns commits whose message matches
    BUG_COMMIT_PATTERN, as {"hash": str, "message": str, "files": list[str]}.
    """
    results = []
    with git.Repo(repo_path) as repo:
        for commit in repo.iter_commits(ref):
            if BUG_COMMIT_PATTERN.search(commit.message):
                results.append({
                    "hash": commit.hexsha,
                    "message": commit.message.strip(),
                    "files": list(commit.stats.files.keys()),
                })
    return results


def build_bug_history(repo_path: str, ref: str = "HEAD") -> dict:
    """Return per-file fix counts in the history reachable from ref."""
    history: dict = {}
    for commit in get_bug_fix_commits(repo_path, ref=ref):
        for path in commit["files"]:
            history[path] = history.get(path, 0) + 1
    return history


def bug_history_detail_by_module(
    repo_path: str, module: str, ref: str = "HEAD"
) -> list[dict]:
    """Return fixes reachable from ref once each, newest first, with dates."""
    results = []
    with git.Repo(repo_path) as repo:
        for data in get_bug_fix_commits(repo_path, ref=ref):
            if any(path.split("/")[0] == module for path in data["files"]):
                commit = repo.commit(data["hash"])
                results.append((commit.committed_date, {
                    "hash": data["hash"],
                    "message": data["message"],
                    "date": commit.committed_datetime.date().isoformat(),
                }))
    results.sort(key=lambda item: item[0], reverse=True)
    return [detail for _, detail in results]
