// 左侧邮件列表：展示收件、撰写新邮件
import { useState } from "react"
import {
  Item,
  ItemContent,
  ItemTitle,
  ItemDescription,
  ItemGroup,
  ItemSeparator,
} from "@/components/ui/item"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Drawer,
  DrawerTrigger,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerFooter,
  DrawerClose,
} from "@/components/ui/drawer"
import { Send, Plus, Loader2 } from "lucide-react"  // Loader2 用于未读摘要加载动画
import type { Email } from "@/types"
import { PRIMARY_USER, API_BASE } from "@/constants"
import { formatDate, getInitials } from "@/utils"

// 功能 2：/ai/digest 接口返回结构
interface UnreadDigest {
  unread_count: number  // 未读邮件数量
  digest: string        // 按发件人分组的摘要正文
}

// =============================================================================
// 第四步：/ai/analytics 接口返回结构
// -----------------------------------------------------------------------------
// 后端先用 SQL 算出 facts（客观数字），再由 LLM 生成 report（可读报告）。
// 前端主要展示 report；facts 可供调试或后续做图表。
// =============================================================================
interface InboxAnalytics {
  total_emails: number
  unread_count: number
  thread_count: number
  report: string  // 中文「收件箱智能分析」正文
}

// =============================================================================
// 第五步：/ai/commitments 接口返回结构
// -----------------------------------------------------------------------------
// 从 pm 发出的邮件中提取承诺；commitments 为结构化列表，report 为中文可读报告。
// =============================================================================
interface CommitmentTracker {
  sent_email_count: number
  commitment_count: number
  commitments: Array<{
    recipient: string
    recipient_name: string
    quote: string
    thread_id: string
    thread_subject: string
    sent_at: string
    deadline_text: string | null
    status: string
    status_reason: string
  }>
  report: string
}

interface EmailListProps {
  emails: Email[]
  selectedEmail: Email | null
  onSelect: (email: Email) => void
  onEmailSent: () => void
}

