# Failure Viewer App - Quick Start

## Start/Stop Commands

```bash
# Start the app
./failure-viewer-app-control.sh start

# Check status
./failure-viewer-app-control.sh status

# Stop the app
./failure-viewer-app-control.sh stop

# Restart the app
./failure-viewer-app-control.sh restart

# View live logs
./failure-viewer-app-control.sh logs
```

## Access URLs

**Tailscale (external access)**:
- The app displays your Tailscale IP on startup
- Frontend: `http://<tailscale-ip>:9001`
- Backend: `http://<tailscale-ip>:9000`

**Local access**:
- **Web App**: http://localhost:9001
- **Backend API**: http://localhost:9000
- **API Docs**: http://localhost:9000/docs

The frontend binds to `0.0.0.0` for external accessibility.

## How to Use

### 1. Select a Project
When you first open the app, you'll see all available analysis projects. Click on any project card to load it.

### 2. Filter Tasks
Once a project is loaded, use the filter bar at the top to:
- **Pass/Fail**: Click "All", "Pass", or "Fail" to filter by task status
- **Axial Codes**: 
  - Type in the search box to find codes
  - Click on a code to add it as a filter
  - Multiple codes can be selected
  - Click the X on any tag to remove it
  - Click "Clear all" to remove all code filters

The task count updates in real-time as you apply filters.

### 3. Browse Tasks
The left panel shows a compact list of all tasks matching your filters. Each task shows:
- Sample ID
- Summary
- Pass/Fail badge
- Primary code
- Severity
- Reward score

Click on any task to view its details.

### 4. View Task Details
The right panel shows comprehensive information for the selected task:

**Evaluation Metrics**: Status, reward scores, and tau2bench checks

**Conversation**: 
- Full conversation with all turns
- Tool calls and results formatted for readability
- Thinking content when available
- Failure point highlighted (if applicable)

**Analysis**:
- Turn-specific issues shown next to the relevant turn
- Conversation-level analysis shown separately (if applicable)

**Axial Coding**: Primary code, secondary codes, severity, and rationale

**Recommendations**: Actionable suggestions for improvement

## Troubleshooting

### App Won't Start
Check the logs:
```bash
tail -f logs/backend.log
tail -f logs/frontend.log
```

### Port Already in Use
Stop any existing instances:
```bash
./failure-viewer-app-control.sh stop
```

### No Projects Showing
Make sure you've run the failure analysis pipeline:
```bash
cd ../failure_analysis/cli
uv run python open_coder.py --input <file> --project <name>
uv run python axial_coder.py --input <input> --project <name>
```

## Current Data

The app currently has access to:
- **Project**: cmd_reasoning_50
- **Samples**: 50 total (19 pass, 31 fail)
- **Unique Codes**: 10

## Tips

1. **Start broad**: Use pass/fail filter first, then narrow down with codes
2. **Compare tasks**: Select multiple codes to see tasks with similar issues
3. **Check logs**: If something seems off, backend logs have detailed debugging info
4. **Restart cleanly**: Use `restart` command instead of manually killing processes

## Development

To modify the app:
- **Backend**: Edit files in `backend/`, restart required
- **Frontend**: Edit files in `frontend/src/`, changes hot-reload automatically

## Support

For issues or questions, check:
1. `README.md` - Full documentation
2. `logs/*.log` - Detailed error logs
3. Backend API at http://localhost:9000/docs - Interactive API documentation

