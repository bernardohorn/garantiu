import re

import git

_RENAME_BRACES_RE = re.compile(r"^(.*)\{.* => (.*)\}(.*)$")


def _resolve_renamed_path(path: str) -> str:
    """
    git diff --numstat reports renames either as "{old => new}" with a
    shared prefix/suffix, or as "old/path => new/path" when nothing is
    shared. Resolve both forms to the file's current (new) path.
    """
    match = _RENAME_BRACES_RE.match(path)
    if match:
        prefix, new, suffix = match.groups()
        return f"{prefix}{new}{suffix}"
    if " => " in path:
        return path.split(" => ")[-1]
    return path


def get_changed_files(repo_path: str, base_ref: str, head_ref: str) -> list[dict]:
    """
    Returns changed files between base_ref and head_ref as a list of dicts:
    {"path": str, "module": str, "lines_added": int, "lines_removed": int}.
    module is the top-level directory of path, or the filename itself if the
    file lives at the repo root.
    """
    with git.Repo(repo_path) as repo:
        numstat = repo.git.diff(base_ref, head_ref, "--numstat")

    results = []
    for line in numstat.splitlines():
        if not line.strip():
            continue
        added_str, removed_str, path = line.split("\t")
        added = 0 if added_str == "-" else int(added_str)
        removed = 0 if removed_str == "-" else int(removed_str)
        path = _resolve_renamed_path(path)
        module = path.split("/")[0] if "/" in path else path
        results.append({
            "path": path,
            "module": module,
            "lines_added": added,
            "lines_removed": removed,
        })
    return results
