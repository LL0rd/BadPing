# BadPing - Project Guide

## Overview

Network monitoring tool with ICMP/ARP ping, device fingerprinting, and latency visualization. Python/FastAPI backend + Nuxt 3/Vue 3 frontend in a single Docker container.

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2 (async), aiosqlite, icmplib, scapy, python-nmap
- **Frontend**: Nuxt 3 (SPA mode), Vue 3, TypeScript, Tailwind CSS, ECharts (vue-echarts), Radix Vue, Lucide icons
- **Database**: SQLite with WAL mode, auto-created on startup
- **Deployment**: Docker (nginx + supervisord + uvicorn), single container

## Project Structure

```
backend/app/
  main.py              # FastAPI app, lifespan, CORS
  models.py            # SQLAlchemy: Device, PingResult, Notification
  schemas.py           # Pydantic request/response models
  database.py          # Async SQLite setup (WAL, pragmas)
  config.py            # Environment variable config
  routers/
    devices.py         # Device CRUD, check, discover, rescan
    stats.py           # Stats, graph data, CSV export, clear data
    notifications.py   # Notification list/read
  services/
    monitor_service.py # Main monitoring loop, batch writes, status detection
    ping_service.py    # ICMP ping via icmplib
    arp_service.py     # ARP ping/discovery via scapy, MAC vendor lookup
    nmap_service.py    # nmap basic_scan (-sn) and full nmap_scan (-O)
    notification_service.py
    cleanup_service.py # Data retention cleanup (hourly)

frontend/
  pages/
    index.vue          # Dashboard with device table
    device/[id].vue    # Device detail, chart, settings, clear data
  components/
    DeviceTable.vue    # Device list
    AddDeviceDialog.vue # Add device form (2-step)
    DiscoverDialog.vue  # ARP network discovery
    LatencyChart.vue    # ECharts with dual ICMP/ARP series
    DeviceInfo.vue      # Device details, OS guesses, device type tags
    StatsCards.vue      # Packet loss / latency stats
    StatusBadge.vue     # online/degraded/offline/unknown badge
    NotificationBanner.vue
    ThemeToggle.vue
    ui/                 # Radix Vue primitives
  composables/
    useApi.ts           # $fetch wrapper (methods: get, post, put, del)
    useDevices.ts       # Pinia device state
    useNotifications.ts
  nuxt.config.ts        # SPA mode, dev proxy /api -> :8000
  tailwind.config.ts    # Dark mode, HSL color variables
```

## Build & Run

### Docker (production)

```bash
docker compose up --build -d
# Access at http://localhost:8765
```

Requires: `cap_add: [NET_RAW, NET_ADMIN]` and `network_mode: host` for ARP.

### Development

```bash
# Backend
cd backend
pip install -r requirements.txt
BADPING_DB_PATH=./data/badping.db uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev   # http://localhost:3000, proxies /api to :8000
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `BADPING_DB_PATH` | `/data/badping.db` | SQLite database path |
| `BADPING_DEFAULT_INTERVAL` | `1.0` | Default ping interval (seconds) |
| `BADPING_DEFAULT_RETENTION_DAYS` | `14` | Default data retention |
| `BADPING_DEGRADED_LOSS_PCT` | `5.0` | Loss % threshold for degraded status |
| `BADPING_OFFLINE_LOSS_SECONDS` | `30` | Seconds of 100% loss before offline |
| `BADPING_BATCH_WRITE_INTERVAL` | `1.0` | DB batch write interval |
| `BADPING_CLEANUP_INTERVAL` | `3600` | Cleanup cycle (seconds) |

## API Endpoints

All prefixed with `/api`.

- `GET/POST /devices` — list / create
- `GET/PUT/DELETE /devices/{id}` — read / update / delete
- `POST /devices/{id}/toggle` — start/stop monitoring
- `POST /devices/{id}/rescan` — run nmap scan
- `POST /devices/check` — test connectivity
- `POST /devices/discover` — ARP network scan
- `GET /stats/{id}` — loss %, latency stats
- `GET /stats/{id}/graph?start=&end=` — time series (auto-bucketed by range)
- `DELETE /stats/{id}/data` — clear all ping data
- `GET /stats/{id}/export?start=&end=` — CSV download
- `GET/PUT /notifications` — list / mark read

## Key Patterns

- **Async everywhere**: FastAPI async endpoints, aiosqlite, scapy/nmap run in thread executors
- **Batch writes**: MonitorService buffers ping results, flushes to DB every 1s
- **Auto-bucketing**: Graph endpoint aggregates data (60s/10s/1s buckets) based on time range
- **Dual ping mode**: When `ping_type=both`, ICMP and ARP run concurrently per interval; graph data includes `ping_type` field, chart shows separate colored series
- **Fingerprint toggle**: `fingerprint_enabled` per device — disabled runs `nmap -sn` (basic), enabled runs `nmap -O --osscan-guess` (full). Manual rescan always runs full scan.
- **Manufacturer fallback**: nmap result → scapy OUI database (`mac_vendor_lookup`) if unknown
- **Legend persistence**: LatencyChart tracks `legendSelected` state via `@legendselectchanged` event to survive data refresh cycles
- **Status detection**: online → degraded (>5% loss in window) → offline (>30s consecutive loss) → recovery notification
- **No migrations**: `Base.metadata.create_all()` on startup; add new columns with `nullable=True` or defaults

## Database

SQLite with WAL mode. Tables: `devices`, `ping_results` (indexed on `device_id + timestamp`), `notifications`. No migration framework — schema changes require manual `ALTER TABLE` or DB recreation.

## Docker Build

Multi-stage: Node 20 builds frontend (`npm run generate`), Python 3.12-slim runs backend. Nginx reverse proxy on port 8765, uvicorn on internal port 8000. supervisord manages both processes.
