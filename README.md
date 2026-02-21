# Network Testing

A Flask + Svelte 5 application for running pre/post change validation tests against network devices. Upload a YAML file that defines your device inventory and the tests to run, execute the tests before and after a change, and compare the output with a built-in diff viewer.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (Svelte 5 + Tailwind)                              │
│  ┌──────────────┐  ┌──────────────────────────────────────┐ │
│  │   Sidebar    │  │  Run Panel           Diff Panel      │ │
│  │  · Devices   │  │  Pre / Run / Post    Pre vs Post     │ │
│  │  · Tests     │  │  Console output      Unified / Split │ │
│  └──────────────┘  └──────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / SSE  (proxied via Vite in dev)
┌──────────────────────────▼──────────────────────────────────┐
│  Flask API  :5000                                           │
│  POST /api/upload   — parse uploaded YAML                   │
│  POST /api/run      — stream test results (SSE)             │
│  GET  /api/diff     — compare pre/post snapshots            │
│  GET  /api/snapshots — list snapshot timestamps             │
└──────┬──────────────────────────────────────────────────────┘
       │ SSH :22 (Netmiko)         │ subprocess
  ┌────▼─────┐  ┌──────────┐      ▼
  │  Router  │  │ Switch   │  ping 8.8.8.8
  └──────────┘  └──────────┘  (host pings)
```

### Workflow

1. **Upload** your `testing.yaml` file via the browser.
2. Choose a **mode**:
   - **Pre-Check** — runs all enabled tests and saves a `pre` snapshot.
   - **Post-Check** — runs all enabled tests and saves a `post` snapshot.
   - **Run Now** — runs tests without saving a snapshot (useful for one-off checks).
3. Make your network change.
4. Run a **Post-Check**.
5. Open the **View Diff** panel to compare pre and post output side-by-side or as a unified diff.

### Test Types

| Type | How it runs | Identified by |
|---|---|---|
| **Command** | SSH into each device (Netmiko), sends the CLI command, captures output | `command:` key in YAML |
| **Ping** | Runs `ping` from the server host via subprocess | `type: ping` in YAML |

Ping results are stored under a `HOST` pseudo-device in snapshots so they appear in the diff panel alongside device command output.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 + |
| Node.js | 18 + |
| npm | 9 + |
| Network reachability | SSH port 22 open from the server to all devices |

---

## Setup

### 1 — Clone / download the project

```
network-testing/
├── backend/
│   ├── app.py
│   ├── network_handler.py
│   ├── ping_handler.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.svelte
│   │   ├── lib/api.js
│   │   └── components/
│   │       ├── Sidebar.svelte
│   │       ├── RunPanel.svelte
│   │       ├── ConsoleOutput.svelte
│   │       └── DiffPanel.svelte
│   ├── package.json
│   └── vite.config.js
└── testing.yaml          ← example config
```

### 2 — Set environment variables

Credentials are **never** stored in the YAML file. Set these on the machine running the Flask server before starting the backend:

```bash
# Required
export NET_USERNAME=admin
export NET_PASSWORD=your_ssh_password

# Optional — only needed if devices require enable/privilege mode
export NET_SECRET=your_enable_password
```

On Windows:

```powershell
$env:NET_USERNAME = "admin"
$env:NET_PASSWORD = "your_ssh_password"
$env:NET_SECRET   = "your_enable_password"
```

### 3 — Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4 — Install frontend dependencies

```bash
cd frontend
npm install
```

---

## Running the Application

Open two terminals.

**Terminal 1 — Backend**

```bash
cd backend
python app.py
```

Flask starts on `http://localhost:5000`.

**Terminal 2 — Frontend (development)**

```bash
cd frontend
npm run dev
```

Vite starts on `http://localhost:5173` and proxies all `/api` requests to Flask automatically.

Open **http://localhost:5173** in your browser.

### Production build

```bash
cd frontend
npm run build        # output goes to frontend/dist/
```

Serve `frontend/dist/` with any static file server, or configure Flask to serve it directly.

---

## YAML Configuration

Upload any file with a `.yaml` or `.yml` extension. The root must contain two keys: `inventory` and `tests`.

### Inventory

Each device entry requires only a name (used as the SSH hostname or IP) and a Netmiko device type. Credentials and port come from environment variables and are always port 22.

