import { useState, useEffect } from "react"
import { Circle, RefreshCw, ListTodo } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"
import { API_BASE } from "@/constants"
import type { Task } from "@/types"

interface TaskDropdownProps {
  onTaskClick: (emailId: number) => void
  onTasksGenerated: () => void
}

export function TaskDropdown({ onTaskClick, onTasksGenerated }: TaskDropdownProps) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [isGenerating, setIsGenerating] = useState(false)
  const [open, setOpen] = useState(false)

  const fetchTasks = () => {
    fetch(`${API_BASE}/tasks?completed=false`)
      .then((res) => res.json())
      .then(setTasks)
  }

  const generateTasks = () => {
    setIsGenerating(true)
    fetch(`${API_BASE}/tasks/generate`, { method: "POST" })
      .then(() => {
        fetchTasks()
        onTasksGenerated()
      })
      .finally(() => setIsGenerating(false))
  }

  const toggleTask = (taskId: number, completed: boolean) => {
    fetch(`${API_BASE}/tasks/${taskId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed }),
    }).then(fetchTasks)
  }

  useEffect(() => {
    fetchTasks()
  }, [])

  useEffect(() => {
    if (open) {
      fetchTasks()
    }
  }, [open])

  const incompleteTasks = tasks.filter((t) => !t.completed)

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="relative">
          <ListTodo className="size-4" />
          {incompleteTasks.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full size-5 flex items-center justify-center">
              {incompleteTasks.length}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-80">
        <div className="flex items-center justify-between px-2 py-1.5">
          <span className="text-sm font-medium">Action Items</span>
          <Button
            variant="ghost"
            size="xs"
            onClick={generateTasks}
            disabled={isGenerating}
          >
            <RefreshCw className={`size-3 ${isGenerating ? "animate-spin" : ""}`} />
          </Button>
        </div>
        <DropdownMenuSeparator />
        {incompleteTasks.length === 0 ? (
          <div className="px-2 py-6 text-center text-sm text-muted-foreground">
            No action items
          </div>
        ) : (
          incompleteTasks.map((task) => (
            <DropdownMenuItem
              key={task.id}
              className="flex items-start gap-2 py-2 cursor-pointer"
              onClick={(e) => {
                e.preventDefault()
                onTaskClick(task.email_id)
                setOpen(false)
              }}
            >
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  toggleTask(task.id, true)
                }}
                className="shrink-0 mt-0.5"
              >
                <Circle className="size-4 text-muted-foreground hover:text-foreground" />
              </button>
              <div className="flex-1 min-w-0">
                <p className="text-sm">{task.description}</p>
                {task.priority === "high" && (
                  <span className="text-xs text-destructive">High Priority</span>
                )}
              </div>
            </DropdownMenuItem>
          ))
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
