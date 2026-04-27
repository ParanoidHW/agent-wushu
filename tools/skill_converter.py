#!/usr/bin/env python3
"""
Skill Converter - 跨平台 Skill 格式转换工具

支持将不同平台的 skill 目录和格式进行互相转换。

平台支持:
- claude: Claude Code (Anthropic)
- codex: OpenAI Codex
- opencode: OpenCode
- openclaw: OpenClaw
- cursor: Cursor

用法:
    python skill_converter.py convert <source_dir> <target_platform> -o <output_dir>
    python skill_converter.py batch <source_dir> <target_platform> -o <output_dir>
    python skill_converter.py list-platforms
"""

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Optional
import yaml


# 平台配置
PLATFORM_CONFIGS = {
    "claude": {
        "name": "Claude Code",
        "frontmatter_fields": ["name", "description", "license"],
        "title_template": "# {skill_name} Skill",
        "title_pattern": r"#\s*\S+\s+Skill",
        "description_prefix": "Use this skill when",
        "trigger_format": "Claude Code skill format",
    },
    "codex": {
        "name": "Codex",
        "frontmatter_fields": ["name", "description"],
        "title_template": "# {skill_name} for Codex",
        "title_pattern": r"#\s*\S+\s+for\s+Codex",
        "description_prefix": "Use when",
        "trigger_format": "Codex skill format",
    },
    "opencode": {
        "name": "OpenCode",
        "frontmatter_fields": ["name", "description"],
        "title_template": "# {skill_name} for OpenCode",
        "title_pattern": r"#\s*\S+\s+for\s+OpenCode",
        "description_prefix": "Use this skill when",
        "trigger_format": "OpenCode skill format",
    },
    "openclaw": {
        "name": "OpenClaw",
        "frontmatter_fields": ["name", "description"],
        "title_template": "# {skill_name} for OpenClaw",
        "title_pattern": r"#\s*\S+\s+for\s+OpenClaw",
        "description_prefix": "Use this skill when",
        "trigger_format": "OpenClaw skill format",
    },
    "cursor": {
        "name": "Cursor",
        "frontmatter_fields": ["name", "description", "version"],
        "title_template": "# {skill_name}",
        "title_pattern": r"#\s*\S+",
        "description_prefix": "A Cursor AI skill for",
        "trigger_format": "Cursor skill format",
    },
}


def parse_skill_file(file_path: Path) -> dict:
    """解析 SKILL.md 文件，提取 frontmatter 和内容"""
    content = file_path.read_text(encoding="utf-8")

    # 解析 YAML frontmatter
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1].strip()
            body = parts[2].strip()
            try:
                frontmatter = yaml.safe_load(fm_text) or {}
            except yaml.YAMLError:
                print(f"Warning: Failed to parse frontmatter in {file_path}")

    return {
        "frontmatter": frontmatter,
        "body": body,
        "raw": content,
    }


def detect_platform(skill_data: dict) -> Optional[str]:
    """检测 skill 文件所属的平台"""
    body = skill_data["body"]
    fm = skill_data["frontmatter"]

    # 从标题检测（最准确）
    for platform, config in PLATFORM_CONFIGS.items():
        # 检查标题是否匹配平台特定格式
        first_line = body.split("\n")[0]
        if re.search(config["title_pattern"], first_line, re.IGNORECASE):
            return platform

    # 从 frontmatter 检测
    if "license" in fm:
        return "claude"

    # 从描述中检测平台引用
    description = fm.get("description", "")
    for platform, config in PLATFORM_CONFIGS.items():
        if config["name"] in description:
            return platform

    # 默认假设为通用格式
    return None


