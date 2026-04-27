# Skill 部署指南

克隆 skill 后，需要将其放置到对应平台的正确目录位置才能生效。本文档说明各平台的 skill 安装路径和部署方法。

---

## Claude Code

### 安装位置

| 类型 | 路径 | 适用范围 |
|------|------|----------|
| **个人 Skill** | `~/.claude/skills/<skill-name>/SKILL.md` | 所有项目 |
| **项目 Skill** | `.claude/skills/<skill-name>/SKILL.md` | 当前项目 |
| **插件 Skill** | `<plugin>/skills/<skill-name>/SKILL.md` | 插件启用时 |

### 部署方法

#### 方法 1: 复制到个人 skill 目录（推荐）

适用于想在所有项目中使用的 skill：

```bash
# 从 Agent Wushu 复制 skill
cp -r skills/anthropics-pptx/skills/pptx ~/.claude/skills/pptx

# 或使用软链接（便于更新）
ln -s $(pwd)/skills/anthropics-pptx/skills/pptx ~/.claude/skills/pptx
```

#### 方法 2: 复制到项目 skill 目录

适用于仅在特定项目中使用的 skill：

```bash
# 在项目目录下创建
mkdir -p your-project/.claude/skills/pptx
cp -r skills/anthropics-pptx/skills/pptx/* your-project/.claude/skills/pptx/
```

#### 方法 3: 使用 --add-dir

不复制文件，直接添加 Agent Wushu 的 skills 目录：

```bash
# 启动 Claude Code 时添加目录
claude --add-dir /path/to/agent-wushu/skills/anthropics-pptx/skills/pptx
```

**注意**: `--add-dir` 方式下，skill 会被自动发现，但其他 `.claude/` 配置不会加载。

### 目录结构要求

Claude Code skill 目录结构：

```
.claude/skills/<skill-name>/
├── SKILL.md           # 必需 - 主指令文件
├── reference.md       # 可选 - 详细参考文档
├── examples.md        # 可选 - 使用示例
├── scripts/           # 可选 - 辅助脚本
│   └── helper.py
└── templates/         # 可选 - 模板文件
```

### 验证安装

```bash
# 检查 skill 是否被识别
claude --print-skills

# 或在 Claude Code 中询问
# "What skills are available?"
```

---

## CLI-Anything 系列 (Codex / OpenCode / OpenClaw)

CLI-Anything 系列平台使用相似的 skill 结构，主要差异在于 frontmatter 和标题格式。

### 安装位置

| 平台 | 推荐路径 |
|------|----------|
| Codex | `.codex/skills/<skill-name>/SKILL.md` |
| OpenCode | `.opencode/skills/<skill-name>/SKILL.md` |
| OpenClaw | `.openclaw/skills/<skill-name>/SKILL.md` |

**或使用 CLI-Anything harness 结构**:

```
<software>/
└── agent-harness/
    └── cli_anything/
        └── <software>/
            └── skills/
                └── SKILL.md
```

### 部署方法

#### 方法 1: 转换后部署

使用 `skill_converter.py` 转换格式后部署：

```bash
# 转换 Claude skill 到目标平台格式
python tools/skill_converter.py convert \
  skills/anthropics-pptx/skills/pptx/SKILL.md \
  opencode \
  -o .opencode/skills/pptx/SKILL.md

# 或批量转换整个目录
python tools/skill_converter.py batch \
  skills/ \
  codex opencode \
  -o converted/
```

#### 方法 2: 直接复制 CLI-Anything skills

CLI-Anything 格式的 skill 可以直接使用：

```bash
# 复制 OpenCode 兼容的 skill
cp plugins/opencode-commands/skills/cli-anything-blender/SKILL.md \
  .opencode/skills/blender/SKILL.md
```

### 格式差异

不同平台的 frontmatter 和标题格式：

| 平台 | Frontmatter | 标题格式 |
|------|-------------|----------|
| Claude | `name`, `description`, `license` | `# <name> Skill` |
| Codex | `name`, `description` | `# <name> for Codex` |
| OpenCode | `name`, `description` | `# <name> for OpenCode` |
| OpenClaw | `name`, `description` | `# <name> for OpenClaw` |
| Cursor | `name`, `description`, `version` | `# <name>` |

