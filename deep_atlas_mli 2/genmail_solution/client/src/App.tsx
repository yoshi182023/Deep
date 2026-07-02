import { useEffect, useState } from "react"
import type { Email } from "@/types"
import { API_BASE } from "@/constants"
import { DevControls } from "@/components/DevControls"
import { EmailList } from "@/components/EmailList"
import { EmailViewer } from "@/components/EmailViewer"
import { CommandPalette } from "@/components/CommandPalette"

function App() {
  const [emails, setEmails] = useState<Email[]>([])
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [threadEmails, setThreadEmails] = useState<Email[]>([])
  const [commandOpen, setCommandOpen] = useState(false)

  const fetchEmails = () => {
    fetch(`${API_BASE}/emails`)
      .then((res) => res.json())
      .then((data) => setEmails(data))
  }

  const generateTasksOnLoad = () => {
    fetch(`${API_BASE}/tasks/generate`, { method: "POST" })
  }

  const handleTaskClick = (emailId: number) => {
    const email = emails.find((e) => e.id === emailId)
    if (email) {
      handleSelect(email)
    }
  }

  const resetDatabase = () => {
    fetch(`${API_BASE}/reset`, { method: "POST" }).then(() => {
      setSelectedEmail(null)
      fetchEmails()
      generateTasksOnLoad()
    })
  }

  const handleDelete = () => {
    setSelectedEmail(null)
    setThreadEmails([])
    fetchEmails()
  }

  const handleSelect = (email: Email) => {
    setSelectedEmail(email)
    fetch(`${API_BASE}/emails?thread_id=${email.thread_id}`)
      .then((res) => res.json())
      .then((data: Email[]) => {
        data.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
        setThreadEmails(data)
      })
    if (!email.is_read) {
      fetch(`${API_BASE}/emails/${email.id}/read`, { method: "PATCH" }).then(fetchEmails)
    }
  }

  useEffect(() => {
    fetchEmails()
    generateTasksOnLoad()
  }, [])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        setCommandOpen(true)
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  return (
    <div className="flex flex-col h-screen">
      <DevControls onReset={resetDatabase} emails={emails} onEmailCreated={fetchEmails} />
      <div className="flex flex-1 min-h-0">
        <EmailList
          emails={emails}
          selectedEmail={selectedEmail}
          onSelect={handleSelect}
          onEmailSent={fetchEmails}
          onTaskClick={handleTaskClick}
        />
        <main className="flex-1 flex flex-col">
          <EmailViewer
            selectedEmail={selectedEmail}
            threadEmails={threadEmails}
            onEmailSent={fetchEmails}
            onDelete={handleDelete}
          />
        </main>
      </div>
      <CommandPalette
        open={commandOpen}
        onOpenChange={setCommandOpen}
        onEmailSelect={handleSelect}
        onRefresh={fetchEmails}
      />
    </div>
  )
}

export default App
