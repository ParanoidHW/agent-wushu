#!/usr/bin/env python3
"""
Agent Wushu - Agent Tools/Skills Repository Manager

支持部分克隆子模块，按类别/标签筛选
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import Optional
import yaml


REPO_ROOT = Path(__file__).parent.resolve()
REGISTRY_FILE = REPO_ROOT / "registry.yaml"


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        print(f"Error: registry.yaml not found at {REGISTRY_FILE}")
        sys.exit(1)
    with open(REGISTRY_FILE) as f:
        return yaml.safe_load(f)


def get_category_path(category: str, registry: dict) -> Path:
    categories = registry.get("categories", {})
    if category not in categories:
        print(f"Error: Unknown category '{category}'")
        print(f"Available: {list(categories.keys())}")
        sys.exit(1)
    return REPO_ROOT / categories[category]["path"]


def is_local_module(module: dict) -> bool:
    return module.get("repo") == "local" or bool(module.get("local_path"))


def get_module_path(module: dict, registry: dict) -> Path:
    configured_path = module.get("target_path") or module.get("local_path")
    if configured_path:
        return REPO_ROOT / configured_path

    category = module.get("category")
    name = module.get("name")
    return get_category_path(category, registry) / name


def format_repo_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def is_git_checkout(path: Path) -> bool:
    if not path.is_dir():
        return False

    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def list_modules(registry: dict, category: Optional[str] = None, tags: Optional[list] = None):
    modules = registry.get("modules", [])
    categories = registry.get("categories", {})
    
    filtered = modules
    if category:
        filtered = [m for m in filtered if m.get("category") == category]
    if tags:
        filtered = [m for m in filtered if any(t in m.get("tags", []) for t in tags)]
    
    if not filtered:
        print("No modules found matching criteria")
        return
    
    print(f"\n{'Name':<25} {'Category':<12} {'Tags':<20} Description")
    print("-" * 80)
    for m in filtered:
        name = m.get("name", "")
        cat = m.get("category", "")
        tags_str = ", ".join(m.get("tags", []))
        desc = m.get("description", "")[:40]
        print(f"{name:<25} {cat:<12} {tags_str:<20} {desc}")


def clone_module(module: dict, registry: dict, shallow: bool = True):
    name = module.get("name")
    repo = module.get("repo")
    branch = module.get("branch", "main")
    sparse_paths = module.get("sparse_checkout", [])

    target_path = get_module_path(module, registry)

    if is_local_module(module):
        if target_path.exists():
            print(f"[LOCAL] {name} available at {format_repo_path(target_path)}")
        else:
            print(f"[MISSING] {name} expected at {format_repo_path(target_path)}")
        return
    
    if target_path.exists():
        print(f"[SKIP] {name} already exists at {format_repo_path(target_path)}")
        return
    
    print(f"[CLONE] {name} -> {format_repo_path(target_path)}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    if sparse_paths:
        target_path.mkdir(parents=True, exist_ok=True)
        clone_sparse(repo, target_path, branch, sparse_paths, shallow)
    else:
        clone_full(repo, target_path, branch, shallow)


def clone_sparse(repo: str, target: Path, branch: str, paths: list, shallow: bool):
    has_file_patterns = any(not path.endswith("/") for path in paths)
    sparse_mode = "--no-cone" if has_file_patterns else "--cone"

    init_cmd = ["git", "init"]
    subprocess.run(init_cmd, cwd=target, check=True)
    
    sparse_cmd = ["git", "sparse-checkout", "init", sparse_mode]
    subprocess.run(sparse_cmd, cwd=target, check=True)
    
    remote_cmd = ["git", "remote", "add", "origin", repo]
    subprocess.run(remote_cmd, cwd=target, check=True)
    
    set_cmd = ["git", "sparse-checkout", "set", sparse_mode] + paths
    subprocess.run(set_cmd, cwd=target, check=True)
    
    fetch_ref = f"{branch}:refs/remotes/origin/{branch}"
    fetch_cmd = ["git", "fetch", "--depth=1", "origin", fetch_ref]
    if not shallow:
        fetch_cmd = ["git", "fetch", "origin", fetch_ref]
    subprocess.run(fetch_cmd, cwd=target, check=True)
    
    checkout_cmd = ["git", "checkout", "-B", branch, f"origin/{branch}"]
    subprocess.run(checkout_cmd, cwd=target, check=True)
    upstream_cmd = ["git", "branch", "--set-upstream-to", f"origin/{branch}", branch]
    subprocess.run(upstream_cmd, cwd=target, check=True)
    
    print(f"  Sparse checkout: {paths}")


def clone_full(repo: str, target: Path, branch: str, shallow: bool):
    cmd = ["git", "clone"]
    if shallow:
        cmd.extend(["--depth=1"])
    cmd.extend(["-b", branch, repo, str(target)])
    subprocess.run(cmd, check=True)


def clone_by_filter(registry: dict, names: Optional[list] = None,
                    category: Optional[str] = None, tags: Optional[list] = None,
                    shallow: bool = True):
    modules = registry.get("modules", [])
    
    to_clone = modules
    if names:
        to_clone = [m for m in to_clone if m.get("name") in names]
    if category:
        to_clone = [m for m in to_clone if m.get("category") == category]
    if tags:
        to_clone = [m for m in to_clone if any(t in m.get("tags", []) for t in tags)]
    
    if not to_clone:
        print("No modules to clone")
        return
    
    print(f"\nCloning {len(to_clone)} modules...")
    for m in to_clone:
        clone_module(m, registry, shallow)


def update_modules(registry: dict, names: Optional[list] = None):
    modules = registry.get("modules", [])
    
    to_update = modules
    if names:
        to_update = [m for m in to_update if m.get("name") in names]
    
    for m in to_update:
        name = m.get("name")
        target_path = get_module_path(m, registry)

        if is_local_module(m):
            print(f"[SKIP] {name} is local at {format_repo_path(target_path)}")
            continue
        
        if not target_path.exists():
            print(f"[SKIP] {name} not cloned")
            continue

        if not is_git_checkout(target_path):
            print(f"[SKIP] {name} is not a git checkout: {format_repo_path(target_path)}")
            continue
        
        print(f"[UPDATE] {name}")
        subprocess.run(["git", "pull"], cwd=target_path)


def status_modules(registry: dict):
    modules = registry.get("modules", [])
    
    print(f"\n{'Name':<25} {'Status':<15} {'Path'}")
    print("-" * 60)
    
    for m in modules:
        name = m.get("name")
        target_path = get_module_path(m, registry)
        
        if not target_path.exists():
            status = "MISSING" if is_local_module(m) else "NOT_CLONED"
        elif is_local_module(m):
            rel_path = format_repo_path(target_path)
            result = subprocess.run(
                ["git", "status", "--porcelain", "--", rel_path],
                cwd=REPO_ROOT, capture_output=True, text=True
            )
            status = "MODIFIED" if result.stdout else "OK"
        elif not is_git_checkout(target_path):
            status = "NOT_GIT"
        else:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=target_path, capture_output=True, text=True
            )
            if result.stdout:
                status = "MODIFIED"
            else:
                status = "OK"
        
        rel_path = format_repo_path(target_path)
        print(f"{name:<25} {status:<15} {rel_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Agent Wushu - Agent Tools Repository Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wushu list                     # 列出所有模块
  wushu list -c skills           # 列出 skills 类别
  wushu list -t cli,automation   # 列出含 cli 或 automation 标签的模块
  wushu clone cli-anything-skill # 克隆指定模块
  wushu clone -c skills          # 克隆 skills 类别所有模块
  wushu clone -t claude,opencode # 克隆含 claude 或 opencode 标签的模块
  wushu update                   # 更新所有已克隆模块
  wushu status                   # 查看状态
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    list_parser = subparsers.add_parser("list", help="List modules")
    list_parser.add_argument("-c", "--category", help="Filter by category")
    list_parser.add_argument("-t", "--tags", help="Filter by tags (comma-separated)")
    
    clone_parser = subparsers.add_parser("clone", help="Clone modules")
    clone_parser.add_argument("names", nargs="*", help="Module names to clone")
    clone_parser.add_argument("-c", "--category", help="Clone all from category")
    clone_parser.add_argument("-t", "--tags", help="Clone by tags (comma-separated)")
    clone_parser.add_argument("--full", action="store_true", help="Full clone (no shallow)")
    
    update_parser = subparsers.add_parser("update", help="Update cloned modules")
    update_parser.add_argument("names", nargs="*", help="Module names to update")
    
    status_parser = subparsers.add_parser("status", help="Show module status")
    
    args = parser.parse_args()
    registry = load_registry()
    
    tags = None
    if hasattr(args, 'tags') and args.tags:
        tags = [t.strip() for t in args.tags.split(",")]
    
    if args.command == "list":
        list_modules(registry, args.category, tags)
    elif args.command == "clone":
        clone_by_filter(registry, args.names, args.category, tags, not args.full)
    elif args.command == "update":
        update_modules(registry, args.names)
    elif args.command == "status":
        status_modules(registry)


if __name__ == "__main__":
    main()
