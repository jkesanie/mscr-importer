#!/bin/bash

# Test CLI Script for MSCR Importer
# Run tests against the CLI with sample files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local command="$2"
    local expect_success="$3"
    
    echo -e "${YELLOW}Testing: $test_name${NC}"
    echo "Command: $command"
    
    if eval "$command" > /tmp/test_output.txt 2>&1; then
        if [ "$expect_success" = "true" ]; then
            echo -e "${GREEN}✓ PASS${NC}"
            ((PASSED++))
        else
            echo -e "${RED}✗ FAIL (expected failure, got success)${NC}"
            cat /tmp/test_output.txt
            ((FAILED++))
        fi
    else
        if [ "$expect_success" = "false" ]; then
            echo -e "${GREEN}✓ PASS (expected failure)${NC}"
            ((PASSED++))
        else
            echo -e "${RED}✗ FAIL${NC}"
            cat /tmp/test_output.txt
            ((FAILED++))
        fi
    fi
    echo ""
}

echo "========================================"
echo "MSCR Importer CLI Tests"
echo "========================================"
echo ""

# Test 1: Validate valid minimal YAML
run_test "Validate minimal YAML" \
    "poetry run python mscr_importer.py validate test_samples/valid_minimal.yaml --verbose" \
    "true"

# Test 2: Validate valid full YAML
run_test "Validate full YAML" \
    "poetry run python mscr_importer.py validate test_samples/valid_full.yaml --verbose" \
    "true"

# Test 3: Validate all valid samples
for file in test_samples/valid_*.yaml; do
    run_test "Validate $(basename $file)" \
        "poetry run python mscr_importer.py validate $file" \
        "true"
done

# Test 4: Validate invalid empty YAML
run_test "Validate invalid empty YAML" \
    "poetry run python mscr_importer.py validate test_samples/invalid_empty.yaml" \
    "false"

# Test 5: Validate invalid missing type
run_test "Validate invalid missing type" \
    "poetry run python mscr_importer.py validate test_samples/invalid_missing_type.yaml" \
    "false"

# Test 6: Validate invalid extra fields
run_test "Validate invalid extra fields" \
    "poetry run python mscr_importer.py validate test_samples/invalid_extra_fields.yaml" \
    "false"

# Test 7: Harvest with dry-run (minimal)
run_test "Harvest dry-run minimal" \
    "poetry run python mscr_importer.py harvest test_samples/valid_minimal.yaml --dry-run --verbose" \
    "true"

# Test 8: Harvest with dry-run (full)
run_test "Harvest dry-run full" \
    "poetry run python mscr_importer.py harvest test_samples/valid_full.yaml --dry-run --verbose" \
    "true"

# Test 9: Ingest with dry-run
run_test "Ingest dry-run" \
    "poetry run python mscr_importer.py ingest test_samples/valid_minimal.yaml --dry-run --verbose" \
    "true"

# Test 10: Test file:// URL handling
run_test "Harvest file URL dry-run" \
    "poetry run python mscr_importer.py harvest test_samples/valid_file_content.yaml --dry-run --verbose" \
    "true"

# Test 11: Test different type mappings
for type_file in test_samples/valid_sssom.yaml test_samples/valid_r2rml.yaml test_samples/valid_xslt.yaml test_samples/valid_sparql.yaml test_samples/valid_other_type.yaml; do
    run_test "Harvest dry-run $(basename $type_file)" \
        "poetry run python mscr_importer.py harvest $type_file --dry-run" \
        "true"
done

# Test 12: Test with visibility override
run_test "Harvest with visibility override" \
    "poetry run python mscr_importer.py harvest test_samples/valid_minimal.yaml --dry-run --visibility RESTRICTED" \
    "true"

# Test 13: Test with state override
run_test "Harvest with state override" \
    "poetry run python mscr_importer.py harvest test_samples/valid_minimal.yaml --dry-run --state PUBLISHED" \
    "true"

# Test 14: Test with action override
run_test "Harvest with action override" \
    "poetry run python mscr_importer.py harvest test_samples/valid_minimal.yaml --dry-run --action update" \
    "true"

echo "========================================"
echo "Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi