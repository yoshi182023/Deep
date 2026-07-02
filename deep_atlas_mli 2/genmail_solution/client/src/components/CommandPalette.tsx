import { useEffect } from "react"
import { useCommand } from "../hooks/useCommand"
import type { Email } from "../types"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "./ui/command"
import { Button } from "./ui/button"

interface CommandPaletteProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onEmailSelect?: (email: Email) => void
  onRefresh?: () => void
}

export function CommandPalette({ open, onOpenChange, onEmailSelect, onRefresh }: CommandPaletteProps) {
  const {
    input,
    setInput,
    previewTools,
    results,
    loading,
    error,
    previewCommand,
    executeCommand,
    reset
  } = useCommand()

  useEffect(() => {
    if (!open) {
      reset()
    }
  }, [open])

  const handlePreview = async () => {
    if (!input.trim()) return
    await previewCommand(input)
  }

  const handleExecute = async () => {
    if (!previewTools) return
    await executeCommand(previewTools)
    if (onRefresh) {
      onRefresh()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !previewTools && !results && input.trim()) {
      e.preventDefault()
      handlePreview()
    }
  }

  const handleEmailClick = (email: Email) => {
    if (onEmailSelect) {
      onEmailSelect(email)
    }
    onOpenChange(false)
  }

  const handleSuggestionClick = (suggestion: string) => {
    setInput(suggestion)
  }

  const isEmail = (item: any): item is Email =>
    typeof item?.id === "number" && typeof item?.sender === "string" && typeof item?.subject === "string"

  const extractEmailsFromResults = (): Email[] => {
    if (!results) return []

    const emails: Email[] = []
    for (const result of results) {
      if (result.output.success && result.output.data) {
        if (Array.isArray(result.output.data)) {
          emails.push(...result.output.data.filter(isEmail))
        } else if (isEmail(result.output.data)) {
          emails.push(result.output.data)
        }
      }
    }
    return emails
  }

  const resultEmails = extractEmailsFromResults()

  const formatResultData = (tool: string, data: any) => {
    if (tool === "get_stats" && data) {
      return (
        <div className="space-y-1">
          <div>Total emails: <span className="font-medium">{data.total_emails}</span></div>
          <div>Unread: <span className="font-medium">{data.unread_count}</span></div>
          <div>Read: <span className="font-medium">{data.read_count}</span></div>
          <div>Threads: <span className="font-medium">{data.thread_count}</span></div>
        </div>
      )
    }

    if (tool === "mark_email_read" || tool === "mark_email_unread" || tool === "delete_email") {
      return <div>✓ Success</div>
    }

    if (data && typeof data === "object" && !Array.isArray(data)) {
      return (
        <pre className="text-xs whitespace-pre-wrap">
          {JSON.stringify(data, null, 2)}
        </pre>
      )
    }

    return <div>✓ Success</div>
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Type a command and press Enter..."
        value={input}
        onValueChange={setInput}
        onKeyDown={handleKeyDown}
      />
      <CommandList shouldFilter={false}>
        {!previewTools && !results && (
          <CommandEmpty>
            {loading ? "Loading..." : error ? `Error: ${error}` : "Type a command and press Enter"}
          </CommandEmpty>
        )}

        {!input && !previewTools && !results && !loading && (
          <CommandGroup heading="Suggestions">
            <CommandItem onSelect={() => handleSuggestionClick("show unread emails")}>
              Show unread emails
            </CommandItem>
            <CommandItem onSelect={() => handleSuggestionClick("search Phoenix")}>
              Search emails about Phoenix
            </CommandItem>
            <CommandItem onSelect={() => handleSuggestionClick("get inbox stats")}>
              Get inbox statistics
            </CommandItem>
            <CommandItem onSelect={() => handleSuggestionClick("show all threads")}>
              Show all conversations
            </CommandItem>
          </CommandGroup>
        )}

        {input && !previewTools && !results && !loading && (
          <div className="p-2">
            <Button onClick={handlePreview} className="w-full">
              Preview Command
            </Button>
          </div>
        )}

        {previewTools && previewTools.length > 0 && !results && (
          <div className="p-2">
            <div className="text-sm font-medium mb-2 px-2 text-muted-foreground">Preview - Will execute:</div>
            {previewTools.map((tool, idx) => (
              <div key={idx} className="px-2 py-2 mb-2 rounded-md bg-muted">
                <div className="font-medium">{tool.name}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {JSON.stringify(tool.input)}
                </div>
              </div>
            ))}
            <div className="space-y-2 mt-2">
              <Button
                onClick={handleExecute}
                disabled={loading}
                className="w-full"
              >
                {loading ? "Executing..." : "Execute"}
              </Button>
              <Button
                onClick={reset}
                variant="outline"
                className="w-full"
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {results && (
          <div className="p-2">
            {resultEmails.length > 0 ? (
              <>
                <div className="text-sm font-medium mb-2 px-2 text-muted-foreground">
                  {resultEmails.length} emails found
                </div>
                {resultEmails.map((email) => (
                  <div
                    key={email.id}
                    onClick={() => handleEmailClick(email)}
                    className="flex flex-col items-start gap-1 cursor-pointer px-2 py-2 mb-2 rounded-md hover:bg-muted"
                  >
                    <div className="flex items-center gap-2 w-full">
                      <div className="font-medium truncate flex-1">{email.subject}</div>
                      {!email.is_read && (
                        <div className="h-2 w-2 rounded-full bg-blue-500" />
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground truncate w-full">
                      {email.sender}
                    </div>
                    <div className="text-xs text-muted-foreground truncate w-full">
                      {email.body.slice(0, 100)}...
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <>
                <div className="text-sm font-medium mb-2 px-2 text-muted-foreground">Results</div>
                {results.map((result, idx) => (
                  <div key={idx} className="px-2 py-2 mb-2 rounded-md bg-muted">
                    <div className="font-medium">{result.tool}</div>
                    {result.output.success ? (
                      <div className="text-sm text-muted-foreground mt-2">
                        {formatResultData(result.tool, result.output.data)}
                      </div>
                    ) : (
                      <div className="text-sm text-destructive mt-2">
                        Error: {result.output.error}
                      </div>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </CommandList>
    </CommandDialog>
  )
}
