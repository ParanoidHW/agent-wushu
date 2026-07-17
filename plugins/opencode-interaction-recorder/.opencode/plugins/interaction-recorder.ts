import type { Message, Part, Plugin } from "@opencode-ai/plugin"

const RECORD_DIRECTORY_ENV = "OPENCODE_INTERACTION_RECORD_DIR"
const INCLUDE_TOOLS_ENV = "OPENCODE_INTERACTION_RECORD_INCLUDE_TOOLS"

type SessionMessage = {
  info: Message
  parts: Part[]
}

export const InteractionRecorder: Plugin = async ({ client, directory, $ }) => {
  const recordDirectory = resolveRecordDirectory(directory)
  const includeTools = process.env[INCLUDE_TOOLS_ENV] === "1"
  const pending = new Map<string, Promise<void>>()
  const scheduled = new Map<string, ReturnType<typeof setTimeout>>()
  const recordFiles = new Map<string, string>()

  const persist = async (sessionID: string) => {
    const current = pending.get(sessionID) ?? Promise.resolve()
    const next = current
      .catch(() => undefined)
      .then(async () => {
        const response = await client.session.messages({ path: { id: sessionID } })
        if (response.error) {
          throw new Error(`Unable to read session ${sessionID}: ${JSON.stringify(response.error)}`)
        }

        const messages = response.data ?? []
        const content = renderRecord(sessionID, messages, includeTools)
        const output = joinPath(recordDirectory, recordFileName(sessionID, recordFiles))

        await $`mkdir -p ${recordDirectory}`
        await Bun.write(output, content)
      })
      .catch(async (error) => {
        await client.app.log({
          body: {
            service: "opencode-interaction-recorder",
            level: "error",
            message: "Failed to persist interaction record",
            extra: { sessionID, error: String(error) },
          },
        })
      })
      .finally(() => {
        if (pending.get(sessionID) === next) pending.delete(sessionID)
      })

    pending.set(sessionID, next)
    await next
  }

  const schedulePersist = (sessionID: string) => {
    const existing = scheduled.get(sessionID)
    if (existing) clearTimeout(existing)

    scheduled.set(sessionID, setTimeout(() => {
      scheduled.delete(sessionID)
      void persist(sessionID)
    }, 250))
  }

  const flushPersist = async (sessionID: string) => {
    const scheduledPersist = scheduled.get(sessionID)
    if (scheduledPersist) {
      clearTimeout(scheduledPersist)
      scheduled.delete(sessionID)
    }
    await persist(sessionID)
  }

  return {
    event: async ({ event }) => {
      if (
        event.type === "message.part.updated" &&
        (event.properties.part.type === "reasoning" || event.properties.part.type === "text")
      ) {
        schedulePersist(event.properties.part.sessionID)
      }

      if (
        event.type === "session.idle" ||
        event.type === "session.compacted"
      ) {
        await flushPersist(event.properties.sessionID)
      }
    },
  }
}

function resolveRecordDirectory(projectDirectory: string): string {
  const configured = process.env[RECORD_DIRECTORY_ENV]?.trim()
  if (!configured) return joinPath(projectDirectory, "session_log")
  if (configured.startsWith("/")) return configured
  return joinPath(projectDirectory, configured)
}

function renderRecord(sessionID: string, messages: SessionMessage[], includeTools: boolean): string {
  const lines = [
    "---",
    "spec: opencode-interaction-record",
    "version: 1.0",
    `session_id: ${sessionID}`,
    `updated_at: ${new Date().toISOString()}`,
    "---",
    "",
    "# OpenCode Interaction Record",
    "",
  ]

  const turns = groupTurns(messages, includeTools)
  for (const [index, turn] of turns.entries()) {
    lines.push(`## Turn ${index + 1}`, "")
    if (turn.user) lines.push("### User", "", turn.user, "")
    if (turn.reasoning) lines.push("### Agent Progress", "", turn.reasoning, "")
    if (turn.result) lines.push("### Agent Result", "", turn.result, "")
    if (turn.tools.length > 0) {
      lines.push("### Tool Calls", "")
      for (const tool of turn.tools) lines.push(`- ${tool}`)
      lines.push("")
    }
  }

  if (turns.length === 0) lines.push("No user or assistant content has been recorded yet.", "")
  return `${lines.join("\n").trimEnd()}\n`
}

type RecordTurn = {
  user: string
  reasoning: string
  result: string
  tools: string[]
}

function groupTurns(messages: SessionMessage[], includeTools: boolean): RecordTurn[] {
  const turns: RecordTurn[] = []
  let current: RecordTurn | undefined

  for (const message of messages) {
    if (message.info.role === "user") {
      const user = textFromParts(message.parts)
      if (!user) continue
      current = { user, reasoning: "", result: "", tools: [] }
      turns.push(current)
      continue
    }

    const reasoning = reasoningFromParts(message.parts)
    const result = textFromParts(message.parts)
    const tools = includeTools ? toolSummaryFromParts(message.parts) : []
    if (!reasoning && !result && tools.length === 0) continue
    if (!current) {
      current = { user: "", reasoning: "", result: "", tools: [] }
      turns.push(current)
    }
    current.reasoning = appendSection(current.reasoning, reasoning)
    current.result = appendSection(current.result, result)
    current.tools.push(...tools)
  }

  return turns.map((turn) => ({
    ...turn,
    tools: turn.tools.filter((tool, index) => turn.tools.indexOf(tool) === index),
  }))
}

function appendSection(current: string, next: string): string {
  if (!next) return current
  return current ? `${current}\n\n${next}` : next
}

function textFromParts(parts: Part[]): string {
  return parts
    .filter((part): part is Extract<Part, { type: "text" }> => part.type === "text")
    .map((part) => part.text.trim())
    .filter(Boolean)
    .join("\n\n")
}

function reasoningFromParts(parts: Part[]): string {
  return parts
    .filter((part): part is Extract<Part, { type: "reasoning" }> => part.type === "reasoning")
    .map((part) => part.text.trim())
    .filter(Boolean)
    .join("\n\n")
}

function toolSummaryFromParts(parts: Part[]): string[] {
  return parts
    .filter((part) => part.type === "tool")
    .map((part) => {
      const state = part.state
      const title = typeof state === "object" && state && "title" in state ? state.title : undefined
      return title ? `\`${String(title)}\`` : "`tool call`"
    })
}

function joinPath(...segments: string[]): string {
  return segments.map((segment, index) => {
    if (index === 0) return segment.replace(/\/+$/, "")
    return segment.replace(/^\/+|\/+$/g, "")
  }).join("/")
}

function safeFileName(value: string): string {
  return value.replace(/[^A-Za-z0-9._-]/g, "_")
}

function recordFileName(sessionID: string, files: Map<string, string>): string {
  const existing = files.get(sessionID)
  if (existing) return existing

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-")
  const name = `${safeFileName(sessionID)}_${timestamp}.md`
  files.set(sessionID, name)
  return name
}
