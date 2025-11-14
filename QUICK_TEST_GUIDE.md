# 🚀 Quick Test Guide

## Run Tests

```bash
# Run all tests with health report
python3 -m pytest -v

# Run only passing tests
python3 -m pytest -v --lf

# Run with coverage
python3 -m pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Check Test Health

After running tests, you'll see a health summary like this:

```
========================= SPAMURAI Test Health Summary =========================

📊 Functionality Health:
--------------------------------------------------------------------------------
✅ HEALTHY  test_google_sheets_client/TestLocalExcelReading      4/4 (100.0%)
❌ BROKEN   test_contact_allocator/TestBasicAllocation           0/3 (  0.0%)
      ↳ test_basic_allocation
      ↳ test_priority_ordering
      ↳ test_excel_output

--------------------------------------------------------------------------------
Overall Health: ⚠️ FAIR - 35/48 tests passing (72.9%)

🔧 Broken Functionality:
   • test_contact_allocator/TestBasicAllocation (3 failures)

✅ Working Functionality:
   • test_google_sheets_client/TestLocalExcelReading (all 4 tests passing)
```

## View Detailed Report

```bash
cat TEST_HEALTH_REPORT.md
```

This shows:
- ✅ **What's Working** - All 35 passing tests categorized by functionality
- ❌ **What's Broken** - Detailed analysis of 13 failing tests
- 🎯 **Fix Priority** - Ranked list (P0-P3) with estimated effort
- 📋 **Root Causes** - Why each test is failing
- 🚀 **Quick Commands** - Diagnostic commands for debugging

## Current Status

**Overall Health**: ⚠️ FAIR (72.9%)

### ✅ Working (35 tests)
- Google Sheets Client (100%)
- Integration workflows (87%)
- Incremental mode (100%)
- Large scale performance (100%)

### ❌ Needs Fixing (13 tests)
1. **Round-robin distribution** - Allocates 4-2 instead of 3-3
2. **Data key mismatch** - Tests expect 'Phone Number', code returns 'phone'
3. **Dry-run behavior** - Creates file when it shouldn't
4. **Error messages** - Format mismatches in validation

## Dependencies for Integration Tests

No additional dependencies needed! The integration tests require:
- ✅ `pytest` (already installed)
- ✅ `pandas` (already installed)
- ✅ `openpyxl` (already installed)
- ✅ Test fixtures (already in repository)

All integration tests use local Excel files, so **no Google Sheets access required**.

## Troubleshooting

### "pytest: command not found"
**Solution**: Use `python3 -m pytest` instead of `pytest`

### Tests hanging or asking for input
**Cause**: Incremental mode tests that require user input
**Solution**: These specific tests are skipped automatically or pass without interaction

### Import errors
**Solution**: Make sure you're in the repository root:
```bash
cd /Users/santoshpawar/code/spamurai-strike-map
python3 -m pytest -v
```

## Next Steps

To get to 100% test health:

1. **Fix data key mismatch** (fixes 7 tests) - 2 hours
2. **Fix round-robin** (fixes 3 tests) - 1 hour
3. **Fix dry-run** (fixes 1 test) - 30 min
4. **Fix messages** (fixes 2 tests) - 30 min

**Total**: ~4 hours to 100% passing tests

See `TEST_HEALTH_REPORT.md` for detailed fix instructions.
