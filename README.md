# Agent Wushu (武术)

Agent 工具/Skills 仓库，集成 GitHub 上开源的 agent 工具、skill、CLI 等。

## 目录结构

```
agent-wushu/
├── skills/          # AI Agent Skills (SKILL.md 等)
│   ├── anthropics-pptx/   # Anthropic 官方 PPTX skill
│   └── nanobanana-ppt/    # NanoBanana PPT 图片/视频生成
├── tools/           # Agent Tools & Utilities
├── clis/            # CLI Tools for Agent Interaction
├── frameworks/      # Agent Frameworks & Libraries
├── plugins/         # Agent Platform Plugins
│   └── opencode-commands/  # OpenCode 命令集
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

## 已集成 Skills

### PPTX 相关 Skills

#### 1. Anthropic PPTX Skill

**路径**: [`skills/anthropics-pptx/skills/pptx/`](./skills/anthropics-pptx/skills/pptx/)

**源仓库**: [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pptx)

**功能描述**:
Anthropic 官方发布的 PPTX 处理 skill，提供完整的演示文稿读取、编辑和创建能力。

| 功能 | 说明 |
|------|------|
| 读取/解析 | 使用 `markitdown` 提取 PPTX 文本内容 |
| 缩略图生成 | `thumbnail.py` 生成可视化概览 |
| XML 解析 | `unpack.py` 解包原始 XML 结构 |
| 模板编辑 | 基于 template 的修改流程 |
| 从零创建 | 使用 `pptxgenjs` 创建全新演示文稿 |

**设计指导**:
- 10+ 专业配色方案（Midnight Executive、Forest & Moss、Coral Energy 等）
- 字体配对建议（Georgia + Calibri、Arial Black + Arial 等）
- 布局模式（双栏、图标+文本、网格、半出血图片）
- QA 流程（内容检查 + 视觉检查）

**依赖**:
```bash
pip install "markitdown[pptx]" Pillow
npm install -g pptxgenjs
# LibreOffice (soffice) + Poppler (pdftoppm) 用于 PDF 转换
```

**使用示例**:
```bash
# 读取 PPTX 内容
python -m markitdown presentation.pptx

# 生成缩略图
python scripts/thumbnail.py presentation.pptx

# 解包查看 XML
python scripts/office/unpack.py presentation.pptx unpacked/
```

---

#### 2. NanoBanana PPT Skills

**路径**: [`skills/nanobanana-ppt/`](./skills/nanobanana-ppt/)

**源仓库**: [op7418/NanoBanana-PPT-Skills](https://github.com/op7418/NanoBanana-PPT-Skills)

**功能描述**:
AI 驱动的 PPT 图片和视频生成工具，支持智能转场和交互式播放。

| 功能 | 说明 |
|------|------|
| 智能文档分析 | 自动提取核心要点，规划 PPT 结构 |
| 多风格支持 | 渐变毛玻璃、矢量插画两种专业风格 |
| 高质量图片 | Gemini API 生成 16:9 高清 PPT (2K/4K) |
| AI 转场视频 | 可灵 AI 生成页面过渡动画 |
| 交互式播放器 | HTML5 视频+图片混合播放器 |
| 完整视频导出 | FFmpeg 合成带转场的完整视频 |

**核心脚本**:
| 文件 | 功能 |
|------|------|
| `generate_ppt.py` | PPT 图片生成主脚本 |
| `generate_ppt_video.py` | 视频生成主脚本 |
| `kling_api.py` | 可灵 AI API 封装 |
| `video_composer.py` | FFmpeg 视频合成 |

**环境变量**:
```bash
# 必需
GEMINI_API_KEY=your_gemini_api_key

# 可选（视频功能）
KLING_ACCESS_KEY=your_kling_access_key
KLING_SECRET_KEY=your_kling_secret_key
```

**依赖**:
```bash
pip install google-genai pillow python-dotenv
# FFmpeg 用于视频合成
```

**使用示例**:
```bash
# 生成 PPT 图片
python generate_ppt.py \
  --plan slides_plan.json \
  --style styles/gradient-glass.md \
  --resolution 2K

# 生成转场视频
python generate_ppt_video.py \
  --slides-dir outputs/images \
  --prompts-file outputs/transition_prompts.json
```

**内置风格**:

| 风格 | 文件 | 适用场景 |
|------|------|----------|
| 渐变毛玻璃卡片 | `styles/gradient-glass.md` | 科技产品、商务演示、数据报告 |
| 矢量插画 | `styles/vector-illustration.md` | 教育培训、创意提案、温暖品牌故事 |

---

## 已集成 Plugins

### OpenCode Commands

**路径**: [`plugins/opencode-commands/`](./plugins/opencode-commands/)

**源仓库**: [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)

**功能描述**:
CLI-Anything 项目为 OpenCode 提供的命令集，扩展 Agent 的 CLI 交互能力。

---

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
# 示例：只克隆 anthropics/skills 仓库的 pptx 目录
sparse_checkout:
  - "skills/pptx/"
```

## 许可证

- 本仓库: MIT
- 子模块遵循各自原仓库的许可证
  - anthropics-pptx: Proprietary (参见 LICENSE.txt)
  - nanobanana-ppt: MIT