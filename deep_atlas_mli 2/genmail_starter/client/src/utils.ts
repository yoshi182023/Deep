// 前端工具函数

/** 将 ISO 时间格式化为可读日期 */
export function formatDate(dateString: string) {
  const date = new Date(dateString)
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  })
}

/** 从邮箱地址提取头像缩写（取 @ 前两位） */
export function getInitials(email: string) {
  const name = email.split("@")[0]
  return name.slice(0, 2).toUpperCase()
}
