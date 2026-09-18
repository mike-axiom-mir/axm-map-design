#!/usr/bin/env python3
"""Bind the local Python source dependency closure for a receiver entry point.

Technical Art uses this only as provenance/evidence plumbing. It does not decide
any domain policy and it does not modify the inspected repository. The closure is
limited to tracked Python files inside one declared package root. Standard-library
and third-party imports are outside this source-identity claim. Ambiguous relative
imports or dynamic imports fail closed instead of being guessed through.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
from pathlib import Path, PurePosixPath

SCHEMA = "axm.technical-art-python-local-dependency-closure/v0.1"


def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _tracked_blob(root: Path, relative: str, data: bytes) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", f"HEAD:{relative}"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"dependency is not tracked at HEAD: {relative}") from exc
    observed = result.stdout.strip()
    calculated = _git_blob_sha(data)
    if observed != calculated:
        raise ValueError(f"working-tree dependency differs from HEAD: {relative}")
    return observed


def _inside(path: PurePosixPath, root: PurePosixPath) -> bool:
    return path == root or root in path.parents


def _resolve_relative_import(
    source: PurePosixPath,
    package_root: PurePosixPath,
    node: ast.ImportFrom,
) -> list[PurePosixPath]:
    if node.level < 1:
        return []
    base = source.parent
    for _ in range(node.level - 1):
        base = base.parent
    if not _inside(base, package_root):
        raise ValueError(f"relative import escapes declared package root: {source}")
    if node.module is None:
        raise ValueError(
            f"ambiguous relative import in {source}; explicit module required for exact closure"
        )
    target = base.joinpath(*node.module.split("."))
    file_candidate = target.with_suffix(".py")
    init_candidate = target / "__init__.py"
    return [file_candidate, init_candidate]


def _resolve_absolute_import(
    package_root: PurePosixPath,
    package_name: str,
    node: ast.Import | ast.ImportFrom,
) -> list[PurePosixPath]:
    names: list[str] = []
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        names.append(node.module)
    elif isinstance(node, ast.Import):
        names.extend(alias.name for alias in node.names)
    candidates: list[PurePosixPath] = []
    for name in names:
        if name == package_name:
            candidates.append(package_root / "__init__.py")
        elif name.startswith(package_name + "."):
            tail = name.split(".")[1:]
            target = package_root.joinpath(*tail)
            candidates.extend([target.with_suffix(".py"), target / "__init__.py"])
    return candidates


def _has_dynamic_import(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "__import__":
            return True
        if isinstance(func, ast.Attribute) and func.attr == "import_module":
            return True
    return False


def python_local_dependency_closure(
    repository_root: Path,
    entry_path: str,
    package_root_path: str,
) -> dict[str, str]:
    root = repository_root.resolve()
    entry = PurePosixPath(entry_path)
    package_root = PurePosixPath(package_root_path)
    if entry.suffix != ".py" or not _inside(entry, package_root):
        raise ValueError("entry must be a Python file inside the declared package root")
    package_name = package_root.name

    pending = [entry]
    observed: dict[str, str] = {}
    while pending:
        relative_path = pending.pop(0)
        relative = relative_path.as_posix()
        if relative in observed:
            continue
        absolute = (root / relative).resolve()
        try:
            absolute.relative_to(root)
        except ValueError as exc:
            raise ValueError("dependency escapes repository root") from exc
        if not absolute.is_file():
            raise ValueError(f"dependency missing: {relative}")
        data = absolute.read_bytes()
        observed[relative] = _tracked_blob(root, relative, data)
        try:
            tree = ast.parse(data.decode("utf-8"), filename=relative)
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise ValueError(f"dependency is not valid UTF-8 Python: {relative}") from exc
        if _has_dynamic_import(tree):
            raise ValueError(f"dynamic import prevents exact local closure: {relative}")

        candidates: list[PurePosixPath] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                candidates.extend(_resolve_relative_import(relative_path, package_root, node))
                candidates.extend(_resolve_absolute_import(package_root, package_name, node))
            elif isinstance(node, ast.Import):
                candidates.extend(_resolve_absolute_import(package_root, package_name, node))

        for candidate in candidates:
            if not _inside(candidate, package_root):
                raise ValueError(f"local import escapes declared package root: {candidate}")
            candidate_abs = root / candidate.as_posix()
            if candidate_abs.is_file() and candidate.as_posix() not in observed and candidate not in pending:
                pending.append(candidate)

    return dict(sorted(observed.items()))


def build_receipt(repository_root: Path, entry: str, package_root: str) -> dict[str, object]:
    closure = python_local_dependency_closure(repository_root, entry, package_root)
    head = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()
    return {
        "schema": SCHEMA,
        "repository_head": head,
        "entry": PurePosixPath(entry).as_posix(),
        "package_root": PurePosixPath(package_root).as_posix(),
        "local_dependency_closure": closure,
        "local_file_count": len(closure),
        "truth_boundary": {
            "local_tracked_python_source_identity_only": True,
            "standard_library_identity_claimed": False,
            "third_party_runtime_identity_claimed": False,
            "domain_policy_claimed": False,
            "product_modified": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--entry", required=True)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    receipt = build_receipt(args.repo_root, args.entry, args.package_root)
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
