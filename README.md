# Agent Wushu (武术)

Agent 工具/Skills 仓库，集成和维护可复用的 agent skills、工具、插件和本地工作流。

这个仓库既包含从开源项目同步来的模块，也包含本地增强能力，例如 OpenRouter ICU 图像生成 skill、论文深度审阅 skill、跨平台 skill 转换器，以及交互记录查看/刷新工具。

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

`registry.yaml` 当前注册 **8 Skills + 1 Tool + 1 CLI + 4 Plugins**，用于按类别、标签或模块名同步外部资源。

当前工作区还包含本地维护的增强模块：`openrouter-icu-image`、`paper-deep-review`、`ai-algorithm-survey`、`research-paper-to-ppt`、`skill_converter.py` 和 `interaction_record`。

👉 **详细说明请查看**: [已集成模块文档](./docs/INTEGRATED_MODULES.md)

| 类别 | 数量 | 链接 |
|------|------|------|
| Registry Skills | 8 | [查看详情](./docs/INTEGRATED_MODULES.md#skills) |
| Registry Tools | 1 | [查看详情](./docs/INTEGRATED_MODULES.md#tools) |
| Registry CLIs | 1 | [`registry.yaml`](./registry.yaml) |
| Registry Plugins | 4 | [查看详情](./docs/INTEGRATED_MODULES.md#plugins) |
| Local Enhancements | 6 | 见下方“本地增强能力” |

### 快速概览

**Skills:**
- [Anthropic PPTX Skill](./skills/anthropics-pptx/) - PPTX 处理
- [NanoBanana PPT Skills](./skills/nanobanana-ppt/) - AI PPT 生成
- [Guizang PPT Skill](./skills/guizang-ppt-skill/) - 杂志风/瑞士风网页 PPT 和封面生成
- [Excalidraw Diagram Skill](./skills/excalidraw-diagram/) - 论证性图表生成
- [Agent Research Skills](./skills/agent-research-skills/) - 深度研究、论文写作、实验和幻灯片生成 skill 集合
- [Research Paper to PPT](./skills/research-paper-to-ppt/) - 论文分析报告和可编辑 PPTX 生成流程
- [Paper Deep Review](./skills/paper-deep-review/) - 严格论文/技术报告深度审阅、技术点消融证据、OpenReview 评审交叉核验和可选 AI 分析示意图
- [AI Algorithm Survey](./skills/ai-algorithm-survey/) - 面向特定 AI 算法领域的论文/GitHub awesome 检索、机构归属和热度价值信号记录、逐篇深度分析、趋势/infra 综合和可选 AI 示意图
- [OpenRouter ICU Image](./skills/openrouter-icu-image/) - OpenRouter ICU 图像生成/编辑、文件输入和多候选图生成
- `cli-anything-skill` / `awesome-agent-skills` - 已在 `registry.yaml` 注册，可按需同步

**Tools:**
- [Skill Converter](./tools/skill_converter.py) - 跨平台格式转换
- [Interaction Record](./tools/interaction_record/) - 交互记录写入、Markdown spec 和 HTML 查看器

**Plugins:**
- [OpenCode Commands](./plugins/opencode-commands/) - CLI 工具集
- `claude-plugin` / `pi-extension` / `qoder-plugin` - 已在 `registry.yaml` 注册，可按需同步

## 本地增强能力

### OpenRouter ICU Image

[`skills/openrouter-icu-image`](./skills/openrouter-icu-image/) 提供一个无第三方 Python 依赖的同步 CLI，用于调用 OpenRouter ICU 的 OpenAI-compatible 图像接口。

核心能力：

- 文本生图：`/v1/images/generations`
- 本地图片编辑和多图参考：`/v1/images/edits` + multipart `image[]`
- 远程图片引用：`--image-url`
- 非图片文档输入：`responses-doc` 走 `/v1/responses` + `input_file` + `image_generation`
- 多候选图：`--n 3` 时输出自动编号
- 默认高质量输出：`quality=high`
- Streaming SSE 解析、partial/final image 解码和本地文件写入

示例：

```bash
cd skills/openrouter-icu-image

# 文本生图
python3 scripts/openrouter_icu_image.py generate \
  --prompt "A clean product photo of a white ceramic coffee mug on a wooden desk" \
  --output output/openrouter-icu/mug.png

# 本地图片编辑
python3 scripts/openrouter_icu_image.py edit \
  --image input.png \
  --prompt "Change the background while preserving the subject" \
  --output output/openrouter-icu/edited.png

# Markdown/PDF/TXT 等文档作为图像生成上下文
python3 scripts/openrouter_icu_image.py responses-doc \
  --input-file report.md \
  --prompt "Create three distinct technical infographic candidates from the uploaded document" \
  --n 3 \
  --output output/openrouter-icu/report.png
```

### Interaction Record

[`tools/interaction_record`](./tools/interaction_record/) 用于保存和查看主题相关的用户-Agent 交互历史。

包含：

- `hooks/hooks/record_interaction.py`：唯一的交互记录脚本，支持 hook stdin payload。
- `interaction-record-spec.md`：Markdown 交互记录格式。
- `interaction-viewer.html`：单文件 HTML 查看器。

`Stop` hook 可加入 `--include-process`，将公开的阶段性进度和 reasoning summary 汇总到每轮记录的 `Notes / Key process`；不会保存完整隐藏推理、加密内容或工具输出。
`SubagentStop` 会记录子代理的任务、公开完成摘要及代理标识；`PreCompact` 会记录压缩触发原因、最近公开上下文和阶段性进度。

查看器特性：

- 选择或拖入 `.md/.markdown` 文件加载。
- 支持 Mermaid、LaTeX、表格、代码块等常见 Markdown 内容。
- 自动刷新文件内容；支持 Chromium 系浏览器刷新页面后恢复上次文件句柄。
- 默认页面宽度为浏览器宽度的 80%。
- 背景主题可切换：深色技术风格 / 浅金色背景。

示例：

```bash
# 追加一轮记录
python3 hooks/hooks/record_interaction.py \
  -o interaction-history.md \
  append \
  --user "用户问题" \
  --agent "Agent 回答" \
  --turn-title "简短标题"

# 打开查看器
python3 -m http.server 8000
# 浏览器访问 http://localhost:8000/tools/interaction_record/interaction-viewer.html
```

### AI Algorithm Survey / Paper Review / Paper to PPT

本仓库维护了三个论文相关本地 skill：

- [`skills/ai-algorithm-survey`](./skills/ai-algorithm-survey/)：输入特定 AI 算法领域后，通过搜索引擎、GitHub/awesome 论文列表、arXiv 和 CVPR、ICML、ICLR、NeurIPS、AAAI、TPAMI、TIP、IROS、ICRA、RA-L 等顶会顶刊检索候选论文，记录论文归属组织/高校、代码仓库热度、引用数、候选论文间交叉引用频率等信号，识别高热度高价值论文，筛选代表性工作，并调用 `paper-deep-review` 逐篇分析后汇总技术谱系、演进趋势和软硬件 infra 需求维度，包括 data types、高效带宽利用、CPU/GPU/NPU 异构等；如果 `openrouter-icu-image` 可用，会基于最终 Markdown 生成浅金色扁平化趋势/infra 示意图并插入文档。
- [`skills/paper-deep-review`](./skills/paper-deep-review/)：面向论文、技术报告、PDF/LaTeX/source code 的严格深度审阅流程，强调公式、图表、代码和证据链；会逐项核对论文声称的技术点是否有消融实验、受控对照或机制证据支撑，并分析 data types、高效带宽利用、CPU/GPU/NPU 异构等 infra 影响；如果论文有公开 OpenReview 页面，会结合论文正文、appendix、rebuttal、实验和代码对评审意见进行交叉核验，而不是只罗列 reviewer comments；如果 `openrouter-icu-image` 可用，会基于最终 Markdown 生成浅金色扁平化算法分析示意图并插入文档。
- [`skills/research-paper-to-ppt`](./skills/research-paper-to-ppt/)：将论文分析结果组织为报告和可编辑 PPTX 的工作流。

`paper-deep-review` 包含 PDF 文本/图片提取、图表裁剪和 Markdown 模板资源，适合离线 PDF 和带代码仓库的论文复核。

### Skill Converter

[`tools/skill_converter.py`](./tools/skill_converter.py) 用于在 Claude、Codex、OpenCode、Cursor 等平台之间转换 `SKILL.md` 格式。

示例：

```bash
python tools/skill_converter.py convert path/to/SKILL.md codex -o .codex/skills/demo/SKILL.md
python tools/skill_converter.py batch skills/ claude opencode cursor -o converted/
```

## 部署到各平台

克隆 skill 后，需要部署到对应平台的正确目录才能生效。

👉 **详细部署指南**: [Skill 部署指南](./docs/SKILL_DEPLOYMENT.md)

### 快速部署

以下以 `anthropics-pptx-skill` 已克隆后的目录布局为例：

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
| [交互记录规范](./tools/interaction_record/interaction-record-spec.md) | Markdown 交互记录格式 |

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
