# OpenCode Interaction Recorder

将每个 OpenCode 会话自动写为一个 Markdown 文件。每个回合按“用户问题、Agent 可见思考/进度、Agent 最终输出”组织；流式 `reasoning` 和 `text` 片段更新时会刷新文件，会话进入空闲状态后再完成一次同步。

默认记录路径为当前项目根目录的 `session_log/`。记录文件名为 `<session-id>_<ISO-8601-timestamp>.md`，例如 `ses_abc_2026-07-17T08-30-11-123Z.md`。同一会话的流式刷新会持续覆盖该会话首次生成的文件；新会话会创建新文件。记录包含用户问题、OpenCode 公开提供的 reasoning 片段和 Agent 输出；不保存系统提示词、隐藏推理或工具输入/输出。

## 安装

### 当前仓库

当前仓库已在 `.opencode/plugins/interaction-recorder.ts` 放置自动加载入口，无需复制到系统目录。重启并在本仓库根目录启动 OpenCode：

```bash
opencode
```

首次完成一次 Agent 回复后，记录会出现在：

```text
session_log/<session-id>_<timestamp>.md
```

### 其他项目

将插件实现文件放到目标项目根目录的 `.opencode/plugins/`。OpenCode 会在启动时自动加载该目录中的 `.ts` 或 `.js` 文件：

```bash
mkdir -p .opencode/plugins
cp plugins/opencode-interaction-recorder/.opencode/plugins/interaction-recorder.ts \
  .opencode/plugins/interaction-recorder.ts
```

然后在目标项目根目录重启 OpenCode。不要放到 `~/.config/opencode/plugins/`，除非需要为所有项目启用。

## 配置

通过环境变量配置：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `OPENCODE_INTERACTION_RECORD_DIR` | `session_log` | 记录目录。相对路径基于项目根目录，绝对路径可用于集中存储。 |
| `OPENCODE_INTERACTION_RECORD_INCLUDE_TOOLS` | 未设置 | 设为 `1` 时，在每条消息下写入工具调用标题；仍不保存工具输入或输出。 |

示例：

```bash
OPENCODE_INTERACTION_RECORD_DIR=session_log \
OPENCODE_INTERACTION_RECORD_INCLUDE_TOOLS=1 \
opencode
```

## 查看记录

查看器是单文件 HTML，位于 `plugins/opencode-interaction-recorder/viewer/interaction-log-viewer.html`。直接在浏览器中打开该文件，点击“导入记录”，选择 `session_log/` 下的 `.md` 文件。

查看器提供：

- 目录（TOC）跳转到每个回合。
- 每轮 QA 独立折叠，默认展开最新回合。
- 用户问题、Agent 进度、最终输出和可选工具标题的分区显示。
- 使用支持 File System Access API 的浏览器点击“导入记录”后，可开启每秒自动刷新，观察仍在写入的会话；若浏览器仅提供普通文件选择，则可使用“刷新”重新读取文件。

## 行为

- `message.part.updated`：可见 reasoning 和结果文本流式更新时，以 250ms 去抖刷新记录。
- `session.idle`：每次助手完成回答后同步记录。
- `session.compacted`：上下文压缩完成后同步记录。
- 同一会话的并发事件会串行处理，避免交叉写入。

本实现不依赖第三方包，使用 OpenCode 内置的 Bun 运行时与 SDK 客户端。
