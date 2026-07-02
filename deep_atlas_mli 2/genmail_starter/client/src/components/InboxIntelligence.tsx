// =============================================================================
// 第九步：主动收件箱提醒（功能 9）— 【LangGraph HITL】
// -----------------------------------------------------------------------------
// 1. POST /ai/inbox-intelligence → LangGraph gather → interrupt 返回待确认列表
// 2. POST /ai/inbox-intelligence/resume → 用户 confirm_all 后生成报告
// =============================================================================
import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, ChevronDown, ChevronUp, Sparkles } from "lucide-react"
import { API_BASE } from "@/constants"

const JSON_POST = {
  method: "POST" as const,
  headers: { "Content-Type": "application/json" },
  body: "{}",
}

interface ProactiveInboxPending {
  run_id: string
  status: "awaiting_confirmation"
  needs_response_count: number
  commitments_due_count: number
  stalled_count: number
  needs_response: Array<{ sender_name: string; subject: string; snippet?: string }>
  commitments_due: Array<{ recipient_name: string; quote: string }>
  stalled_conversations: Array<{ blocking_party_name: string; subject: string }>
}

interface ProactiveInboxComplete {
  status: string
  report: string
  needs_response_count: number
  commitments_due_count: number
  stalled_count: number
}

export function InboxIntelligence() {
  const [loading, setLoading] = useState(true)
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState<ProactiveInboxPending | null>(null)
  const [data, setData] = useState<ProactiveInboxComplete | null>(null)
  const [collapsed, setCollapsed] = useState(false)
  const fetchSeq = useRef(0)

  // 【LangGraph】invoke 到 human_review interrupt
  const fetchIntelligence = () => {
    const seq = ++fetchSeq.current
    setLoading(true)
    setError(null)
    setPending(null)
    setData(null)

    fetch(`${API_BASE}/ai/inbox-intelligence`, JSON_POST)
      .then(async (res) => {
        const json = await res.json()
        if (seq !== fetchSeq.current) return
        if (!res.ok) {
          const hint = json.hint ? ` ${json.hint}` : ""
          throw new Error((json.error || "收件箱智能加载失败") + hint)
        }
        if (json.status === "awaiting_confirmation") {
          setPending(json as ProactiveInboxPending)
        } else {
          setData(json as ProactiveInboxComplete)
        }
      })
      .catch((err: Error) => {
        if (seq !== fetchSeq.current) return
        setError(err.message || "收件箱智能加载失败")
      })
      .finally(() => {
        if (seq === fetchSeq.current) setLoading(false)
      })
  }

  // 【LangGraph】Command(resume) 确认待办并生成报告
  const handleConfirm = () => {
    if (!pending?.run_id) return
    setConfirming(true)
    setError(null)

    fetch(`${API_BASE}/ai/inbox-intelligence/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: pending.run_id, action: "confirm_all" }),
    })
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) {
          const hint = json.hint ? ` ${json.hint}` : ""
          const msg = (json.error || "生成报告失败") + hint
          if (msg.includes("会话已过期") || msg.includes("过期")) {
            fetchIntelligence()
          }
          throw new Error(msg)
        }
        setPending(null)
        setData(json as ProactiveInboxComplete)
      })
      .catch((err: Error) => {
        setError(err.message || "生成报告失败")
      })
      .finally(() => {
        setConfirming(false)
      })
  }

  const handleSkip = () => {
    if (!pending?.run_id) return
    setConfirming(true)
    fetch(`${API_BASE}/ai/inbox-intelligence/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_id: pending.run_id, action: "skip" }),
    })
      .then(async (res) => {
        const json = await res.json()
        if (!res.ok) {
          if ((json.error || "").includes("会话已过期")) fetchIntelligence()
          throw new Error(json.error || "操作失败")
        }
        setPending(null)
        setData(json as ProactiveInboxComplete)
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setConfirming(false))
  }

  useEffect(() => {
    fetchIntelligence()
  }, [])

  const totalItems = pending
    ? pending.needs_response_count + pending.commitments_due_count + pending.stalled_count
    : (data?.needs_response_count ?? 0) +
      (data?.commitments_due_count ?? 0) +
      (data?.stalled_count ?? 0)

  const showPending = pending && !loading && !data

  return (
    <div className="border-b bg-muted/30">
      <div className="flex items-center justify-between px-4 py-2 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <Sparkles className="size-4 shrink-0 text-primary" />
          <span className="text-sm font-medium truncate">收件箱智能</span>
          {showPending && totalItems > 0 && (
            <span className="text-xs text-muted-foreground shrink-0">
              {totalItems} 项待确认
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button variant="ghost" size="sm" onClick={fetchIntelligence} disabled={loading || confirming}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : "刷新"}
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed((v) => !v)}
            aria-label={collapsed ? "展开" : "收起"}
          >
            {collapsed ? <ChevronDown className="size-4" /> : <ChevronUp className="size-4" />}
          </Button>
        </div>
      </div>
      {!collapsed && (
        <div className="px-4 pb-3">
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
              <Loader2 className="size-4 animate-spin" />
              正在分析收件箱...
            </div>
          )}
          {error && (
            <div className="flex items-center gap-2 py-2">
              <p className="text-sm text-destructive">{error}</p>
              <Button variant="outline" size="sm" onClick={fetchIntelligence}>
                重试
              </Button>
            </div>
          )}
          {showPending && (
            <div className="flex flex-col gap-3 py-2">
              <p className="text-sm text-muted-foreground">
                {totalItems > 0
                  ? "发现待关注事项，请确认后生成报告："
                  : "暂无待关注事项，可直接生成空报告或跳过。"}
              </p>
              {pending.needs_response_count > 0 && (
                <div className="text-sm">
                  <p className="font-medium">🔴 需要你回复（{pending.needs_response_count}）</p>
                  <ul className="list-disc pl-5 text-muted-foreground">
                    {pending.needs_response.slice(0, 3).map((item, i) => (
                      <li key={i}>
                        {item.sender_name}：{item.subject}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {pending.stalled_count > 0 && (
                <div className="text-sm">
                  <p className="font-medium">⚠️ 停滞对话（{pending.stalled_count}）</p>
                  <ul className="list-disc pl-5 text-muted-foreground">
                    {pending.stalled_conversations.slice(0, 2).map((item, i) => (
                      <li key={i}>
                        {item.blocking_party_name}：{item.subject}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {pending.commitments_due_count > 0 && (
                <div className="text-sm">
                  <p className="font-medium">⏳ 到期承诺（{pending.commitments_due_count}）</p>
                </div>
              )}
              <div className="flex gap-2">
                <Button size="sm" onClick={handleConfirm} disabled={confirming}>
                  {confirming ? <Loader2 className="size-4 animate-spin" /> : "确认并生成报告"}
                </Button>
                <Button size="sm" variant="outline" onClick={handleSkip} disabled={confirming}>
                  跳过
                </Button>
              </div>
            </div>
          )}
          {data && !loading && data.report && (
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{data.report}</p>
          )}
        </div>
      )}
    </div>
  )
}
