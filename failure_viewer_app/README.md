# Failure Viewer App

A web application for exploring tau2bench failure mode analysis results.

## Overview

This self-contained web app provides an interactive interface to:
- Browse analysis projects
- Filter tasks by axial codes and pass/fail status
- View detailed task information including conversations, eval metrics, and analysis
- Explore open coding and axial coding results
- Review recommendations for improvement

## Architecture

### Backend (Python + FastAPI)
- **Port**: 9000
- **Location**: `backend/`
- **Key files**:
  - `main.py` - Application entry point
  - `routes.py` - API endpoints
  - `models.py` - Data models
  - `config.py` - App configuration

### Frontend (React + TypeScript + Vite)
- **Port**: 9001
- **Location**: `frontend/`
- **Tech stack**:
  - React 18
  - TypeScript
  - Vite (build tool)
  - Tailwind CSS (styling)
  - shadcn/ui components

### Logs
- **Location**: `logs/`
- `backend.log` - Backend API logs
- `frontend.log` - Frontend build/serve logs

## Quick Start

### Prerequisites
- Node.js v18 or higher
- Python 3.10 or higher
- `uv` (Python dependency manager)

### Starting the App

```bash
# Start all services (backend + frontend)
./failure-viewer-app-control.sh start

# Check status
./failure-viewer-app-control.sh status

# Stop all services
./failure-viewer-app-control.sh stop

# Restart services
./failure-viewer-app-control.sh restart

# View logs
./failure-viewer-app-control.sh logs
```

### Accessing the App

Once started, the app is accessible via:

**Tailscale (external access)**:
- The control script will display your Tailscale IP address
- Access format: `http://<tailscale-ip>:9001`

**Local access**:
- **Frontend**: http://localhost:9001
- **Backend API**: http://localhost:9000
- **API Docs**: http://localhost:9000/docs

The frontend binds to `0.0.0.0` making it accessible from any network interface.

## Features

### 1. Project Selection
- View all available analysis projects
- See summary statistics (total samples, success/fail counts)
- Quick overview of unique axial codes per project

### 2. Task Filtering
- **Pass/Fail Filter**: Show all, only passing, or only failing tasks
- **Axial Code Filter**: 
  - Typeahead search for codes
  - Select multiple codes
  - Tag-based display with easy removal
  - Real-time task count updates

### 3. Task List
- Compact view of filtered tasks
- Shows:
  - Sample ID (truncated)
  - Descriptive summary
  - Pass/fail status badge
  - Primary axial code
  - Severity level
  - Reward score

### 4. Task Detail View
Displays comprehensive information for selected tasks:

#### Evaluation Metrics
- Pass/fail status
- Reward scores
- Tau2bench checks (same format as bee_sample_viewer Reward tab)

#### Conversation
- Full conversation with all turns
- Tool calls with arguments displayed
- Tool results formatted
- Thinking content (when available)
- Failure point highlighted (if turn-specific)

#### Turn-Specific Analysis
When analysis pertains to a specific turn:
- Highlighted in the conversation
- Issues displayed next to the turn
- Clear visual indication

#### Conversation-Level Analysis
When analysis pertains to the whole conversation:
- Displayed in separate section below conversation
- Includes:
  - Summary
  - Detailed analysis
  - Issues identified
  - Observations

#### Axial Coding
- Primary code
- Secondary codes
- Severity level
- Rationale

#### Recommendations
- Actionable improvement suggestions
- Displayed in dedicated section

## Data Source

The app loads data from:
```
../failure_analysis/outputs/
```

Expected structure:
```
failure_analysis/outputs/
└── project_name/
    ├── original_bee_run_*.jsonl
    ├── open_coded_*.jsonl
    └── axial_coded_*.jsonl  # Main data source
```

## API Endpoints

### `GET /api/projects`
List all available projects

### `GET /api/projects/{project_name}`
Load all samples from a project

### `POST /api/projects/{project_name}/filter`
Filter tasks by criteria
- Body: `{ "axial_codes": [], "pass_fail": null }`

### `GET /api/projects/{project_name}/samples/{sample_id}`
Get a specific sample by ID

### `GET /api/health`
Health check endpoint

## Development

### Backend Development
```bash
cd backend
uv run python main.py
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Logs for Debugging
All logs are written to `logs/` directory:
- Check `backend.log` for API errors
- Check `frontend.log` for build/runtime errors
- Logs include timestamps and log levels for easy debugging

## Troubleshooting

### Ports Already in Use
If ports 9000 or 9001 are in use:
1. Check running processes: `./failure-viewer-app-control.sh status`
2. Stop the app: `./failure-viewer-app-control.sh stop`
3. Or manually: `lsof -ti:9000 | xargs kill` (and 9001)

### Backend Not Starting
Check `logs/backend.log` for errors:
```bash
tail -f logs/backend.log
```

### Frontend Not Starting
Check `logs/frontend.log` for errors:
```bash
tail -f logs/frontend.log
```

### No Projects Showing
Ensure you have run the failure analysis pipeline:
```bash
cd failure_analysis/cli
uv run python open_coder.py --input <input> --project <name>
uv run python axial_coder.py --input <input> --project <name>
```

## Version

v1.0.0 - Initial release

