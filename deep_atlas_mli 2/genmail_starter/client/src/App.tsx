import { useEffect, useState } from "react"
import type { Email } from "@/types"
import { API_BASE } from "@/constants"
import { DevControls } from "@/components/DevControls"
import { EmailList } from "@/components/EmailList"
import { EmailViewer } from "@/components/EmailViewer"

function App() {
  const [emails, setEmails] = useState<Email[]>([])
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [threadEmails, setThreadEmails] = useState<Email[]>([])

  const fetchEmails = () => {
    fetch(`${API_BASE}/emails`)
      .then((res) => res.json())
      .then((data) => setEmails(data))
  }

  const resetDatabase = () => {
    fetch(`${API_BASE}/reset`, { method: "POST" }).then(() => {
      setSelectedEmail(null)
      fetchEmails()
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
    </div>
  )
}

export default App
