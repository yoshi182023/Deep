// 邮件数据类型，与后端 Email.to_dict() 返回结构一致
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
