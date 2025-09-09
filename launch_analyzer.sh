#!/bin/bash

# Sample Analyzer Launch Script
# Modern Python tooling with uv for dependency management

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Sample Analyzer${NC}"
echo "======================================"

# Check if we're in the right directory
if [[ ! -f "sample_analyzer.py" ]]; then
    echo -e "${RED}Error: sample_analyzer.py not found. Please run from the eval-ds directory.${NC}"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: uv is not installed. Please install it first:${NC}"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check if CSV files exist
if [[ ! -d "output" ]] || [[ ! $(find output -name "*_samples_*.csv" -type f) ]]; then
    echo -e "${RED}Error: No sample CSV files found in output/ directory.${NC}"
    echo "Please ensure you have run the eval and have CSV files like 'bee_run_samples_*.csv'"
    exit 1
fi

# Launch the analyzer using uv
echo -e "${GREEN}✨ Launching Sample Analyzer...${NC}"
echo -e "${BLUE}The analyzer will open in your default browser.${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server when done.${NC}"
echo ""

# Run streamlit with uv, specifying dependencies inline
uv run --with streamlit --with pandas streamlit run sample_analyzer.py --server.address 0.0.0.0 --server.port 8501
