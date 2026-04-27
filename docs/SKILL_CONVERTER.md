# Skill Converter 工具

跨平台 Skill 格式转换工具，支持将不同 Agent 平台的 skill 目录和格式进行互相转换。

## 支持平台

| 平台 | 标识符 | 说明 |
|------|--------|------|
| Claude Code | `claude` | Anthropic 官方 Claude Code |
| Codex | `codex` | OpenAI Codex |
| OpenCode | `opencode` | OpenCode |
| OpenClaw | `openclaw` | OpenClaw |
| Cursor | `cursor` | Cursor IDE |

## 平台格式差异

### Claude Code 格式

```yaml
---
name: pptx
description: "Use this skill any time a .pptx file is involved..."
license: MIT
---

# PPTX Skill

[内容...]
```

**特点：**
- YAML frontmatter 包含 `name`, `description`, `license`
- 标题简洁：`# PPTX Skill`
- 描述详细，包含触发条件

### CLI-Anything 系列格式（Codex/OpenCode/OpenClaw）

```yaml
---
name: cli-anything
description: Use when the user wants Codex to build...
---

# CLI-Anything for Codex

[内容...]
```

**特点：**
- YAML frontmatter 包含 `name`, `description`
- 标题包含平台名：`# CLI-Anything for Codex`
- 描述中明确提及目标平台

### Cursor 格式

```yaml
---
name: pptx
description: A Cursor AI skill for PPTX manipulation
version: 1.0.0
---

# pptx

[内容...]
```

**特点：**
- YAML frontmatter 包含 `name`, `description`, `version`
- 标题使用小写名称

## 安装

```bash
# 无需额外依赖，仅需 Python 3.8+ 和 PyYAML
pip install pyyaml
```

## 使用方法

### 基本命令

```bash
# 列出支持的平台
python tools/skill_converter.py list-platforms

# 转换单个文件
python tools/skill_converter.py convert <source_file> <target_platform>

# 转换整个目录
python tools/skill_converter.py convert <source_dir> <target_platform>

# 批量转换到多个平台
python tools/skill_converter.py batch <source_dir> <platform1> <platform2> ...
```

### 示例

#### 转换单个 skill 文件

```bash
# 将 Claude skill 转换为 Codex 格式
python tools/skill_converter.py convert skills/anthropics-pptx/skills/pptx/SKILL.md codex

# 输出到指定路径
python tools/skill_converter.py convert skills/pptx/SKILL.md claude -o output/SKILL.md
```

#### 转换整个目录

```bash
# 将 skills 目录转换为 OpenCode 格式
python tools/skill_converter.py convert skills/ opencode -o output/skills/

# 转换 CLI-Anything skills 到 Claude 格式
python tools/skill_converter.py convert plugins/opencode-commands/skills/ claude -o skills/claude-skills/
```

#### 批量转换

```bash
# 转换到所有支持的平台
python tools/skill_converter.py batch skills/ claude codex opencode openclaw cursor

# 转换到指定平台
python tools/skill_converter.py batch skills/ claude codex -o converted/
```

### 输出目录结构

批量转换后的目录结构：

```
converted/
├── claude/
│   └── SKILL.md
├── codex/
│   └── SKILL.md
├── opencode/
│   └── SKILL.md
└── ...
```

## 转换规则

### Frontmatter 转换

| 源平台 | 目标平台 | 转换内容 |
|--------|----------|----------|
| Claude | CLI-Any | 移除 `license`，简化描述 |
| CLI-Any | Claude | 添加 `license`，扩展描述 |
| Any | Cursor | 添加 `version` |

### 内容转换

1. **标题调整**：添加或移除平台名称后缀
2. **描述标准化**：调整触发条件描述格式
3. **平台特定内容**：替换平台名称引用

## 工作原理

```
输入 SKILL.md
    │
    ▼
解析 YAML frontmatter
    │
    ▼
检测源平台格式
    │
    ▼
提取 skill 元数据
    │
    ▼
应用目标平台模板
    │
    ├── 调整 frontmatter 字段
    ├── 修改标题格式
    └── 标准化描述
    │
    ▼
输出转换结果
```

## 扩展新平台

在 `tools/skill_converter.py` 的 `PLATFORM_CONFIGS` 中添加新配置：

```python
"new-platform": {
    "name": "NewPlatform",
    "frontmatter_fields": ["name", "description"],
    "title_template": "# {skill_name} for NewPlatform",
    "description_prefix": "Use this skill when",
    "trigger_format": "NewPlatform skill format",
},
```

## 注意事项

1. **格式兼容性**：某些平台可能有额外的要求字段，转换后需手动检查
2. **内容一致性**：核心 skill 内容保持不变，仅调整格式
3. **许可证处理**：Claude 格式包含 `license` 字段，其他平台可能不需要
4. **自定义 skill**：对于高度定制化的 skill，可能需要手动调整

---

*文档版本: 2026-04-27*