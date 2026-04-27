# 已集成模块

本页详细介绍 Agent Wushu 仓库中已集成的 Skills、Tools、Plugins 等模块。

---

## Skills

### 1. Anthropic PPTX Skill

**路径**: [`skills/anthropics-pptx/skills/pptx/`](../skills/anthropics-pptx/skills/pptx/)

**源仓库**: [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/pptx)

**标签**: `pptx`, `presentation`, `claude`, `anthropic`

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

**许可证**: Proprietary (参见 LICENSE.txt)

---

### 2. NanoBanana PPT Skills

**路径**: [`skills/nanobanana-ppt/`](../skills/nanobanana-ppt/)

**源仓库**: [op7418/NanoBanana-PPT-Skills](https://github.com/op7418/NanoBanana-PPT-Skills)

**标签**: `pptx`, `presentation`, `video`, `generation`, `kling`

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

**许可证**: MIT

---

### 3. Excalidraw Diagram Skill

**路径**: [`skills/excalidraw-diagram/`](../skills/excalidraw-diagram/)

**源仓库**: [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill)

**标签**: `diagram`, `excalidraw`, `visualization`, `architecture`

**功能描述**:
生成"论证性图表"的 Agent skill，让图表的视觉结构反映概念含义，而非仅仅是信息的展示。

| 功能 | 说明 |
|------|------|
| 论证性图表设计 | 形状反映概念（扇形=一对多，时间线=序列） |
| Evidence Artifacts | 代码片段、JSON 示例、真实数据展示 |
| 视觉验证 | Playwright 渲染 PNG，验证布局正确性 |
| 多缩放架构 | 概览流 + 区域边界 + 详情内容 |
| 可定制配色 | 单文件配置品牌颜色 (`color-palette.md`) |

**核心理念**:
- **同构测试**: 移除所有文字，结构本身能否传达概念？
- **教育测试**: 图表能教会具体内容，而非仅标记方框？

**视觉模式库**:

| 概念 | 视觉模式 |
|------|----------|
| 一对多输出 | Fan-out（放射状箭头） |
| 多对一聚合 | Convergence（漏斗） |
| 层级嵌套 | Tree（线+自由文本） |
| 步骤序列 | Timeline（线+点+标签） |
| 循环迭代 | Spiral/Cycle |
| 抽象状态 | Cloud（重叠椭圆） |
| 输入→输出转换 | Assembly Line |

**依赖设置**:
```bash
cd skills/excalidraw-diagram/references
uv sync
uv run playwright install chromium
```

**使用示例**:
```bash
# 生成后渲染验证（必需步骤）
cd skills/excalidraw-diagram/references
uv run python render_excalidraw.py diagram.excalidraw

# 查看渲染结果
# 使用 Read 工具查看生成的 PNG
```

**文件结构**:
| 文件 | 功能 |
|------|------|
| `SKILL.md` | 设计方法论 + 工作流程 |
| `references/color-palette.md` | 品牌配色（可编辑） |
| `references/element-templates.md` | JSON 元素模板 |
| `references/json-schema.md` | Excalidraw 格式参考 |
| `references/render_excalidraw.py` | 渲染脚本 |

**许可证**: MIT

---

## Tools

### Skill Converter

**路径**: [`tools/skill_converter.py`](../tools/skill_converter.py)

**标签**: `converter`, `skill`, `cross-platform`, `claude`, `codex`, `opencode`, `cursor`

**功能描述**:
跨平台 Skill 格式转换工具，支持将不同 Agent 平台的 skill 目录和格式进行互相转换。

| 支持平台 | 标识符 | 说明 |
|----------|--------|------|
| Claude Code | `claude` | Anthropic 官方 Claude Code |
| Codex | `codex` | OpenAI Codex |
| OpenCode | `opencode` | OpenCode |
| OpenClaw | `openclaw` | OpenClaw |
| Cursor | `cursor` | Cursor IDE |

**使用示例**:
```bash
# 列出支持的平台
python tools/skill_converter.py list-platforms

# 转换单个 skill 文件
python tools/skill_converter.py convert skills/pptx/SKILL.md codex

# 转换整个目录
python tools/skill_converter.py convert skills/ opencode -o output/

# 批量转换到多个平台
python tools/skill_converter.py batch skills/ claude codex opencode

# 强制转换（源格式=目标格式时）
python tools/skill_converter.py convert skills/pptx/SKILL.md claude --force
```

**详细文档**: [docs/SKILL_CONVERTER.md](../docs/SKILL_CONVERTER.md)

---

## Plugins

### OpenCode Commands

**路径**: [`plugins/opencode-commands/`](../plugins/opencode-commands/)

**源仓库**: [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything)

**标签**: `opencode`, `commands`

**功能描述**:
CLI-Anything 项目为 OpenCode 提供的命令集，包含大量 CLI 工具的 Agent harness，扩展 Agent 的 CLI 交互能力。

**包含的 CLI 工具** (部分列表):
- Blender - 3D 场景编辑
- GIMP - 图像处理
- Inkscape - 矢量图形
- LibreOffice - 文档处理
- OBS Studio - 视频录制
- FFmpeg - 视频处理
- Mermaid - 图表生成
- Ollama - 本地 LLM 运行
- N8N - 工作流自动化
- ChromaDB - 向量数据库
- 更多...

---

## 模块总览

| 名称 | 类别 | 标签 | 源仓库 |
|------|------|------|--------|
| anthropics-pptx-skill | skills | pptx, claude | [anthropics/skills](https://github.com/anthropics/skills) |
| nanobanana-ppt-skill | skills | pptx, video, kling | [op7418/NanoBanana-PPT-Skills](https://github.com/op7418/NanoBanana-PPT-Skills) |
| excalidraw-diagram-skill | skills | diagram, visualization | [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) |
| skill-converter | tools | converter, cross-platform | 本地开发 |
| opencode-commands | plugins | opencode | [HKUDS/CLI-Anything](https://github.com/HKUDS/CLI-Anything) |

---

## 许可证汇总

| 模块 | 许可证 |
|------|--------|
| 本仓库 | MIT |
| anthropics-pptx | Proprietary (参见 LICENSE.txt) |
| nanobanana-ppt | MIT |
| excalidraw-diagram | MIT |
| opencode-commands | MIT (CLI-Anything) |