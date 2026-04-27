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
python wushu.py list -t claude

# 克隆单个模块
python wushu.py clone cli-anything-skill

# 克隆某个类别的所有模块
python wushu.py clone -c skills
python wushu.py clone -c plugins

# 按标签克隆
python wushu.py clone -t claude,opencode

# 完整克隆（非浅克隆）
python wushu.py clone cli-anything-skill --full

# 更新已克隆的模块
python wushu.py update

# 查看状态
python wushu.py status
```

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
      - "another/path/"
```

## 部分克隆功能

使用 `sparse_checkout` 字段指定要克隆的路径，避免克隆整个仓库：

```yaml
# 示例：只克隆 CLI-Anything 的 skills 目录
sparse_checkout:
  - "skills/"
  - "openclaw-skill/"
```

## 已集成模块

| 名称 | 类别 | 标签 | 来源 |
|------|------|------|------|
| cli-anything-skill | skills | cli, generation | HKUDS/CLI-Anything |
| cli-hub | clis | cli, hub | HKUDS/CLI-Anything |
| claude-plugin | plugins | claude | HKUDS/CLI-Anything |
| opencode-commands | plugins | opencode | HKUDS/CLI-Anything |
| pi-extension | plugins | pi | HKUDS/CLI-Anything |
| qoder-plugin | plugins | qoder | HKUDS/CLI-Anything |

## 许可证

MIT