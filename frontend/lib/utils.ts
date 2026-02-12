import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTimestamp(ts: number): string {
  return new Date(ts * 1000).toLocaleString()
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return '-'
  if (ms < 1) return `${(ms * 1000).toFixed(0)}us`
  if (ms < 100) return `${ms.toFixed(1)}ms`
  return `${ms.toFixed(0)}ms`
}

export function statusColor(status: string): string {
  switch (status) {
    case 'online': return 'text-green-500'
    case 'offline': return 'text-red-500'
    case 'degraded': return 'text-yellow-500'
    default: return 'text-muted-foreground'
  }
}

export function statusBg(status: string): string {
  switch (status) {
    case 'online': return 'bg-green-500/10 text-green-500 border-green-500/20'
    case 'offline': return 'bg-red-500/10 text-red-500 border-red-500/20'
    case 'degraded': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
    default: return 'bg-muted text-muted-foreground border-border'
  }
}

export function lossColor(pct: number | null | undefined): string {
  if (pct === null || pct === undefined) return 'text-muted-foreground'
  if (pct === 0) return 'text-green-500'
  if (pct < 1) return 'text-yellow-500'
  if (pct < 5) return 'text-orange-500'
  return 'text-red-500'
}
