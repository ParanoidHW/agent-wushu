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
    category = module.get("category")
    
    target_dir = get_category_path(category, registry) / name
    
    if target_dir.exists():
        print(f"[SKIP] {name} already exists at {target_dir}")
        return
    
    print(f"[CLONE] {name} -> {target_dir}")
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if sparse_paths:
        clone_sparse(repo, target_dir, branch, sparse_paths, shallow)
    else:
        clone_full(repo, target_dir, branch, shallow)


def clone_sparse(repo: str, target: Path, branch: str, paths: list, shallow: bool):
    init_cmd = ["git", "init"]
    subprocess.run(init_cmd, cwd=target, check=True)
    
    sparse_cmd = ["git", "sparse-checkout", "init", "--cone"]
    subprocess.run(sparse_cmd, cwd=target, check=True)
    
    remote_cmd = ["git", "remote", "add", "origin", repo]
    subprocess.run(remote_cmd, cwd=target, check=True)
    
    set_cmd = ["git", "sparse-checkout", "set"] + paths
    subprocess.run(set_cmd, cwd=target, check=True)
    
    fetch_cmd = ["git", "fetch", "--depth=1", "origin", branch]
    if not shallow:
        fetch_cmd = ["git", "fetch", "origin", branch]
    subprocess.run(fetch_cmd, cwd=target, check=True)
    
    checkout_cmd = ["git", "checkout", branch]
    subprocess.run(checkout_cmd, cwd=target, check=True)
    
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
    categories = registry.get("categories", {})
    
    to_update = modules
    if names:
        to_update = [m for m in to_update if m.get("name") in names]
    
    for m in to_update:
        name = m.get("name")
        category = m.get("category")
        target_dir = get_category_path(category, registry) / name
        
        if not target_dir.exists():
            print(f"[SKIP] {name} not cloned")
            continue
        
        print(f"[UPDATE] {name}")
        subprocess.run(["git", "pull"], cwd=target_dir)


def status_modules(registry: dict):
    modules = registry.get("modules", [])
    categories = registry.get("categories", {})
    
    print(f"\n{'Name':<25} {'Status':<15} {'Path'}")
    print("-" * 60)
    
    for m in modules:
        name = m.get("name")
        category = m.get("category")
        target_dir = get_category_path(category, registry) / name
        
        if not target_dir.exists():
            status = "NOT_CLONED"
        else:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=target_dir, capture_output=True, text=True
            )
            if result.stdout:
                status = "MODIFIED"
            else:
                status = "OK"
        
        rel_path = str(target_dir.relative_to(REPO_ROOT))
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