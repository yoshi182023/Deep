export type Email = {
  id: number
  thread_id: string
  sender: string
  recipient: string
  subject: string
  body: string
  created_at: string
  is_read: boolean
}

export type Task = {
  id: number
  description: string
  email_id: number
  thread_id: string
  priority: "high" | "medium" | "low"
  completed: boolean
  created_at: string
}
