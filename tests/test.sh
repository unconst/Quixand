#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test configuration
RUNTIMES=("docker" "podman")
TEST_SCRIPTS=(
    "async_minimal.py"
    "file_operations.py"
    "minimal.py"
    "streaming.py"
    "resource_limits.py"
    "template_build.py"
)

# Function to print separator
print_separator() {
    echo -e "\n${BLUE}════════════════════════════════════════════════════════════════${NC}\n"
}

# Function to run a test
run_test() {
    local runtime=$1
    local script=$2
    
    echo -e "${YELLOW}[RUNNING]${NC} QS_RUNTIME=${runtime} python3 ./examples/${script}"
    QS_RUNTIME=${runtime} python3 ./examples/${script}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[SUCCESS]${NC} ${script} with ${runtime} runtime completed"
    else
        echo -e "${RED}[FAILED]${NC} ${script} with ${runtime} runtime failed"
    fi
}

# Main test execution
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Quixand Test Suite Execution                         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

# Run tests for each runtime
for runtime in "${RUNTIMES[@]}"; do
    print_separator
    echo -e "${GREEN}Testing with ${runtime^^} runtime${NC}"
    print_separator
    
    for script in "${TEST_SCRIPTS[@]}"; do
        run_test "$runtime" "$script"
        print_separator
    done
done

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                  All tests completed!                             ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}\n"