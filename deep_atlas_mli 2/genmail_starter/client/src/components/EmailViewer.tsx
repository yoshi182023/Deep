// 右侧邮件详情：展示线程对话、回复、删除、标未读
import { useState, useRef, useEffect } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ButtonGroup } from "@/components/ui/button-group"
import { Separator } from "@/components/ui/separator"
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
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription } from "@/components/ui/empty"
import { Reply, Trash2, Mail, Sparkles, Loader2, Tags, AlertTriangle } from "lucide-react"
import type { Email } from "@/types"
import { PRIMARY_USER, API_BASE } from "@/constants"
import { formatDate, getInitials } from "@/utils"

interface ThreadSummary {
  thread_id: string
  message_count: number
  summary: string
}

// 功能 3：/ai/sender/<sender> 接口返回结构
interface SenderTopics {
  sender: string       // 被分析的发件人邮箱
  email_count: number  // 该发件人的邮件总数
  analysis: string     // 主题聚类分析正文
}

// =============================================================================
// 第六步：/ai/urgency/<email_id> 接口返回结构
// -----------------------------------------------------------------------------
// Python 算 facts，LLM 返回 score / level / reasoning；不持久化。
// =============================================================================
interface UrgencyResult {
  email_id: number
  thread_id: string
  subject: string
  sender: string
  sender_name: string
  score: number | null
  level: string | null
  action_needed: boolean | null
  reasoning: string[]
  false_alarm_risk: string | null
  skipped: boolean
}

interface EmailViewerProps {
  selectedEmail: Email | null
  threadEmails: Email[]
  onEmailSent: () => void
  onDelete: () => void
}