def convert_to_platform(
    skill_data: dict, source_platform: Optional[str], target_platform: str, force: bool = False
) -> tuple[str, bool]:
    """将 skill 转换为目标平台格式

    返回: (转换后的内容, 是否实际进行了转换)
    """
    target_config = PLATFORM_CONFIGS[target_platform]
    fm = skill_data["frontmatter"]
    body = skill_data["body"]

    # 检查是否源平台和目标平台相同
    if source_platform == target_platform and not force:
        return skill_data["raw"], False

    # 提取 skill name
    skill_name = fm.get("name", "unknown-skill")

    # 处理标题
    first_line = body.split("\n")[0]
    rest_content = body[len(first_line):].lstrip("\n")

    # 移除现有标题中的平台后缀
    new_title = re.sub(
        r"for\s+(Codex|OpenCode|OpenClaw|Cursor|Claude(?: Code)?)",
        "",
        first_line,
        flags=re.IGNORECASE
    ).strip()

    # 移除 "Skill" 后缀（如果存在）以便重新格式化
    new_title = re.sub(r"\s+Skill$", "", new_title, flags=re.IGNORECASE).strip()
    new_title = new_title.replace("# ", "").strip()

    # 根据目标平台构建新标题
    if target_platform == "claude":
        new_title = f"# {new_title} Skill"
    elif target_platform == "cursor":
        new_title = f"# {new_title}"
    else:
        new_title = f"# {new_title} for {target_config['name']}"

    # 组合新内容
    body = f"{new_title}\n\n{rest_content}"

    # 调整 description 格式
    description = fm.get("description", "")
    if description:
        # 移除源平台特定的触发词格式
        desc_patterns = [
            r"Use when the user wants (Codex|OpenCode|OpenClaw|Cursor|Claude)",
            r"Use this skill when the user wants (Codex|OpenCode|OpenClaw|Cursor|Claude)",
        ]
        for pattern in desc_patterns:
            description = re.sub(pattern, "Use when the user wants", description)

        # 根据目标平台调整描述开头
        if target_platform in ["codex"]:
            # Codex 使用简洁的 "Use when"
            if description.startswith("Use this skill when"):
                description = description.replace("Use this skill when", "Use when")
        elif target_platform == "cursor":
            # Cursor 使用 "A Cursor AI skill for"
            if not description.startswith("A Cursor AI skill"):
                description = f"A Cursor AI skill for {description.lower().lstrip('use when use this skill when ')}"

    # 构建新的 frontmatter
    new_fm = {}
    for field in target_config["frontmatter_fields"]:
        if field in fm:
            # 对于 description，使用调整后的版本
            if field == "description" and description:
                new_fm[field] = description
            else:
                new_fm[field] = fm[field]
        elif field == "name":
            new_fm["name"] = skill_name
        elif field == "description":
            new_fm["description"] = description
        elif field == "version":
            new_fm["version"] = "1.0.0"

    # 构建输出
    fm_yaml = yaml.dump(new_fm, default_flow_style=False, sort_keys=False)
    output = f"---\n{fm_yaml}---\n\n{body}"

    return output, True


def convert_single_skill(
    source_path: Path, target_platform: str, output_path: Optional[Path] = None, force: bool = False
) -> tuple[Path, bool]:
    """转换单个 skill 文件

    返回: (输出路径, 是否实际进行了转换)
    """
    skill_data = parse_skill_file(source_path)
    source_platform = detect_platform(skill_data)

    # 检查源平台和目标平台是否相同
    if source_platform == target_platform and not force:
        print(f"⚠️  Skip: {source_path} (already in {target_platform} format, use --force to override)")

        # 如果指定了输出路径，复制原文件
        if output_path:
            shutil.copy(source_path, output_path)
            print(f"   Copied original file to: {output_path}")
            return output_path, False
        return source_path, False

    converted_content, was_converted = convert_to_platform(
        skill_data, source_platform, target_platform, force
    )

    # 确定输出路径
    if output_path:
        target_path = output_path
    else:
        # 在源文件同目录创建目标平台版本
        target_path = source_path.parent / f"SKILL.{target_platform}.md"

    target_path.write_text(converted_content, encoding="utf-8")

    if was_converted:
        print(f"✅ Converted: {source_path} ({source_platform or 'generic'}) -> {target_platform}")
    else:
        print(f"📋 Copied: {source_path} -> {target_path} (no conversion needed)")

    return target_path, was_converted


