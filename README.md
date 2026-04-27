# Agent Wushu (武术)

Agent 工具/Skills 仓库，集成 GitHub 上开源的 agent 工具、skill、CLI 等。

## 目录结构

```
agent-wushu/
├── skills/          # AI Agent Skills (SKILL.md 等)
├── tools/           # Agent Tools & Utilities
├── clis/            # CLI Tools for Agent Interaction
├── frameworks/      # Agent Frameworks & Libraries
├── plugins/         # Agent Platform Plugins
├── docs/            # 文档目录
├── registry.yaml    # 子模块注册表
├── wushu.py         # 管理脚本
└── README.md
```

## 快速开始

### 前置要求

```bash
pip install pyyaml
```

### 使用方法

```bash
# 列出所有模块
python wushu.py list

# 列出特定类别
python wushu.py list -c skills
python wushu.py list -c plugins

# 列出含特定标签的模块
python wushu.py list -t cli,automation
python wushu.py list -t pptx

# 克隆单个模块
python wushu.py clone anthropics-pptx-skill

# 克隆某个类别的所有模块
python wushu.py clone -c skills

# 按标签克隆
python wushu.py clone -t pptx,video

# 更新已克隆的模块
python wushu.py update

# 查看状态
python wushu.py status
```

## 已集成模块

当前已集成 **2 Skills + 1 Tool + 1 Plugin**。

👉 **详细说明请查看**: [已集成模块文档](./docs/INTEGRATED_MODULES.md)

| 类别 | 数量 | 链接 |
|------|------|------|
| Skills | 2 | [查看详情](./docs/INTEGRATED_MODULES.md#skills) |
| Tools | 1 | [查看详情](./docs/INTEGRATED_MODULES.md#tools) |
| Plugins | 1 | [查看详情](./docs/INTEGRATED_MODULES.md#plugins) |

### 快速概览

**Skills:**
- [Anthropic PPTX Skill](./skills/anthropics-pptx/skills/pptx/) - PPTX 处理
- [NanoBanana PPT Skills](./skills/nanobanana-ppt/) - AI PPT 生成

**Tools:**
- [Skill Converter](./tools/skill_converter.py) - 跨平台格式转换

**Plugins:**
- [OpenCode Commands](./plugins/opencode-commands/) - CLI 工具集

## 部署到各平台

克隆 skill 后，需要部署到对应平台的正确目录才能生效。

👉 **详细部署指南**: [Skill 部署指南](./docs/SKILL_DEPLOYMENT.md)

### 快速部署

```bash
# Claude Code（个人 skill）
cp -r skills/anthropics-pptx/skills/pptx ~/.claude/skills/pptx

# 转换后部署到 OpenCode
python tools/skill_converter.py convert \
  skills/anthropics-pptx/skills/pptx/SKILL.md \
  opencode \
  -o .opencode/skills/pptx/SKILL.md

# 批量转换到多个平台
python tools/skill_converter.py batch skills/ claude opencode cursor -o converted/
```

### 各平台安装位置

| 平台 | 位置 | 说明 |
|------|------|------|
| Claude Code | `~/.claude/skills/` | 个人 skill，全局可用 |
| OpenCode | `.opencode/skills/` | 项目 skill |
| Codex | `.codex/skills/` | 项目 skill |
| Cursor | `.cursor/skills/` | 项目 skill |

## 文档索引

| 文档 | 说明 |
|------|------|
| [已集成模块](./docs/INTEGRATED_MODULES.md) | Skills/Tools/Plugins 详细说明 |
| [部署指南](./docs/SKILL_DEPLOYMENT.md) | 部署 skill 到各平台项目目录 |
| [架构设计](./docs/ARCHITECTURE.md) | 仓库架构和设计原则 |
| [配置规范](./docs/REGISTRY_SPEC.md) | registry.yaml 配置说明 |
| [管理脚本](./docs/WUSHU_CLI.md) | wushu.py 使用指南 |
| [Skill Converter](./docs/SKILL_CONVERTER.md) | 格式转换工具文档 |
| [Agent 参考](./docs/AGENT_REFERENCE.md) | Agent 快速参考指南 |

## 添加新模块

编辑 `registry.yaml`，添加新模块配置：

```yaml
modules:
  - name: your-module-name
    repo: "https://github.com/user/repo"
    category: skills  # skills|tools|clis|frameworks|plugins
    tags: [tag1, tag2]
    description: "简短描述"
    branch: main
    sparse_checkout:  # 可选，只克隆指定路径
      - "path/to/file/"
```

详细配置说明请查看 [配置规范文档](./docs/REGISTRY_SPEC.md)。

## 许可证

- 本仓库: MIT
- 子模块遵循各自原仓库的许可证（详见 [已集成模块文档](./docs/INTEGRATED_MODULES.md#许可证汇总)）