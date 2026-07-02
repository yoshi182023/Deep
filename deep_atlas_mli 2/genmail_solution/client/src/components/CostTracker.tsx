import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Drawer,
  DrawerTrigger,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerClose,
} from "@/components/ui/drawer"
import { API_BASE } from "@/constants"
import { DollarSign } from "lucide-react"

interface AgentStats {
  overview: {
    total_calls: number
    total_cost_usd: number
    total_tokens: number
    avg_latency_ms: number
  }
  by_agent: Array<{
    agent_name: string
    call_count: number
    total_tokens: number
    total_cost_usd: number
    avg_latency_ms: number
  }>
  by_operation: Array<{
    operation: string
    call_count: number
    total_tokens: number
    total_cost_usd: number
  }>
}

interface AgentLog {
  id: number
  agent_name: string
  operation: string
  model: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost_usd: number
  latency_ms: number
  created_at: string
}

export function CostTracker() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [stats, setStats] = useState<AgentStats | null>(null)
  const [logs, setLogs] = useState<AgentLog[]>([])

  const fetchData = () => {
    fetch(`${API_BASE}/agent-logs/stats`)
      .then((res) => res.json())
      .then(setStats)
    fetch(`${API_BASE}/agent-logs?limit=20`)
      .then((res) => res.json())
      .then(setLogs)
  }

  useEffect(() => {
    if (drawerOpen) {
      fetchData()
      const interval = setInterval(fetchData, 5000)
      return () => clearInterval(interval)
    }
  }, [drawerOpen])

  const formatCost = (cost: number) => {
    if (cost === 0) return "$0.00"
    if (cost < 0.01) return `$${(cost * 1000).toFixed(4)}k`
    return `$${cost.toFixed(4)}`
  }

  const formatTime = (ms: number) => {
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  return (
    <Drawer direction="right" open={drawerOpen} onOpenChange={setDrawerOpen}>
      <DrawerTrigger asChild>
        <Button variant="outline" size="xs">
          <DollarSign className="size-3" />
          Cost Tracker
        </Button>
      </DrawerTrigger>
      <DrawerContent className="w-[600px]">
        <DrawerHeader>
          <DrawerTitle>Agent Cost Tracker</DrawerTitle>
        </DrawerHeader>

        <div className="flex flex-col gap-6 p-4 overflow-y-auto">
          {stats && (
            <>
              <Card className="p-4">
                <h3 className="font-semibold mb-3">Overview</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-muted-foreground">Total Calls</div>
                    <div className="text-2xl font-bold">{stats.overview.total_calls}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Total Cost</div>
                    <div className="text-2xl font-bold">{formatCost(stats.overview.total_cost_usd)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Total Tokens</div>
                    <div className="text-2xl font-bold">{stats.overview.total_tokens.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Avg Latency</div>
                    <div className="text-2xl font-bold">{formatTime(stats.overview.avg_latency_ms)}</div>
                  </div>
                </div>
              </Card>

              <div>
                <h3 className="font-semibold mb-3">By Agent</h3>
                <div className="space-y-2">
                  {stats.by_agent.map((agent) => (
                    <Card key={agent.agent_name} className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline">{agent.agent_name}</Badge>
                        <span className="text-sm text-muted-foreground">{agent.call_count} calls</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <div className="text-muted-foreground">Tokens</div>
                          <div className="font-medium">{agent.total_tokens.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Cost</div>
                          <div className="font-medium">{formatCost(agent.total_cost_usd)}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Avg Latency</div>
                          <div className="font-medium">{formatTime(agent.avg_latency_ms)}</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-3">By Operation</h3>
                <div className="space-y-2">
                  {stats.by_operation.map((op) => (
                    <Card key={op.operation} className="p-3">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="secondary">{op.operation}</Badge>
                        <span className="text-sm text-muted-foreground">{op.call_count} calls</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <div className="text-muted-foreground">Tokens</div>
                          <div className="font-medium">{op.total_tokens.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Cost</div>
                          <div className="font-medium">{formatCost(op.total_cost_usd)}</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-3">Recent Logs</h3>
                <div className="space-y-2">
                  {logs.map((log) => (
                    <Card key={log.id} className="p-3 text-sm">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">{log.agent_name}</Badge>
                          <Badge variant="secondary" className="text-xs">{log.operation}</Badge>
                        </div>
                        <span className="text-muted-foreground text-xs">
                          {new Date(log.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs text-muted-foreground">
                        <span>{log.total_tokens} tokens</span>
                        <span>{formatTime(log.latency_ms)}</span>
                        <span>{formatCost(log.cost_usd)}</span>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            </>
          )}

          {!stats && (
            <div className="text-center text-muted-foreground py-8">
              No agent logs yet. Try generating a draft reply or extracting tasks.
            </div>
          )}
        </div>

        <div className="border-t p-4">
          <DrawerClose asChild>
            <Button variant="outline" className="w-full">Close</Button>
          </DrawerClose>
        </div>
      </DrawerContent>
    </Drawer>
  )
}