def convert_skill_directory(
    source_dir: Path, target_platform: str, output_dir: Optional[Path] = None, force: bool = False
) -> tuple[list[Path], int]:
    """转换整个 skill 目录

    返回: (转换后的路径列表, 实际转换的数量)
    """
    converted_paths = []
    converted_count = 0

    # 查找 SKILL.md 文件
    skill_files = list(source_dir.glob("**/SKILL.md"))

    if not skill_files:
        print(f"Warning: No SKILL.md found in {source_dir}")
        return converted_paths, converted_count

    for skill_file in skill_files:
        relative_path = skill_file.relative_to(source_dir)

        if output_dir:
            target_path = output_dir / relative_path.parent / "SKILL.md"
            target_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            target_path = skill_file.parent / f"SKILL.{target_platform}.md"

        path, was_converted = convert_single_skill(skill_file, target_platform, target_path, force)
        converted_paths.append(path)
        if was_converted:
            converted_count += 1

    return converted_paths, converted_count


def batch_convert(
    source_dir: Path, target_platforms: list[str], output_dir: Optional[Path] = None, force: bool = False
) -> dict[str, tuple[list[Path], int]]:
    """批量转换到多个平台"""
    results = {}

    for platform in target_platforms:
        platform_output = output_dir / platform if output_dir else None
        paths, count = convert_skill_directory(source_dir, platform, platform_output, force)
        results[platform] = (paths, count)

        total = len(paths)
        if count == 0 and total > 0:
            print(f"\n📦 {platform}: {total} skills (all already in target format, use --force)")
        else:
            print(f"\n📦 {platform}: Converted {count}/{total} skills")

    return results


def list_platforms():
    """列出支持的平台"""
    print("\n支持的平台:")
    print("-" * 50)
    for platform, config in PLATFORM_CONFIGS.items():
        print(f"  {platform:<12} - {config['name']}")
        print(f"               Fields: {', '.join(config['frontmatter_fields'])}")
    print("-" * 50)
    print(f"\n总计: {len(PLATFORM_CONFIGS)} 个平台")


def main():
    parser = argparse.ArgumentParser(
        description="Skill Converter - 跨平台 Skill 格式转换工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 轗换单个 skill 文件到 Claude 格式
  python skill_converter.py convert ./skills/pptx/SKILL.md claude

  # 轗换目录下所有 skill 到 Codex 格式，输出到指定目录
  python skill_converter.py convert ./skills/ codex -o ./output/

  # 批量转换到多个平台
  python skill_converter.py batch ./skills/ claude codex opencode

  # 强制转换（即使源格式和目标格式相同）
  python skill_converter.py convert ./skills/ claude --force

  # 列出支持的平台
  python skill_converter.py list-platforms
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # convert 命令
    convert_parser = subparsers.add_parser("convert", help="转换单个文件或目录")
    convert_parser.add_argument("source", help="源 skill 文件或目录路径")
    convert_parser.add_argument(
        "target",
        choices=list(PLATFORM_CONFIGS.keys()),
        help="目标平台",
    )
    convert_parser.add_argument("-o", "--output", help="输出路径")
    convert_parser.add_argument("-f", "--force", action="store_true",
                                 help="强制转换，即使源格式和目标格式相同")

    # batch 命令
    batch_parser = subparsers.add_parser("batch", help="批量转换到多个平台")
    batch_parser.add_argument("source", help="源 skill 目录路径")
    batch_parser.add_argument(
        "targets",
        nargs="+",
        choices=list(PLATFORM_CONFIGS.keys()),
        help="目标平台列表",
    )
    batch_parser.add_argument("-o", "--output", help="输出目录")
    batch_parser.add_argument("-f", "--force", action="store_true",
                               help="强制转换，即使源格式和目标格式相同")

    # list-platforms 命令
    subparsers.add_parser("list-platforms", help="列出支持的平台")

    args = parser.parse_args()

    if args.command == "list-platforms":
        list_platforms()
        return

    source_path = Path(args.source)
    if not source_path.exists():
        print(f"Error: Source path not found: {source_path}")
        sys.exit(1)

    output_path = Path(args.output) if args.output else None
    force = args.force if hasattr(args, 'force') else False

    if args.command == "convert":
        if source_path.is_file():
            convert_single_skill(source_path, args.target, output_path, force)
        else:
            paths, count = convert_skill_directory(source_path, args.target, output_path, force)
            if count == 0 and len(paths) > 0:
                print(f"\n提示: 所有 skills 已是 {args.target} 格式，使用 --force 强制转换")

    elif args.command == "batch":
        batch_convert(source_path, args.targets, output_path, force)


if __name__ == "__main__":
    main()