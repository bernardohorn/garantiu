import git


def get_changed_files(repo_path: str, base_ref: str, head_ref: str) -> list[dict]:
    """
    Returns changed files between base_ref and head_ref as a list of dicts:
    {"path": str, "module": str, "lines_added": int, "lines_removed": int}.
    module is the top-level directory of path, or the filename itself if the
    file lives at the repo root.
    """
    repo = git.Repo(repo_path)
    numstat = repo.git.diff(base_ref, head_ref, "--numstat")

    results = []
    for line in numstat.splitlines():
        if not line.strip():
            continue
        added_str, removed_str, path = line.split("\t")
        added = 0 if added_str == "-" else int(added_str)
        removed = 0 if removed_str == "-" else int(removed_str)
        module = path.split("/")[0] if "/" in path else path
        results.append({
            "path": path,
            "module": module,
            "lines_added": added,
            "lines_removed": removed,
        })
    return results
