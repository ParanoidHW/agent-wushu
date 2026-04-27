# Agent Wushu 架构设计

## 概述

Agent Wushu 是一个聚合型仓库，用于集中管理和集成 GitHub 上开源的 AI Agent 工具、Skills、CLI、框架和插件。采用 **Git Submodule + Registry 配置** 的混合架构，兼顾灵活性和可维护性。

## 核心设计原则

### 1. 模块化分类

所有集成的内容按功能分类存放：

| 类别 | 目录 | 说明 |
|------|------|------|
| `skills` | `skills/` | AI Agent Skills（含 SKILL.md） |
| `tools` | `tools/` | Agent 工具和实用程序 |
| `clis` | `clis/` | CLI 命令行工具 |
| `frameworks` | `frameworks/` | Agent 框架和库 |
| `plugins` | `plugins/` | 平台插件（Claude、OpenCode 等） |

### 2. 双层管理机制

```
┌─────────────────────────────────────────────────────┐
│                  Agent Wushu Repository              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ registry.yaml│  │  wushu.py   │  │ .gitmodules │  │
│  │  (元数据配置) │  │ (管理脚本)  │  │ (submodule) │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
├─────────────────────────────────────────────────────┤
│                    Submodules                        │
│  ┌───────────────────────────────────────────────┐  │
│  │  skills/                                      │  │
│  │    ├── anthropics-pptx/  → anthropics/skills  │  │
│  │    └── nanobanana-ppt/   → NanoBanana-PPT     │  │
│  └───────────────────────────────────────────────┐  │
│  │  plugins/                                     │  │
│  │    └── opencode-commands/ → CLI-Anything      │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

- **registry.yaml**: 存储所有模块的元数据（名称、仓库、标签、描述）
- **.gitmodules**: Git 官方 submodule 注册表
- **wushu.py**: 统一管理脚本，提供 list/clone/update/status 命令

### 3. Sparse Checkout 支持

对于大型仓库，支持只克隆特定目录，减少存储空间：

```yaml
# 示例：只克隆 anthropics/skills 仓库的 pptx 目录
sparse_checkout:
  - "skills/pptx/"
```

## 文件职责

| 文件 | 作用 | 维护方式 |
|------|------|----------|
| `registry.yaml` | 模块元数据注册表 | 手动编辑添加新模块 |
| `wushu.py` | 管理脚本 | 核心工具，谨慎修改 |
| `.gitmodules` | Submodule 配置 | Git 自动管理 |
| `README.md` | 用户文档 | 随模块更新 |
| `docs/` | 架构文档 | Agent 参考用 |

## 数据流

```
用户操作
    │
    ▼
wushu.py parse args
    │
    ▼
load registry.yaml
    │
    ▼
filter modules (by category/tags/names)
    │
    ▼
execute git commands
    │
    ├── git submodule add (新模块)
    ├── git sparse-checkout (部分克隆)
    ├── git pull (更新)
    └── git status (状态检查)
    │
    ▼
output results
```

## 扩展策略

### 添加新模块

1. 编辑 `registry.yaml`，添加模块元数据
2. 运行 `python wushu.py clone <module-name>`
3. Git 自动更新 `.gitmodules`
4. 更新 `README.md` 添加说明

### 更新模块

```bash
# 更新单个模块
python wushu.py update <module-name>

# 或直接使用 git
cd skills/<module>
git pull origin main
```

### 移除模块

```bash
# 从 registry.yaml 删除配置
# 从 .gitmodules 和 git 移除
git submodule deinit -f skills/<module>
git rm -f skills/<module>
rm -rf .git/modules/skills/<module>
```

## 与 Agent 的交互

本仓库设计为 Agent 可直接参考和操作：

1. **读取 registry.yaml** - 了解所有可用模块
2. **调用 wushu.py** - 执行克隆/更新操作
3. **查阅 docs/** - 理解架构和规范
4. **使用 skills/** - 直接应用集成的 skill

---

*文档版本: 2026-04-27*