```yaml
inventory:
  - name: R1                  # hostname or IP — used as the SSH target
    device_type: cisco_ios

  - name: 10.0.0.2            # IP addresses work too
    device_type: cisco_nxos

  - name: core-sw.lab.local
    device_type: arista_eos
```

### Command Tests

```yaml
tests:
  - name: Show Version
    command: show version
    enabled: true

  - name: Show IP Interface Brief
    command: show ip interface brief
    enabled: true

  - name: Show BGP Summary
    command: show bgp summary
    enabled: false            # false = skipped, not shown in sidebar
```

### Ping Tests

Ping tests run from the **server host** (not from the network devices). Results are captured per destination and included in pre/post snapshots.

```yaml
tests:
  - name: Reachability Check
    type: ping
    destinations:
      - 8.8.8.8
      - 1.1.1.1
      - 192.168.1.254
    count: 4                  # optional, defaults to 4
    enabled: true
```

### Complete Example

```yaml
inventory:
  - name: R1
    device_type: cisco_ios

  - name: R2
    device_type: cisco_ios

  - name: SW1
    device_type: cisco_ios

tests:
  - name: Reachability Check
    type: ping
    destinations:
      - 8.8.8.8
      - 1.1.1.1
    count: 4
    enabled: true

  - name: Show Version
    command: show version
    enabled: true

  - name: Show IP Interface Brief
    command: show ip interface brief
    enabled: true

  - name: Show IP Route
    command: show ip route
    enabled: true

  - name: Show ARP
    command: show arp
    enabled: true

  - name: Show BGP Summary
    command: show bgp summary
    enabled: false
```

---

## Supported Device Types

Any device type supported by [Netmiko](https://github.com/ktbyers/netmiko) can be used in the `device_type` field. Common values:

| Platform | `device_type` |
|---|---|
| Cisco IOS / IOS-XE | `cisco_ios` |
| Cisco IOS-XR | `cisco_xr` |
| Cisco NX-OS | `cisco_nxos` |
| Arista EOS | `arista_eos` |
| Juniper JunOS | `juniper_junos` |
| Palo Alto PAN-OS | `paloalto_panos` |
| Fortinet FortiOS | `fortinet` |
| HP / Aruba ProCurve | `hp_procurve` |

See the full list at https://github.com/ktbyers/netmiko/blob/develop/PLATFORMS.md

---

## UI Overview

### Sidebar (read-only after upload)

- Lists every device from the inventory.
- Lists only **enabled** tests.
  - Cyan dot — command test; shows the CLI command below the name.
  - Violet dot — ping test; lists each destination IP/hostname.
- **Load New File** button at the bottom re-opens the file picker without a page reload.

### Run Panel

| Control | Description |
|---|---|
| **Pre-Check** | Runs tests and saves output as the `pre` snapshot |
| **Run Now** | Runs tests, no snapshot saved |
| **Post-Check** | Runs tests and saves output as the `post` snapshot |
| **Execute** | Starts the selected mode |
| Snapshot row | Shows timestamps for saved pre/post snapshots; click ✕ to delete |

Output streams into the console as each command completes — no waiting for all devices to finish. The **Copy** button in the console toolbar copies the full plain-text output to the clipboard.

### Diff Panel

- Left list: all test results grouped by device; colour-coded (amber = changed, green = unchanged).
- **Changed only** toggle hides unchanged results.
- **Unified** view: classic `+`/`-` diff with syntax highlighting.
- **Split** view: pre output on the left, post output on the right.
- **Copy** button copies the diff or raw output for the selected result.

---

## Snapshots

Pre and post snapshots are saved as JSON files in `backend/snapshots/`:

```
backend/snapshots/
├── pre.json
└── post.json
```

Each file contains a timestamp and the full command output for every device and test. Delete them with the ✕ buttons in the UI, or delete the files manually to start fresh.

---

## Troubleshooting

| Problem | Likely cause |
|---|---|
| `Authentication failed` | `NET_USERNAME` or `NET_PASSWORD` is wrong or not set |
| `Connection timed out` | Device unreachable on port 22; check firewall / routing |
| `No devices in inventory for command tests` | Inventory section is empty in your YAML |
| `No tests are enabled` | All tests have `enabled: false` |
| `YAML parse error` | Indentation or syntax issue in the YAML file |
| Upload rejected | File extension must be `.yaml` or `.yml` |
| Diff panel shows "Missing snapshots" | Run a Pre-Check and a Post-Check first |
