#!/bin/bash
# Convenience script to run tests with common options

set -e  # Exit on error

echo "=================================="
echo "🧪 SPAMURAI Contact Allocator Tests"
echo "=================================="
echo ""

# Check if fixtures exist
if [ ! -d "tests/fixtures" ] || [ -z "$(ls -A tests/fixtures 2>/dev/null)" ]; then
    echo "📦 Generating test fixtures..."
    python3 tests/create_test_fixtures.py
    echo ""
fi

# Parse arguments
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --test|-t)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage     Run with coverage report"
            echo "  -v, --verbose      Run with verbose output"
            echo "  -t, --test FILE    Run specific test file"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh --coverage         # Run with coverage"
            echo "  ./run_tests.sh --verbose          # Verbose output"
            echo "  ./run_tests.sh -t test_contact_allocator.py"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="python3 -m pytest"

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=src --cov-report=term-missing --cov-report=html"
fi

if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD tests/$SPECIFIC_TEST"
fi

# Run tests
echo "🚀 Running tests..."
echo "Command: $PYTEST_CMD"
echo ""

$PYTEST_CMD

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"

    if [ "$COVERAGE" = true ]; then
        echo ""
        echo "📊 Coverage report generated:"
        echo "   Open htmlcov/index.html to view detailed coverage"
    fi
else
    echo "❌ Some tests failed (exit code: $EXIT_CODE)"
fi

echo ""
echo "=================================="

exit $EXIT_CODE
