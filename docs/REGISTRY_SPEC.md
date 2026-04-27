# Registry 配置规范

## registry.yaml 结构

```yaml
# 类别定义
categories:
  skills:
    description: "AI Agent Skills (SKILL.md 等)"
    path: "skills"
  tools:
    description: "Agent Tools & Utilities"
    path: "tools"
  # ...其他类别

# 模块注册表
modules:
  - name: module-name
    repo: "https://github.com/user/repo"
    category: skills
    tags: [tag1, tag2]
    description: "简短描述"
    branch: main
    sparse_checkout:
      - "path/to/files/"

# 标签分组
tag_groups:
  coding: [cli, generation, automation]
  platform: [claude, opencode, pi, qoder]
```

## 字段说明

### categories

定义分类体系，每个类别包含：

| 字段 | 必需 | 说明 |
|------|------|------|
| `description` | ✅ | 类别描述 |
| `path` | ✅ | 对应的目录路径 |

### modules

每个模块的完整配置：

| 字段 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `name` | ✅ | 模块唯一标识 | `anthropics-pptx-skill` |
| `repo` | ✅ | Git 仓库 URL | `https://github.com/anthropics/skills` |
| `category` | ✅ | 所属类别 | `skills` |
| `tags` | ✅ | 标签数组 | `[pptx, claude, anthropic]` |
| `description` | ✅ | 简短描述 | "Anthropic 官方 PPTX skill" |
| `branch` | ❌ | 分支名，默认 `main` | `main` |
| `sparse_checkout` | ❌ | 部分克隆路径 | `["skills/pptx/"]` |

### tag_groups

可选的标签分组，便于快速筛选：

```yaml
tag_groups:
  coding: [cli, generation, automation]
  platform: [claude, opencode, pi, qoder]
  reference: [awesome, curated]
```

## Sparse Checkout 配置

### 使用场景

当只需要仓库的特定目录时：

```yaml
# 只克隆 anthropics/skills 的 pptx 目录
- name: anthropics-pptx-skill
  repo: "https://github.com/anthropics/skills"
  sparse_checkout:
    - "skills/pptx/"
```

### 多路径配置

```yaml
# 克隆多个目录
sparse_checkout:
  - "skills/"
  - "scripts/"
  - "README.md"
```

### 不使用 Sparse Checkout

省略 `sparse_checkout` 字段，将克隆整个仓库：

```yaml
- name: nanobanana-ppt
  repo: "https://github.com/op7418/NanoBanana-PPT-Skills"
  category: skills
  tags: [pptx, video, kling]
  description: "AI驱动的PPT生成"
```

## 标签规范

### 建议标签

| 标签 | 用途 |
|------|------|
| `cli` | CLI 相关工具 |
| `pptx` | PPT/演示文稿相关 |
| `video` | 视频生成/处理 |
| `claude` | Claude Code 专用 |
| `generation` | 内容生成类 |
| `automation` | 自动化工具 |
| `kling` | 可灵 AI 相关 |

### 标签命名规则

- 使用小写字母
- 多个单词用 `-` 连接
- 保持简洁有意义

## 配置示例

### 最小配置

```yaml
- name: simple-tool
  repo: "https://github.com/user/tool"
  category: tools
  tags: [utility]
  description: "简单工具"
```

### 完整配置

```yaml
- name: complete-example
  repo: "https://github.com/org/complex-repo"
  category: skills
  tags: [ai, generation, automation, claude]
  description: "完整配置示例模块"
  branch: develop
  sparse_checkout:
    - "skills/main/"
    - "docs/"
    - "scripts/core/"
```

---

*文档版本: 2026-04-27*