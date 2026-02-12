interface Notification {
  id: number
  device_id: number
  device_name: string | null
  type: string
  message: string
  is_read: boolean
  created_at: number
}

interface NotificationList {
  notifications: Notification[]
  unread_count: number
}

export function useNotifications() {
  const notifications = useState<Notification[]>('notifications', () => [])
  const unreadCount = useState('unreadCount', () => 0)
  const api = useApi()
  let interval: ReturnType<typeof setInterval> | null = null

  async function fetchNotifications() {
    try {
      const data = await api.get<NotificationList>('/notifications')
      notifications.value = data.notifications
      unreadCount.value = data.unread_count
    } catch (e) {
      console.error('Failed to fetch notifications:', e)
    }
  }

  async function markRead(id: number) {
    try {
      await api.put(`/notifications/${id}/read`)
      const notif = notifications.value.find(n => n.id === id)
      if (notif && !notif.is_read) {
        notif.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (e) {
      console.error('Failed to mark notification read:', e)
    }
  }

  async function markAllRead() {
    try {
      await api.put('/notifications/read-all')
      notifications.value.forEach(n => n.is_read = true)
      unreadCount.value = 0
    } catch (e) {
      console.error('Failed to mark all read:', e)
    }
  }

  function startPolling() {
    fetchNotifications()
    interval = setInterval(fetchNotifications, 10000)
  }

  function stopPolling() {
    if (interval) {
      clearInterval(interval)
      interval = null
    }
  }

  return { notifications, unreadCount, fetchNotifications, markRead, markAllRead, startPolling, stopPolling }
}
