#!/usr/bin/env bash
#
# Run stress tests for hadiscover
# 
# Usage:
#   ./run_stress_tests.sh              # Run all levels
#   ./run_stress_tests.sh level1       # Run only level 1
#   ./run_stress_tests.sh level2       # Run only level 2
#   ./run_stress_tests.sh level3       # Run only level 3
#

set -e

cd "$(dirname "$0")/backend"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Determine which tests to run
case "${1:-all}" in
    level1)
        echo "Running Level 1 (Light) stress test..."
        pytest tests/stress/test_stress.py::test_stress_level_1_light -v -s
        ;;
    level2)
        echo "Running Level 2 (Medium) stress test..."
        pytest tests/stress/test_stress.py::test_stress_level_2_medium -v -s
        ;;
    level3)
        echo "Running Level 3 (Heavy) stress test..."
        pytest tests/stress/test_stress.py::test_stress_level_3_heavy -v -s
        ;;
    all)
        echo "Running all stress tests..."
        echo ""
        echo "This will run 3 levels of stress tests:"
        echo "  - Level 1: 100 repos, 1000 automations"
        echo "  - Level 2: 500 repos, 5000 automations"
        echo "  - Level 3: 2000 repos, 20000 automations"
        echo ""
        echo "This may take several minutes to complete."
        echo ""
        pytest tests/stress/test_stress.py -v -s
        ;;
    *)
        echo "Usage: $0 [level1|level2|level3|all]"
        exit 1
        ;;
esac

echo ""
echo "Stress tests completed!"
echo ""
echo "For more details, see the performance reports above."
