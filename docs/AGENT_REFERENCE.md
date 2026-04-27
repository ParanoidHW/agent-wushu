# Agent 快速参考指南

本指南专为 AI Agent 设计，帮助快速理解仓库结构并执行操作。

## 仓库定位

Agent Wushu 是一个 **聚合型仓库**，用于集中管理 AI Agent 相关的工具、Skills、CLI 和插件。

## 快速理解

### 目录结构（一句话）

```
skills/ → AI Skills (SKILL.md)
tools/  → 工具和实用程序
clis/   → CLI 命令行工具
frameworks/ → 框架和库
plugins/ → 平台插件
```

### 关键文件

| 文件 | 一句话描述 |
|------|-----------|
| `registry.yaml` | 所有模块的元数据注册表 |
| `wushu.py` | 管理脚本（list/clone/update/status） |
| `.gitmodules` | Git submodule 配置 |
| `docs/` | 架构文档 |

### 当前已集成模块

```
skills/anthropics-pptx/    → Anthropic 官方 PPTX skill
skills/nanobanana-ppt/     → AI PPT 图片/视频生成
plugins/opencode-commands/ → OpenCode 命令集
```

## 常见任务

### 添加新模块

1. **读取 registry.yaml** 了解现有配置格式
2. **编辑 registry.yaml** 添加新模块元数据：
   ```yaml
   - name: new-module-name
     repo: "https://github.com/user/repo"
     category: skills
     tags: [tag1, tag2]
     description: "简短描述"
     sparse_checkout:  # 可选
       - "path/to/files/"
   ```
3. **克隆模块**：`python wushu.py clone new-module-name`
4. **更新 README.md** 添加模块说明
5. **提交更改**：`git add . && git commit && git push`

### 更新现有模块

```bash
python wushu.py update <module-name>
```

或直接：
```bash
cd skills/<module> && git pull origin main
```

### 查看模块状态

```bash
python wushu.py status
```

### 查找特定类型模块

```bash
# 查找 PPTX 相关
python wushu.py list -t pptx

# 查找 skills 类别
python wushu.py list -c skills
```

## Skills 使用

### anthropics-pptx

**路径**: `skills/anthropics-pptx/skills/pptx/`

**用途**: 创建/编辑/解析 PPTX 文件

**快速命令**:
```bash
# 读取 PPTX
python -m markitdown presentation.pptx

# 生成缩略图
python scripts/thumbnail.py presentation.pptx
```

### nanobanana-ppt

**路径**: `skills/nanobanana-ppt/`

**用途**: AI 生成 PPT 图片和视频

**依赖**: `GEMINI_API_KEY`（必需）、`KLING_ACCESS_KEY`（可选）

**快速命令**:
```bash
python generate_ppt.py --plan slides_plan.json --style styles/gradient-glass.md
```

## Git Submodule 操作

### 添加 submodule

```bash
git submodule add --depth 1 https://github.com/user/repo.git skills/module-name
```

### 配置 sparse checkout

```bash
git config -f .gitmodules submodule.skills/module-name.sparse-checkout-dir path/to/dir
```

### 更新 submodule

```bash
git submodule update --remote skills/module-name
```

### 移除 submodule

```bash
git submodule deinit -f skills/module-name
git rm -f skills/module-name
rm -rf .git/modules/skills/module-name
```

## 配置规范速查

### registry.yaml 必需字段

- `name` - 模块标识
- `repo` - Git URL
- `category` - 类别（skills/tools/clis/frameworks/plugins）
- `tags` - 标签数组
- `description` - 描述

### 可选字段

- `branch` - 分支（默认 main）
- `sparse_checkout` - 部分克隆路径

## 文档索引

| 文档 | 内容 |
|------|------|
| `docs/ARCHITECTURE.md` | 架构设计详解 |
| `docs/REGISTRY_SPEC.md` | registry.yaml 配置规范 |
| `docs/WUSHU_CLI.md` | wushu.py 使用指南 |
| `README.md` | 用户文档 |

## 错误处理

### 模块已存在

```
[SKIP] module-name already exists at skills/module-name
```
→ 跳过，无需处理

### 克隆失败

检查：
1. URL 是否正确
2. 分支是否存在
3. sparse_checkout 路径是否存在

### Git 冲突

```bash
cd skills/module-name
git stash  # 暂存本地修改
git pull   # 拉取远程
git stash pop  # 恢复修改
```

---

*文档版本: 2026-04-27*