import re

import git

_RENAME_BRACES_RE = re.compile(r"^(.*)\{.* => (.*)\}(.*)$")
AUTO_BASE_REF = "AUTO"
_DOCUMENTATION_SUFFIXES = {
    ".md", ".mdx", ".pdf", ".rst", ".txt", ".adoc",
}


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


def resolve_comparison_base(
    repo: git.Repo, base_ref: str, head_ref: str,
) -> tuple[str, str]:
    """Resolve an explicit base or choose a release-sized automatic range.

    Automatic mode compares from the latest tag reachable before the selected
    head. Repositories without tags fall back to the first commit reachable on
    the head's first-parent history. The returned tuple contains the full SHA
    and a human-readable label.
    """
    head = repo.commit(head_ref)
    requested = base_ref.strip()
    if requested and requested.upper() != AUTO_BASE_REF:
        return repo.commit(requested).hexsha, requested

    if head.parents:
        try:
            tag = repo.git.describe(
                head.parents[0].hexsha, tags=True, abbrev=0,
            ).strip()
        except git.GitCommandError:
            tag = ""
        if tag:
            return repo.commit(tag).hexsha, tag

    roots = repo.git.rev_list(
        "--first-parent", "--max-parents=0", head.hexsha,
    ).splitlines()
    if not roots:
        raise ValueError("Não foi possível localizar o primeiro commit do intervalo.")
    root_sha = roots[0]
    return root_sha, f"primeiro commit ({root_sha[:8]})"


def is_documentation_change(path: str) -> bool:
    """Return whether a changed path is documentation-only."""
    normalized = path.replace("\\", "/").lower()
    if normalized.startswith("docs/"):
        return True
    suffix = "." + normalized.rsplit(".", 1)[-1] if "." in normalized else ""
    return suffix in _DOCUMENTATION_SUFFIXES


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