export function EmailViewer({ selectedEmail, threadEmails, onEmailSent, onDelete }: EmailViewerProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [replyBody, setReplyBody] = useState("")
  const [summarizeOpen, setSummarizeOpen] = useState(false)
  const [summarizeLoading, setSummarizeLoading] = useState(false)
  const [summary, setSummary] = useState<ThreadSummary | null>(null)
  const [summaryError, setSummaryError] = useState<string | null>(null)
  // --- 功能 3：发件人主题分析 ---
  const [topicsOpen, setTopicsOpen] = useState(false)
  const [topicsLoading, setTopicsLoading] = useState(false)
  const [topics, setTopics] = useState<SenderTopics | null>(null)
  const [topicsError, setTopicsError] = useState<string | null>(null)
  // --- 第六步：紧急程度分类 ---
  const [urgencyOpen, setUrgencyOpen] = useState(false)
  const [urgencyLoading, setUrgencyLoading] = useState(false)
  const [urgency, setUrgency] = useState<UrgencyResult | null>(null)
  const [urgencyError, setUrgencyError] = useState<string | null>(null)
  const selectedRef = useRef<HTMLDivElement>(null)

  // 选中邮件变化时滚动到该条消息
  useEffect(() => {
    if (selectedRef.current) {
      selectedRef.current.scrollIntoView({ behavior: "smooth", block: "center" })
    }
  }, [selectedEmail?.id])

  if (!selectedEmail) {
    return (
      <Empty className="flex-1">
        <EmptyHeader>
          <EmptyTitle>No email selected</EmptyTitle>
          <EmptyDescription>
            Select an email from the sidebar to view its contents.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    )
  }

  const threadSubject = threadEmails[0]?.subject || selectedEmail.subject
  const latestEmail = threadEmails[threadEmails.length - 1] || selectedEmail
  const activeSummary = summary?.thread_id === selectedEmail.thread_id ? summary : null
  // 分析对象：当前邮件的对方联系人（非 pm@acme.com 的一方）
  const contactEmail =
    selectedEmail.sender === PRIMARY_USER ? selectedEmail.recipient : selectedEmail.sender
  const activeTopics = topics?.sender === contactEmail ? topics : null
  const activeUrgency = urgency?.email_id === selectedEmail.id ? urgency : null
  const isInboundToUser =
    selectedEmail.recipient === PRIMARY_USER && selectedEmail.sender !== PRIMARY_USER

  const urgencyLevelLabel = (level: string | null) => {
    if (level === "high") return "高"
    if (level === "medium") return "中"
    if (level === "low") return "低"
    return "—"
  }

  // 回复线程中最新一封邮件
  const handleReply = () => {
    const replySubject = latestEmail.subject.startsWith("Re: ") ? latestEmail.subject : `Re: ${latestEmail.subject}`
    fetch(`${API_BASE}/emails`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sender: PRIMARY_USER,
        recipient: latestEmail.sender,
        subject: replySubject,
        body: replyBody,
        thread_id: selectedEmail.thread_id,
      }),
    }).then(() => {
      setReplyBody("")
      setDrawerOpen(false)
      onEmailSent()
    })
  }

  const handleDelete = () => {
    fetch(`${API_BASE}/emails/${selectedEmail.id}`, { method: "DELETE" }).then(onDelete)
  }

  const handleMarkUnread = () => {
    fetch(`${API_BASE}/emails/${selectedEmail.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_read: false }),
    }).then(onDelete)
  }

  const handleSummarize = () => {
    setSummarizeOpen(true)
    setSummarizeLoading(true)
    setSummary(null)
    setSummaryError(null)

    fetch(`${API_BASE}/ai/summarize/${selectedEmail.thread_id}`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          const hint = data.hint ? ` ${data.hint}` : ""
          throw new Error((data.error || "Failed to summarize thread") + hint)
        }
        setSummary(data as ThreadSummary)
      })
      .catch((err: Error) => {
        setSummaryError(err.message || "Failed to summarize thread")
      })
      .finally(() => {
        setSummarizeLoading(false)
      })
  }

  // 调用 POST /ai/sender/<email>，分析当前联系人的邮件主题聚类
  const handleSenderTopics = () => {
    setTopicsOpen(true)
    setTopicsLoading(true)
    setTopics(null)
    setTopicsError(null)

    fetch(`${API_BASE}/ai/sender/${encodeURIComponent(contactEmail)}`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          const hint = data.hint ? ` ${data.hint}` : ""
          throw new Error((data.error || "发件人主题分析失败") + hint)
        }
        setTopics(data as SenderTopics)
      })
      .catch((err: Error) => {
        setTopicsError(err.message || "发件人主题分析失败")
      })
      .finally(() => {
        setTopicsLoading(false)
      })
  }

  // 调用 POST /ai/urgency/<email_id>，分析当前选中邮件的紧急程度
  const handleUrgency = () => {
    setUrgencyOpen(true)
    setUrgencyLoading(true)
    setUrgency(null)
    setUrgencyError(null)

    fetch(`${API_BASE}/ai/urgency/${selectedEmail.id}`, { method: "POST" })
      .then(async (res) => {
        const data = await res.json()
        if (!res.ok) {
          const hint = data.hint ? ` ${data.hint}` : ""
          throw new Error((data.error || "紧急程度分析失败") + hint)
        }
        setUrgency(data as UrgencyResult)
      })
      .catch((err: Error) => {
        setUrgencyError(err.message || "紧急程度分析失败")
      })
      .finally(() => {
        setUrgencyLoading(false)
      })
  }

  return (
    <>
      <div className="p-6 border-b flex justify-center">
        <div className="w-full max-w-[100ch]">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-xl font-semibold">{threadSubject}</h2>
            <Badge variant="outline" className="text-xs">
              Thread: {selectedEmail.thread_id.slice(0, 8)}
            </Badge>
          </div>
          <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {threadEmails.length} {threadEmails.length === 1 ? "message" : "messages"}
            </div>
            <ButtonGroup>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSummarize}
                  disabled={summarizeLoading}
                >
                  {summarizeLoading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Sparkles className="size-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>Summarize</TooltipContent>
            </Tooltip>
            {/* 功能 3：发件人主题分析按钮 */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSenderTopics}
                  disabled={topicsLoading}
                >
                  {topicsLoading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Tags className="size-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>发件人主题</TooltipContent>
            </Tooltip>
            {/* 第六步：紧急程度分类按钮（仅分析收到的邮件） */}
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleUrgency}
                  disabled={urgencyLoading || !isInboundToUser}
                >
                  {urgencyLoading ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <AlertTriangle className="size-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {isInboundToUser ? "紧急程度" : "仅分析收到的邮件"}
              </TooltipContent>
            </Tooltip>
            {/* 第六步：紧急程度结果抽屉 */}
            <Drawer direction="right" open={urgencyOpen} onOpenChange={setUrgencyOpen}>
              <DrawerContent>
                <DrawerHeader>
                  <DrawerTitle>紧急程度</DrawerTitle>
                </DrawerHeader>
                <div className="flex flex-col gap-4 p-4">
                  {urgencyLoading && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="size-4 animate-spin" />
                      正在分析紧急程度...
                    </div>
                  )}
                  {urgencyError && (
                    <p className="text-sm text-destructive">{urgencyError}</p>
                  )}
                  {activeUrgency && (
                    <>
                      {activeUrgency.skipped ? (
                        <p className="text-sm text-muted-foreground">
                          {activeUrgency.reasoning.join(" ")}
                        </p>
                      ) : (
                        <>
                          <p className="text-lg font-semibold">
                            {urgencyLevelLabel(activeUrgency.level)}（{activeUrgency.score}/10）
                          </p>
                          {activeUrgency.action_needed !== null && (
                            <p className="text-sm text-muted-foreground">
                              {activeUrgency.action_needed
                                ? "仍需你采取行动"
                                : "你已回复或暂无需行动"}
                            </p>
                          )}
                          <ul className="text-sm list-disc pl-5 space-y-1">
                            {activeUrgency.reasoning.map((line, i) => (
                              <li key={i}>{line}</li>
                            ))}
                          </ul>
                          {activeUrgency.false_alarm_risk && (
                            <p className="text-xs text-muted-foreground">
                              误报风险：{activeUrgency.false_alarm_risk}
                            </p>
                          )}
                        </>
                      )}
                      <p className="text-xs text-muted-foreground">
                        {activeUrgency.sender_name} · {activeUrgency.subject}
                      </p>
                    </>
                  )}
                </div>
                <DrawerFooter>
                  {urgencyError && (
                    <Button variant="outline" onClick={handleUrgency} disabled={urgencyLoading}>
                      重试
                    </Button>
                  )}
                  <DrawerClose asChild>
                    <Button variant="outline">关闭</Button>
                  </DrawerClose>
                </DrawerFooter>
              </DrawerContent>
            </Drawer>
            {/* 功能 3：主题分析结果抽屉 */}
            <Drawer direction="right" open={topicsOpen} onOpenChange={setTopicsOpen}>
              <DrawerContent>
                <DrawerHeader>
                  <DrawerTitle>发件人主题分析</DrawerTitle>
                </DrawerHeader>
                <div className="flex flex-col gap-4 p-4">
                  <p className="text-xs text-muted-foreground">{contactEmail}</p>
                  {topicsLoading && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="size-4 animate-spin" />
                      正在分析主题...
                    </div>
                  )}
                  {topicsError && (
                    <p className="text-sm text-destructive">{topicsError}</p>
                  )}
                  {activeTopics && (
                    <>
                      <p className="text-sm whitespace-pre-wrap">{activeTopics.analysis}</p>
                      <p className="text-xs text-muted-foreground">
                        共 {activeTopics.email_count} 封邮件
                      </p>
                    </>
                  )}
                </div>
                <DrawerFooter>
                  {topicsError && (
                    <Button variant="outline" onClick={handleSenderTopics} disabled={topicsLoading}>
                      重试
                    </Button>
                  )}
                  <DrawerClose asChild>
                    <Button variant="outline">关闭</Button>
                  </DrawerClose>
                </DrawerFooter>
              </DrawerContent>
            </Drawer>
            <Drawer direction="right" open={summarizeOpen} onOpenChange={setSummarizeOpen}>
              <DrawerContent>
                <DrawerHeader>
                  <DrawerTitle>Thread Summary</DrawerTitle>
                </DrawerHeader>
                <div className="flex flex-col gap-4 p-4">
                  {summarizeLoading && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Loader2 className="size-4 animate-spin" />
                      Generating summary...
                    </div>
                  )}
                  {summaryError && (
                    <p className="text-sm text-destructive">{summaryError}</p>
                  )}
                  {activeSummary && (
                    <>
                      <p className="text-sm whitespace-pre-wrap">{activeSummary.summary}</p>
                      <p className="text-xs text-muted-foreground">
                        {activeSummary.message_count} {activeSummary.message_count === 1 ? "message" : "messages"} in thread
                      </p>
                    </>
                  )}
                </div>
                <DrawerFooter>
                  {summaryError && (
                    <Button variant="outline" onClick={handleSummarize} disabled={summarizeLoading}>
                      Retry
                    </Button>
                  )}
                  <DrawerClose asChild>
                    <Button variant="outline">Close</Button>
                  </DrawerClose>
                </DrawerFooter>
              </DrawerContent>
            </Drawer>
            <Drawer direction="right" open={drawerOpen} onOpenChange={setDrawerOpen}>
              <Tooltip>
                <TooltipTrigger asChild>
                  <DrawerTrigger asChild>
                    <Button variant="outline" size="sm">
                      <Reply className="size-4" />
                    </Button>
                  </DrawerTrigger>
                </TooltipTrigger>
                <TooltipContent>Reply</TooltipContent>
              </Tooltip>
              <DrawerContent>
                <DrawerHeader>
                  <DrawerTitle>Reply to {latestEmail.sender.split("@")[0]}</DrawerTitle>
                </DrawerHeader>
                <div className="flex flex-col gap-4 p-4">
                  <Textarea
                    placeholder="Write your reply..."
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    className="min-h-32"
                  />
                </div>
                <DrawerFooter>
                  <Button onClick={handleReply}>Send</Button>
                  <DrawerClose asChild>
                    <Button variant="outline">Cancel</Button>
                  </DrawerClose>
                </DrawerFooter>
              </DrawerContent>
            </Drawer>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={handleMarkUnread}>
                  <Mail className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Mark as unread</TooltipContent>
            </Tooltip>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={handleDelete}>
                  <Trash2 className="size-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Delete</TooltipContent>
            </Tooltip>
          </ButtonGroup>
          </div>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto flex justify-center">
        <div className="w-full max-w-[100ch]">
        {threadEmails.map((email, index) => (
          <div key={email.id}>
            <div
              ref={email.id === selectedEmail.id ? selectedRef : null}
              className={`p-6 ${email.id === selectedEmail.id ? "bg-accent/30" : ""}`}
            >
              <div className="flex items-start gap-4 mb-4">
                <Avatar size="lg">
                  <AvatarFallback>{getInitials(email.sender)}</AvatarFallback>
                </Avatar>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <div className="font-medium">{email.sender}</div>
                    <div className="text-sm text-muted-foreground">to {email.recipient}</div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDate(email.created_at)}
                  </div>
                </div>
              </div>
              <p className="whitespace-pre-wrap text-sm">{email.body}</p>
            </div>
            {index < threadEmails.length - 1 && <Separator />}
          </div>
        ))}
        </div>
      </div>
    </>
  )
}