---

## Cursor IDE

### 安装位置

Cursor 的 skill 通常作为 `.cursorrules` 或独立的 skill 文件存在：

```
your-project/
├── .cursorrules        # 项目规则（类似 CLAUDE.md）
└── .cursor/
    └── skills/
        └── <skill-name>/SKILL.md
```

### 部署方法

```bash
# 转换为 Cursor 格式
python tools/skill_converter.py convert \
  skills/anthropics-pptx/skills/pptx/SKILL.md \
  cursor \
  -o .cursor/skills/pptx/SKILL.md
```

---

## 快速部署脚本

Agent Wushu 提供了一个便捷的部署脚本模板：

```bash
#!/bin/bash
# deploy_skill.sh - 快速部署 skill 到目标平台

SKILL_NAME=$1
TARGET_PLATFORM=$2
TARGET_PROJECT=$3

case $TARGET_PLATFORM in
  claude)
    DEST="$HOME/.claude/skills/$SKILL_NAME"
    ;;
  claude-project)
    DEST="$TARGET_PROJECT/.claude/skills/$SKILL_NAME"
    ;;
  opencode)
    DEST="$TARGET_PROJECT/.opencode/skills/$SKILL_NAME"
    ;;
  codex)
    DEST="$TARGET_PROJECT/.codex/skills/$SKILL_NAME"
    ;;
  cursor)
    DEST="$TARGET_PROJECT/.cursor/skills/$SKILL_NAME"
    ;;
  *)
    echo "Unknown platform: $TARGET_PLATFORM"
    exit 1
    ;;
esac

# 转换并部署
python tools/skill_converter.py convert \
  "skills/$SKILL_NAME/SKILL.md" \
  "$TARGET_PLATFORM" \
  -o "$DEST/SKILL.md"

echo "Deployed to: $DEST"
```

**使用示例**:

```bash
# 部署到 Claude Code（个人）
./deploy_skill.sh anthropics-pptx claude

# 部署到 OpenCode 项目
./deploy_skill.sh nanobanana-ppt opencode /path/to/project

# 部署到 Cursor 项目
./deploy_skill.sh anthropics-pptx cursor /path/to/project
```

---

## 常见问题

### Q: Skill 没有被识别？

**Claude Code**: 
- 确保 `SKILL.md` 文件存在且格式正确
- 检查 frontmatter 中有 `description` 字段
- 尝试手动调用: `/skill-name`

**CLI-Anything 系列**:
- 检查标题是否包含平台名称（如 `# pptx for OpenCode`）
- 确认 frontmatter 格式符合平台要求

### Q: 多个平台共用一个 skill？

使用软链接或直接在各自平台目录创建副本：

```bash
# Claude Code 个人 skill
ln -s ~/.claude/skills/pptx /path/to/project/.opencode/skills/pptx

# 或使用 skill_converter 批量转换
python tools/skill_converter.py batch skills/pptx claude opencode cursor
```

### Q: 如何更新已部署的 skill？

**软链接方式**: 更新 Agent Wushu 仓库即可

```bash
cd /path/to/agent-wushu
git pull
```

**复制方式**: 需要重新复制或转换

```bash
# 更新单个 skill
cp -r skills/anthropics-pptx/skills/pptx ~/.claude/skills/pptx

# 或使用脚本重新部署
./deploy_skill.sh anthropics-pptx claude
```

---

## 总结

| 平台 | 默认位置 | 是否需要转换 |
|------|----------|--------------|
| Claude Code | `~/.claude/skills/` | Claude 格式不需要 |
| OpenCode | `.opencode/skills/` | 需要（CLI-Anything 格式可直接用） |
| Codex | `.codex/skills/` | 需要 |
| Cursor | `.cursor/skills/` | 需要 |

推荐使用 `skill_converter.py` 进行格式转换，或使用 CLI-Anything 格式的 skill（兼容 OpenCode/Codex/OpenClaw）。