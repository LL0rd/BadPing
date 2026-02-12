interface Device {
  id: number
  name: string
  ip_address: string | null
  mac_address: string | null
  manufacturer: string | null
  os_info: string | null
  device_type: string | null
  nmap_raw: string | null
  ping_type: string
  interval_seconds: number
  packet_size: number
  retention_days: number
  monitoring_enabled: boolean
  status: string
  last_seen_at: number | null
  created_at: number
  updated_at: number
  stats_6h?: number | null
  stats_12h?: number | null
  stats_24h?: number | null
  stats_48h?: number | null
}

export function useDevices() {
  const devices = useState<Device[]>('devices', () => [])
  const loading = useState('devicesLoading', () => false)
  const api = useApi()

  async function fetchDevices() {
    loading.value = true
    try {
      devices.value = await api.get<Device[]>('/devices')
    } catch (e) {
      console.error('Failed to fetch devices:', e)
    } finally {
      loading.value = false
    }
  }

  async function toggleMonitoring(id: number) {
    try {
      const updated = await api.post<Device>(`/devices/${id}/toggle`)
      const idx = devices.value.findIndex(d => d.id === id)
      if (idx >= 0) devices.value[idx] = updated
    } catch (e) {
      console.error('Failed to toggle monitoring:', e)
    }
  }

  async function deleteDevice(id: number) {
    try {
      await api.del(`/devices/${id}`)
      devices.value = devices.value.filter(d => d.id !== id)
    } catch (e) {
      console.error('Failed to delete device:', e)
    }
  }

  return { devices, loading, fetchDevices, toggleMonitoring, deleteDevice }
}
