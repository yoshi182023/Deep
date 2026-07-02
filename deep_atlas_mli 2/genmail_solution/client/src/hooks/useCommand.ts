import { useState } from "react"
import { API_BASE } from "../constants"

interface Tool {
  name: string
  input: Record<string, any>
}

interface ToolResult {
  tool: string
  output: {
    success: boolean
    data?: any
    error?: string
  }
}

export function useCommand() {
  const [input, setInput] = useState("")
  const [previewTools, setPreviewTools] = useState<Tool[] | null>(null)
  const [results, setResults] = useState<ToolResult[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const previewCommand = async (command: string) => {
    if (!command.trim()) {
      setPreviewTools(null)
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE}/command`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: command })
      })

      if (!response.ok) {
        throw new Error(`Failed to preview command: ${response.statusText}`)
      }

      const data = await response.json()
      setPreviewTools(data.tools)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to preview command")
      setPreviewTools(null)
    } finally {
      setLoading(false)
    }
  }

  const executeCommand = async (tools: Tool[]) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch(`${API_BASE}/command/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tools })
      })

      if (!response.ok) {
        throw new Error(`Failed to execute command: ${response.statusText}`)
      }

      const data = await response.json()
      setResults(data.results)
      setPreviewTools(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to execute command")
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setInput("")
    setPreviewTools(null)
    setResults(null)
    setError(null)
  }

  return {
    input,
    setInput,
    previewTools,
    results,
    loading,
    error,
    previewCommand,
    executeCommand,
    reset
  }
}
