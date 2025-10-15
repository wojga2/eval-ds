#!/bin/bash
# Monitor evaluation and automatically start analysis when complete

set -e

LOG_FILE="$1"
PROJECT_NAME="$2"

if [ -z "$LOG_FILE" ] || [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <log_file> <project_name>"
    exit 1
fi

echo "🔍 Monitoring evaluation progress..."
echo "Log file: $LOG_FILE"
echo "Project name: $PROJECT_NAME"
echo ""

# Wait for completion
while true; do
    if grep -q "✅ SUCCESS" "$LOG_FILE" 2>/dev/null; then
        echo "✅ Evaluation complete!"
        break
    elif grep -q "task(s) failed" "$LOG_FILE" 2>/dev/null && ! grep -q "Completed.*task run" "$LOG_FILE" 2>/dev/null; then
        echo "⚠️ Evaluation may have failed"
        break
    fi
    
    # Show progress every 5 minutes
    sleep 300
    echo "$(date): Still running..."
    
    # Check if process is still alive
    if ! pgrep -f "tau2bench_telecom_full_cmd_reasoning" > /dev/null; then
        echo "⚠️ Process may have ended"
        break
    fi
done

# Extract run ID
RUN_ID=$(grep -oP "bee run on co/bee/run.*id=\K[a-f0-9-]+" "$LOG_FILE" | tail -1)

if [ -z "$RUN_ID" ]; then
    echo "❌ Could not find run ID"
    exit 1
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║      EVALUATION COMPLETE - STARTING FAILURE ANALYSIS                     ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Run ID: $RUN_ID"
echo ""

# Download results
echo "📥 Step 1: Downloading results..."
cd /home/wojciech_cohere_com/dev/eval-ds
uv run download-bee-run --run-id "$RUN_ID"

# Find downloaded file
DOWNLOADED_FILE=$(ls -t output/bee_run_${RUN_ID:0:8}_*.jsonl 2>/dev/null | head -1)

if [ -z "$DOWNLOADED_FILE" ]; then
    echo "❌ Could not find downloaded file"
    exit 1
fi

echo "✅ Downloaded: $DOWNLOADED_FILE"
echo ""

# Count samples
NUM_SAMPLES=$(wc -l < "$DOWNLOADED_FILE")
echo "Total samples: $NUM_SAMPLES"
echo ""

# Run open coding
echo "🔬 Step 2: Running open coding ($NUM_SAMPLES samples)..."
cd failure_analysis/cli
source ../../.env

uv run python3 open_coder.py \
  --input "../../$DOWNLOADED_FILE" \
  --project "$PROJECT_NAME" \
  --num-samples "$NUM_SAMPLES" \
  --max-concurrent 30

OPEN_CODED_FILE=$(ls -t ../outputs/$PROJECT_NAME/open_coded_*.jsonl 2>/dev/null | head -1)

if [ -z "$OPEN_CODED_FILE" ]; then
    echo "❌ Open coding failed"
    exit 1
fi

echo "✅ Open coding complete: $OPEN_CODED_FILE"
echo ""

# Run axial coding
echo "🔬 Step 3: Running axial coding..."
uv run python3 axial_coder.py \
  --input "$OPEN_CODED_FILE" \
  --project "$PROJECT_NAME"

echo ""
echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║                 🎉 PIPELINE COMPLETE! 🎉                                 ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Results: failure_analysis/outputs/$PROJECT_NAME/"
echo ""

