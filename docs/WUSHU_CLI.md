# Wushu.py 管理脚本使用指南

## 命令概览

```bash
python wushu.py <command> [options]
```

| 命令 | 说明 |
|------|------|
| `list` | 列出模块 |
| `clone` | 克隆模块 |
| `update` | 更新模块 |
| `status` | 查看状态 |

## list 命令

列出 registry.yaml 中注册的模块。

### 基本用法

```bash
# 列出所有模块
python wushu.py list

# 按类别筛选
python wushu.py list -c skills
python wushu.py list -c plugins

# 按标签筛选
python wushu.py list -t pptx
python wushu.py list -t cli,automation

# 组合筛选
python wushu.py list -c skills -t pptx
```

### 输出格式

```
Name                      Category     Tags                 Description
--------------------------------------------------------------------------------
anthropics-pptx-skill     skills       pptx, claude         Anthropic 官方 PPTX skill
nanobanana-ppt            skills       pptx, video          AI驱动的PPT生成
opencode-commands         plugins      opencode             OpenCode 命令集
```

## clone 命令

克隆指定的模块到本地。

### 基本用法

```bash
# 克隆单个模块
python wushu.py clone anthropics-pptx-skill

# 克隆整个类别
python wushu.py clone -c skills

# 按标签克隆
python wushu.py clone -t pptx
python wushu.py clone -t claude,opencode

# 克隆多个指定模块
python wushu.py clone module1 module2 module3

# 完整克隆（非浅克隆）
python wushu.py clone module-name --full
```

### 克隆行为

| 配置 | 行为 |
|------|------|
| 有 `sparse_checkout` | 只克隆指定路径 |
| 无 `sparse_checkout` | 克隆整个仓库 |
| 默认 | 浅克隆 (`--depth=1`) |
| `--full` | 完整克隆（包含历史） |

### 已存在模块

如果目标目录已存在，会跳过：

```
[SKIP] anthropics-pptx-skill already exists at skills/anthropics-pptx
```

## update 命令

更新已克隆的模块。

### 基本用法

```bash
# 更新所有已克隆模块
python wushu.py update

# 更新指定模块
python wushu.py update anthropics-pptx-skill
python wushu.py update module1 module2
```

### 更新行为

在每个模块目录执行 `git pull`。

## status 命令

查看所有模块的克隆状态。

### 基本用法

```bash
python wushu.py status
```

### 输出格式

```
Name                      Status          Path
------------------------------------------------------------
anthropics-pptx-skill     OK              skills/anthropics-pptx
nanobanana-ppt            OK              skills/nanobanana-ppt
cli-anything-skill        NOT_CLONED      skills/cli-anything-skill
opencode-commands         MODIFIED        plugins/opencode-commands
```

### 状态说明

| 状态 | 说明 |
|------|------|
| `OK` | 已克隆，无修改 |
| `NOT_CLONED` | 未克隆 |
| `MODIFIED` | 已克隆，有本地修改 |

## 工作原理

### 执行流程

```
1. 加载 registry.yaml
2. 解析命令行参数
3. 筛选目标模块
4. 执行 Git 操作：
   - clone: git init + sparse-checkout + fetch + checkout
   - update: git pull
   - status: git status --porcelain
5. 输出结果
```

### Sparse Checkout 实现

```python
# 1. 初始化空仓库
git init

# 2. 配置 sparse checkout
git sparse-checkout init --cone
git sparse-checkout set <paths>

# 3. 添加远程
git remote add origin <repo>

# 4. 拉取内容
git fetch --depth=1 origin <branch>
git checkout <branch>
```

## 与 Git Submodule 的关系

### 区别

| 方面 | wushu.py | git submodule |
|------|----------|---------------|
| 管理 | 独立克隆 | Git 统一管理 |
| 配置 | registry.yaml | .gitmodules |
| 状态 | 需手动更新 | Git 自动追踪 |
| 灵活性 | 更灵活 | 更严格 |

### 推荐

- **正式 submodule**: 使用 `git submodule add`
- **临时/测试**: 使用 `wushu.py clone`
- **混合使用**: 可以共存

---

*文档版本: 2026-04-27*