export function EmailList({ emails, selectedEmail, onSelect, onEmailSent }: EmailListProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  // --- 功能 2：未读邮件摘要 ---
  const [digestOpen, setDigestOpen] = useState(false)       // 摘要抽屉是否打开
  const [digestLoading, setDigestLoading] = useState(false) // 是否正在请求 LLM
  const [digest, setDigest] = useState<UnreadDigest | null>(null)
  const [digestError, setDigestError] = useState<string | null>(null)
  // --- 第四步：统计仪表盘 / 收件箱智能分析 ---
  const [analyticsOpen, setAnalyticsOpen] = useState(false)       // 分析抽屉是否打开
  const [analyticsLoading, setAnalyticsLoading] = useState(false) // 是否正在请求
  const [analytics, setAnalytics] = useState<InboxAnalytics | null>(null)
  const [analyticsError, setAnalyticsError] = useState<string | null>(null)
  // --- 第五步：承诺追踪 ---
  const [commitmentsOpen, setCommitmentsOpen] = useState(false)
  const [commitmentsLoading, setCommitmentsLoading] = useState(false)
  const [commitments, setCommitments] = useState<CommitmentTracker | null>(null)
  const [commitmentsError, setCommitmentsError] = useState<string | null>(null)
  const [recipient, setRecipient] = useState("")
  const [subject, setSubject] = useState("")
  const [body, setBody] = useState("")

  // 调用 POST /ai/digest，在抽屉中展示未读摘要
  const handleDigest = () => {
    setDigestOpen(true)
    setDigestLoading(true)
    setDigest(null)
    setDigestError(null)

    fetch(`${API_BASE}/ai/digest`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          const hint = data.hint ? ` ${data.hint}` : ""
          throw new Error((data.error || "生成未读摘要失败") + hint)
        }
        setDigest(data as UnreadDigest)
      })
      .catch((err: Error) => {
        setDigestError(err.message || "生成未读摘要失败")
      })
      .finally(() => {
        setDigestLoading(false)
      })
  }

  // 第四步：调用 POST /ai/analytics，展示超越 /stats 的收件箱智能分析
  const handleAnalytics = () => {
    setAnalyticsOpen(true)
    setAnalyticsLoading(true)
    setAnalytics(null)
    setAnalyticsError(null)

    fetch(`${API_BASE}/ai/analytics`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          const hint = data.hint ? ` ${data.hint}` : ""
          throw new Error((data.error || "收件箱分析失败") + hint)
        }
        setAnalytics(data as InboxAnalytics)
      })
      .catch((err: Error) => {
        setAnalyticsError(err.message || "收件箱分析失败")
      })
      .finally(() => {
        setAnalyticsLoading(false)
      })
  }

  // 第五步：调用 POST /ai/commitments，扫描已发送邮件中的承诺
  const handleCommitments = () => {
    setCommitmentsOpen(true)
    setCommitmentsLoading(true)
    setCommitments(null)
    setCommitmentsError(null)

    fetch(`${API_BASE}/ai/commitments`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          const hint = data.hint ? ` ${data.hint}` : ""
          throw new Error((data.error || "承诺追踪失败") + hint)
        }
        setCommitments(data as CommitmentTracker)
      })
      .catch((err: Error) => {
        setCommitmentsError(err.message || "承诺追踪失败")
      })
      .finally(() => {
        setCommitmentsLoading(false)
      })
  }

  // 以当前用户身份发送新邮件（新线程）
  const handleSend = () => {
    fetch(`${API_BASE}/emails`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sender: PRIMARY_USER, recipient, subject, body }),
    }).then(() => {
      setRecipient("")
      setSubject("")
      setBody("")
      setDrawerOpen(false)
      onEmailSent()
    })
  }

  return (
    <aside className="w-80 border-r flex flex-col">
      <div className="p-4 border-b flex items-center justify-between">
        <h1 className="font-semibold">GenMail</h1>
        <div className="flex items-center gap-1 flex-wrap justify-end">
          {/* 功能 2：未读摘要按钮 */}
          <Button variant="outline" size="sm" onClick={handleDigest} disabled={digestLoading}>
            {digestLoading ? <Loader2 className="size-4 animate-spin" /> : "未读摘要"}
          </Button>
          {/* 第四步：收件箱智能分析按钮（功能 4） */}
          <Button variant="outline" size="sm" onClick={handleAnalytics} disabled={analyticsLoading}>
            {analyticsLoading ? <Loader2 className="size-4 animate-spin" /> : "收件箱分析"}
          </Button>
          {/* 第五步：承诺追踪按钮 */}
          <Button variant="outline" size="sm" onClick={handleCommitments} disabled={commitmentsLoading}>
            {commitmentsLoading ? <Loader2 className="size-4 animate-spin" /> : "承诺追踪"}
          </Button>
          {/* 功能 2：摘要结果抽屉 */}
          <Drawer direction="right" open={digestOpen} onOpenChange={setDigestOpen}>
            <DrawerContent>
              <DrawerHeader>
                <DrawerTitle>未读邮件摘要</DrawerTitle>
              </DrawerHeader>
              <div className="flex flex-col gap-4 p-4">
                {digestLoading && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" />
                    正在生成摘要...
                  </div>
                )}
                {digestError && (
                  <p className="text-sm text-destructive">{digestError}</p>
                )}
                {digest && (
                  <p className="text-sm whitespace-pre-wrap">{digest.digest}</p>
                )}
              </div>
              <DrawerFooter>
                {digestError && (
                  <Button variant="outline" onClick={handleDigest} disabled={digestLoading}>
                    重试
                  </Button>
                )}
                <DrawerClose asChild>
                  <Button variant="outline">关闭</Button>
                </DrawerClose>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
          {/* 第四步：收件箱分析结果抽屉 */}
          <Drawer direction="right" open={analyticsOpen} onOpenChange={setAnalyticsOpen}>
            <DrawerContent>
              <DrawerHeader>
                <DrawerTitle>收件箱智能分析</DrawerTitle>
              </DrawerHeader>
              <div className="flex flex-col gap-4 p-4">
                {analyticsLoading && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" />
                    正在分析收件箱...
                  </div>
                )}
                {analyticsError && (
                  <p className="text-sm text-destructive">{analyticsError}</p>
                )}
                {analytics && (
                  <>
                    <p className="text-sm whitespace-pre-wrap">{analytics.report}</p>
                    <p className="text-xs text-muted-foreground">
                      {analytics.total_emails} 封邮件 · {analytics.unread_count} 封未读 · {analytics.thread_count} 个线程
                    </p>
                  </>
                )}
              </div>
              <DrawerFooter>
                {analyticsError && (
                  <Button variant="outline" onClick={handleAnalytics} disabled={analyticsLoading}>
                    重试
                  </Button>
                )}
                <DrawerClose asChild>
                  <Button variant="outline">关闭</Button>
                </DrawerClose>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
          {/* 第五步：承诺追踪结果抽屉 */}
          <Drawer direction="right" open={commitmentsOpen} onOpenChange={setCommitmentsOpen}>
            <DrawerContent>
              <DrawerHeader>
                <DrawerTitle>你的承诺</DrawerTitle>
              </DrawerHeader>
              <div className="flex flex-col gap-4 p-4">
                {commitmentsLoading && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="size-4 animate-spin" />
                    正在扫描已发送邮件...
                  </div>
                )}
                {commitmentsError && (
                  <p className="text-sm text-destructive">{commitmentsError}</p>
                )}
                {commitments && (
                  <>
                    <p className="text-sm whitespace-pre-wrap">{commitments.report}</p>
                    <p className="text-xs text-muted-foreground">
                      已扫描 {commitments.sent_email_count} 封已发送邮件 · 发现 {commitments.commitment_count} 条承诺
                    </p>
                  </>
                )}
              </div>
              <DrawerFooter>
                {commitmentsError && (
                  <Button variant="outline" onClick={handleCommitments} disabled={commitmentsLoading}>
                    重试
                  </Button>
                )}
                <DrawerClose asChild>
                  <Button variant="outline">关闭</Button>
                </DrawerClose>
              </DrawerFooter>
            </DrawerContent>
          </Drawer>
        <Drawer direction="right" open={drawerOpen} onOpenChange={setDrawerOpen}>
          <DrawerTrigger asChild>
            <Button variant="ghost" size="icon">
              <Plus className="size-4" />
            </Button>
          </DrawerTrigger>
          <DrawerContent>
            <DrawerHeader>
              <DrawerTitle>New Email</DrawerTitle>
            </DrawerHeader>
            <div className="flex flex-col gap-4 p-4">
              <Input
                placeholder="Recipient"
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
              />
              <Input
                placeholder="Subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
              />
              <Textarea
                placeholder="Message"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                className="min-h-32"
              />
            </div>
            <DrawerFooter>
              <Button onClick={handleSend}>Send</Button>
              <DrawerClose asChild>
                <Button variant="outline">Cancel</Button>
              </DrawerClose>
            </DrawerFooter>
          </DrawerContent>
        </Drawer>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        <ItemGroup>
          {emails.map((email, index) => (
            <div key={email.id}>
              {index > 0 && <ItemSeparator />}
              <Item
                size="sm"
                className={`cursor-pointer hover:bg-accent/50 ${
                  selectedEmail?.id === email.id ? "bg-accent" : ""
                }`}
                onClick={() => onSelect(email)}
              >
                <Avatar>
                  <AvatarFallback>{getInitials(email.sender)}</AvatarFallback>
                </Avatar>
                <ItemContent>
                  <div className="flex items-center gap-2">
                    {!email.is_read && (
                      <div className="size-2 rounded-full bg-blue-500 shrink-0" />
                    )}
                    <ItemTitle className={`text-sm ${!email.is_read ? "font-bold" : ""}`}>
                      {email.sender.split("@")[0]}
                    </ItemTitle>
                  </div>
                  <ItemDescription className={`line-clamp-1 ${!email.is_read ? "font-semibold text-foreground" : "font-medium text-foreground"}`}>
                    {email.subject}
                  </ItemDescription>
                  <ItemDescription className="line-clamp-1">
                    {email.body}
                  </ItemDescription>
                </ItemContent>
                <div className="flex flex-col items-end shrink-0 gap-1">
                  <span className="text-xs text-muted-foreground">
                    {formatDate(email.created_at)}
                  </span>
                  {email.sender === PRIMARY_USER && (
                    <Send className="size-3 text-muted-foreground" />
                  )}
                </div>
              </Item>
            </div>
          ))}
        </ItemGroup>
      </div>
    </aside>
  )
}
