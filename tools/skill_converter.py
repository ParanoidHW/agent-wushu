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
        "description_prefix": "Use this skill when",
        "trigger_format": "Claude Code skill format",
    },
    "codex": {
        "name": "Codex",
        "frontmatter_fields": ["name", "description"],
        "title_template": "# {skill_name} for Codex",
        "description_prefix": "Use when",
        "trigger_format": "Codex skill format",
    },
    "opencode": {
        "name": "OpenCode",
        "frontmatter_fields": ["name", "description"],
        "title_template": "# {skill_name} for OpenCode",
        "description_prefix": "Use this skill when",
        "trigger_format": "OpenCode skill format",
    },
    "openclaw": {
        "name": "OpenClaw",
        "frontmatter_fields": ["name", "description"],
        "title_template": "# {skill_name} for OpenClaw",
        "description_prefix": "Use this skill when",
        "trigger_format": "OpenClaw skill format",
    },
    "cursor": {
        "name": "Cursor",
        "frontmatter_fields": ["name", "description", "version"],
        "title_template": "# {skill_name}",
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

    # 从标题检测
    for platform, config in PLATFORM_CONFIGS.items():
        if f"for {config['name']}" in body[:100]:
            return platform

    # 从 frontmatter 检测
    if "license" in fm:
        return "claude"

    # 默认假设为通用格式
    return None


def convert_to_platform(
    skill_data: dict, source_platform: Optional[str], target_platform: str
) -> str:
    """将 skill 转换为目标平台格式"""
    target_config = PLATFORM_CONFIGS[target_platform]
    fm = skill_data["frontmatter"]
    body = skill_data["body"]

    # 提取 skill name
    skill_name = fm.get("name", "unknown-skill")

    # 清理标题中的平台特定内容
    # 移除 "for Codex", "for OpenCode", "for OpenClaw" 等
    body = re.sub(
        r"#\s*\S+\s+for\s+(Codex|OpenCode|OpenClaw|Cursor|Claude)",
        f"# {skill_name} for {target_config['name']}",
        body,
        count=1,
    )

    # 如果标题没被替换，使用模板
    if not body.startswith(f"# {skill_name}"):
        first_line_end = body.find("\n")
        if first_line_end > 0:
            body = f"# {skill_name} for {target_config['name']}\n" + body[first_line_end + 1 :]
        else:
            body = f"# {skill_name} for {target_config['name']}\n\n{body}"

    # 调整 description 格式
    description = fm.get("description", "")
    if description:
        # 移除源平台特定的触发词格式
        desc_patterns = [
            r"Use when the user wants (Codex|OpenCode|OpenClaw|Cursor|Claude)",
            r"Use this skill when the user wants (Codex|OpenCode|OpenClaw|Cursor|Claude)",
        ]
        for pattern in desc_patterns:
            description = re.sub(pattern, f"Use when the user wants", description)

        # 确保描述以目标平台格式开头
        if not description.startswith(target_config["description_prefix"]):
            description = f"{target_config['description_prefix']} {description.lstrip('Use when Use this skill when ')}"

    # 构建新的 frontmatter
    new_fm = {}
    for field in target_config["frontmatter_fields"]:
        if field in fm:
            new_fm[field] = fm[field]
        elif field == "name":
            new_fm["name"] = skill_name
        elif field == "description":
            new_fm["description"] = description

    # 更新 name（如果需要包含平台标识）
    if target_platform in ["codex", "opencode", "openclaw"]:
        # CLI-Anything 风格保持通用 name
        pass
    elif target_platform == "claude":
        # Claude 格式通常使用简短名称
        new_fm["name"] = skill_name

    # 构建输出
    fm_yaml = yaml.dump(new_fm, default_flow_style=False, sort_keys=False)
    output = f"---\n{fm_yaml}---\n\n{body}"

    return output


def convert_single_skill(
    source_path: Path, target_platform: str, output_path: Optional[Path] = None
) -> Path:
    """转换单个 skill 文件"""
    skill_data = parse_skill_file(source_path)
    source_platform = detect_platform(skill_data)

    converted_content = convert_to_platform(skill_data, source_platform, target_platform)

    # 确定输出路径
    if output_path:
        target_path = output_path
    else:
        # 在源文件同目录创建目标平台版本
        target_path = source_path.parent / f"SKILL.{target_platform}.md"

    target_path.write_text(converted_content, encoding="utf-8")
    print(f"✅ Converted: {source_path} -> {target_path}")

    return target_path


def convert_skill_directory(
    source_dir: Path, target_platform: str, output_dir: Optional[Path] = None
) -> list[Path]:
    """转换整个 skill 目录"""
    converted_paths = []

    # 查找 SKILL.md 文件
    skill_files = list(source_dir.glob("**/SKILL.md"))

    if not skill_files:
        print(f"Warning: No SKILL.md found in {source_dir}")
        return converted_paths

    for skill_file in skill_files:
        relative_path = skill_file.relative_to(source_dir)

        if output_dir:
            target_path = output_dir / relative_path.parent / "SKILL.md"
            target_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            target_path = skill_file.parent / f"SKILL.{target_platform}.md"

        converted_paths.append(convert_single_skill(skill_file, target_platform, target_path))

    return converted_paths


def batch_convert(
    source_dir: Path, target_platforms: list[str], output_dir: Optional[Path] = None
) -> dict[str, list[Path]]:
    """批量转换到多个平台"""
    results = {}

    for platform in target_platforms:
        platform_output = output_dir / platform if output_dir else None
        results[platform] = convert_skill_directory(source_dir, platform, platform_output)
        print(f"\n📦 {platform}: Converted {len(results[platform])} skills")

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

    if args.command == "convert":
        if source_path.is_file():
            convert_single_skill(source_path, args.target, output_path)
        else:
            convert_skill_directory(source_path, args.target, output_path)

    elif args.command == "batch":
        batch_convert(source_path, args.targets, output_path)


if __name__ == "__main__":
    main()