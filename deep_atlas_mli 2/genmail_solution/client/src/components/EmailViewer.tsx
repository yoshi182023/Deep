import { useState, useRef, useEffect } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ButtonGroup } from "@/components/ui/button-group"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
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
import { Reply, Trash2, Mail } from "lucide-react"
import type { Email } from "@/types"
import { PRIMARY_USER, API_BASE } from "@/constants"
import { formatDate, getInitials } from "@/utils"

interface EmailViewerProps {
  selectedEmail: Email | null
  threadEmails: Email[]
  onEmailSent: () => void
  onDelete: () => void
}

export function EmailViewer({ selectedEmail, threadEmails, onEmailSent, onDelete }: EmailViewerProps) {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [replyBody, setReplyBody] = useState("")
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false)
  const [draftGenerated, setDraftGenerated] = useState(false)
  const [feedback, setFeedback] = useState("")
  const [isRefining, setIsRefining] = useState(false)
  const selectedRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (selectedRef.current) {
      selectedRef.current.scrollIntoView({ behavior: "smooth", block: "center" })
    }
  }, [selectedEmail?.id])

  useEffect(() => {
    if (drawerOpen && !draftGenerated) {
      handleGenerateDraft()
    } else if (!drawerOpen) {
      setDraftGenerated(false)
      setFeedback("")
      setReplyBody("")
    }
  }, [drawerOpen])

  const handleGenerateDraft = async () => {
    if (!selectedEmail) return
    setIsGeneratingDraft(true)
    try {
      const response = await fetch(`${API_BASE}/emails/${selectedEmail.id}/draft-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      })
      const data = await response.json()
      setReplyBody(data.draft)
      setDraftGenerated(true)
    } catch (error) {
      console.error("Error generating draft:", error)
    } finally {
      setIsGeneratingDraft(false)
    }
  }

  const handleRefineDraft = async (toneButton?: string) => {
    if (!selectedEmail) return
    setIsRefining(true)
    try {
      const response = await fetch(`${API_BASE}/emails/${selectedEmail.id}/draft-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          previous_draft: replyBody,
          feedback: feedback || undefined,
          tone: toneButton || undefined
        })
      })
      const data = await response.json()
      setReplyBody(data.draft)
      setFeedback("")
    } catch (error) {
      console.error("Error refining draft:", error)
    } finally {
      setIsRefining(false)
    }
  }

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
      setDraftGenerated(false)
      setFeedback("")
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
    }).then(onEmailSent)
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
                    disabled={isGeneratingDraft || isRefining}
                  />

                  {isGeneratingDraft && (
                    <div className="text-sm text-muted-foreground">Generating draft...</div>
                  )}

                  {isRefining && (
                    <div className="text-sm text-muted-foreground">Refining draft...</div>
                  )}

                  {draftGenerated && !isGeneratingDraft && (
                    <>
                      <Separator />
                      <div className="text-sm font-medium">Refine your draft</div>

                      <ButtonGroup>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefineDraft("formal")}
                          disabled={isRefining}
                        >
                          Formal
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefineDraft("concise")}
                          disabled={isRefining}
                        >
                          Concise
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleRefineDraft("friendly")}
                          disabled={isRefining}
                        >
                          Friendly
                        </Button>
                      </ButtonGroup>

                      <Input
                        placeholder="Additional feedback..."
                        value={feedback}
                        onChange={(e) => setFeedback(e.target.value)}
                        disabled={isRefining}
                      />

                      <Button
                        variant="outline"
                        onClick={() => handleRefineDraft()}
                        disabled={!feedback.trim() || isRefining}
                      >
                        Refine Draft
                      </Button>
                    </>
                  )}
                </div>
                <DrawerFooter>
                  <Button onClick={handleReply} disabled={isGeneratingDraft || isRefining}>
                    Send
                  </Button>
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
