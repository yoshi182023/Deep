// 主应用：邮件列表 + 详情视图 + 开发工具
import { useEffect, useState } from "react"
import type { Email } from "@/types"
import { API_BASE } from "@/constants"
import { DevControls } from "@/components/DevControls"
import { EmailList } from "@/components/EmailList"
import { EmailViewer } from "@/components/EmailViewer"
import { InboxIntelligence } from "@/components/InboxIntelligence"

function App() {
  const [emails, setEmails] = useState<Email[]>([])  // 全部邮件
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)  // 当前选中的邮件
  const [threadEmails, setThreadEmails] = useState<Email[]>([])  // 当前线程内的所有邮件

  // 从后端拉取邮件列表
  const fetchEmails = () => {
    fetch(`${API_BASE}/emails`)
      .then((res) => res.json())
      .then((data) => setEmails(data))
  }

  // 重置数据库为种子数据
  const resetDatabase = () => {
    fetch(`${API_BASE}/reset`, { method: "POST" }).then(() => {
      setSelectedEmail(null)
      fetchEmails()
    })
  }

  // 删除邮件后刷新列表
  const handleDelete = () => {
    setSelectedEmail(null)
    setThreadEmails([])
    fetchEmails()
  }

  // 选中邮件：加载同线程邮件，未读则标记已读
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
      <InboxIntelligence />
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
