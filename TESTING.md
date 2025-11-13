# 🧪 Testing Guide - SPAMURAI Contact Allocator

Comprehensive testing documentation for the Contact Allocator project.

## 📋 Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Fixtures](#test-fixtures)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [Continuous Integration](#continuous-integration)

---

## Overview

The test suite provides comprehensive coverage of all Contact Allocator functionality:

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test end-to-end workflows and CLI
- **Fixtures**: Reusable test data files covering various scenarios

### Test Statistics

- **Total Test Cases**: 40+
- **Test Fixtures**: 10 Excel files covering different scenarios
- **Coverage Goal**: >90% code coverage

---

## Quick Start

### 1. Install Test Dependencies

```bash
cd spamurai-strike-map
pip install -r requirements.txt
```

This installs:
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting

### 2. Generate Test Fixtures

```bash
python3 tests/create_test_fixtures.py
```

This creates 10 Excel files in `tests/fixtures/` with various test scenarios.

### 3. Run All Tests

```bash
pytest
```

Or with verbose output:

```bash
pytest -v
```

---

## Test Structure

```
tests/
├── __init__.py
├── create_test_fixtures.py       # Script to generate test data
├── test_contact_allocator.py     # Unit tests for ContactAllocator
├── test_integration.py            # End-to-end integration tests
├── test_google_sheets_client.py  # Tests for GoogleSheetsClient
└── fixtures/                      # Test data files (auto-generated)
    ├── basic_allocation.xlsx
    ├── center_based_allocation.xlsx
    ├── duplicates_allocation.xlsx
    ├── unallocated_contacts.xlsx
    ├── invalid_contacts_centers.xlsx
    ├── invalid_spamurais_centers.xlsx
    ├── existing_allocation.xlsx
    ├── incremental_new_contacts.xlsx
    ├── large_scale_allocation.xlsx
    └── edge_cases.xlsx
```

### Test Files

#### `test_contact_allocator.py`
Unit tests for core allocation logic:
- Basic allocation without centers
- Center-based matching
- Priority ordering
- Round-robin distribution
- Deduplication (input, incremental, per-tab)
- Incremental mode
- Edge cases
- Validation errors

#### `test_integration.py`
End-to-end integration tests:
- CLI interface
- Full allocation workflows
- Excel output verification
- Data integrity checks
- Performance tests

#### `test_google_sheets_client.py`
Tests for Google Sheets utility:
- Spreadsheet ID extraction
- Excel file reading
- Data formatting
- Error handling

---

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_contact_allocator.py
```

### Run Specific Test Class

```bash
pytest tests/test_contact_allocator.py::TestBasicAllocation
```

### Run Specific Test

```bash
pytest tests/test_contact_allocator.py::TestBasicAllocation::test_basic_allocation
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

Then open `htmlcov/index.html` in a browser.

### Run Only Fast Tests (skip slow)

```bash
pytest -m "not slow"
```

### Run with Output Capture Disabled

```bash
pytest -s
```

Useful for debugging when you want to see print statements.

---

## Test Fixtures

Test fixtures are pre-created Excel files that cover different scenarios. They are located in `tests/fixtures/`.

### Available Fixtures

#### 1. `basic_allocation.xlsx`
- **Purpose**: Basic allocation without centers
- **Contacts**: 6 contacts
- **Spamurais**: 2 (Rahul, Priya)
- **Centers**: None
- **Use Case**: Test basic round-robin allocation and priority ordering

#### 2. `center_based_allocation.xlsx`
- **Purpose**: Center-based matching
- **Contacts**: 8 contacts (Mumbai, Delhi, Bangalore)
- **Spamurais**: 3 (Rahul-Mumbai, Priya-Delhi, Arjun-Mumbai)
- **Use Case**: Test center matching and allocation to correct Spamurais

#### 3. `duplicates_allocation.xlsx`
- **Purpose**: Duplicate phone number handling
- **Contacts**: 5 contacts with 2 duplicates
- **Use Case**: Test deduplication keeps first occurrence

#### 4. `unallocated_contacts.xlsx`
- **Purpose**: Contacts with no matching center
- **Contacts**: 4 contacts, 1 with Bangalore center (no Bangalore Spamurai)
- **Use Case**: Test unallocated contacts handling

#### 5. `invalid_contacts_centers.xlsx`
- **Purpose**: Validation error - mixed centers in contacts
- **Use Case**: Test validation fails when some contacts have centers, some don't

#### 6. `invalid_spamurais_centers.xlsx`
- **Purpose**: Validation error - mixed centers in Spamurais
- **Use Case**: Test validation fails when some Spamurais have centers, some don't

#### 7. `existing_allocation.xlsx`
- **Purpose**: Existing allocation for incremental mode
- **Contacts**: 3 contacts already allocated
- **Use Case**: Test incremental mode loads existing allocations

#### 8. `incremental_new_contacts.xlsx`
- **Purpose**: New contacts for incremental mode
- **Contacts**: 5 contacts (3 old + 2 new)
- **Use Case**: Test incremental mode filters already-allocated contacts

#### 9. `large_scale_allocation.xlsx`
- **Purpose**: Performance testing
- **Contacts**: 100 contacts
- **Spamurais**: 5
- **Use Case**: Test performance with larger datasets

#### 10. `edge_cases.xlsx`
- **Purpose**: Edge cases and special characters
- **Contacts**: Names with emojis, apostrophes, missing sources
- **Use Case**: Test robustness with unusual data

### Regenerating Fixtures

If you need to recreate fixtures (e.g., after changing test data):

```bash
python3 tests/create_test_fixtures.py
```

This will overwrite existing fixtures.

---

## Test Coverage

### Current Coverage

Run coverage report:

```bash
pytest --cov=src --cov-report=term-missing
```

### Coverage Goals

- **Overall**: >90%
- **Core Allocation Logic**: 100%
- **CLI**: >85%
- **Utilities**: >80%

### Viewing Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

---

## Writing New Tests

### Test Template

```python
import pytest
import os
from contact_allocator import ContactAllocator

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

@pytest.fixture
def logger():
    import logging
    return logging.getLogger('test')

def test_my_new_feature(logger):
    """Test description"""
    fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

    allocator = ContactAllocator(fixture, logger)
    allocator.load_data()
    allocator.validate_data()
    allocator.preprocess_data()
    result = allocator.allocate()

    # Assertions
    assert result is not None
    assert len(result['spamurai_allocations']) > 0
```

### Best Practices

1. **Use Descriptive Names**: Test names should describe what they're testing
   ```python
   # Good
   def test_center_matching_allocates_to_correct_spamurai(self):

   # Bad
   def test_centers(self):
   ```

2. **One Assertion Focus**: Each test should focus on one behavior
   ```python
   # Good - tests one thing
   def test_duplicates_are_removed(self):
       assert len(allocator.contacts) == 3

   # Less ideal - tests multiple things
   def test_everything(self):
       assert len(allocator.contacts) == 3
       assert allocator.spamurais[0]['name'] == 'Rahul'
       assert result['summary']['total'] == 10
   ```

3. **Use Fixtures**: Reuse test data via fixtures
   ```python
   @pytest.fixture
   def allocated_result(logger):
       allocator = ContactAllocator(fixture, logger)
       allocator.load_data()
       allocator.validate_data()
       allocator.preprocess_data()
       return allocator.allocate()

   def test_allocation_count(allocated_result):
       assert len(allocated_result['spamurai_allocations']) == 2
   ```

4. **Clean Up**: Remove temporary files created during tests
   ```python
   def test_with_temp_file():
       temp_file = 'temp_output.xlsx'
       try:
           # Test code
           pass
       finally:
           if os.path.exists(temp_file):
               os.remove(temp_file)
   ```

### Creating New Fixtures

If you need a new test scenario:

1. Add a function to `tests/create_test_fixtures.py`:

```python
def create_my_new_fixture():
    """Description of test scenario"""
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob'],
        'Phone Number': ['1111111111', '2222222222'],
        'Center': ['Mumbai', 'Mumbai'],
        'Source of Interest': ['Workshop', 'Workshop']
    })

    spamurais = pd.DataFrame({
        'Name': ['Rahul'],
        'Center': ['Mumbai']
    })

    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop'],
        'Priority': [1]
    })

    filepath = os.path.join(FIXTURES_DIR, 'my_new_fixture.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")
```

2. Add the function call in `__main__`:

```python
if __name__ == '__main__':
    # ... existing fixtures
    create_my_new_fixture()
```

3. Regenerate fixtures:

```bash
python3 tests/create_test_fixtures.py
```

---

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Generate test fixtures
      run: |
        python3 tests/create_test_fixtures.py

    - name: Run tests
      run: |
        pytest --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "Running tests before commit..."
pytest

if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi

echo "All tests passed!"
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

---

## Troubleshooting

### Tests Fail with "Fixtures not found"

**Solution**: Generate fixtures first:
```bash
python3 tests/create_test_fixtures.py
```

### Import Errors

**Solution**: Make sure you're running from the project root:
```bash
cd spamurai-strike-map
pytest
```

### Coverage Command Not Found

**Solution**: Install pytest-cov:
```bash
pip install pytest-cov
```

### Tests Hang During Incremental Mode

**Solution**: Some integration tests that require user input are skipped. If running manually, provide input when prompted.

### Permission Errors on Windows

**Solution**: Close Excel files before running tests. Windows locks Excel files when they're open.

---

## Test Maintenance

### Regular Tasks

1. **Run tests before commits**:
   ```bash
   pytest
   ```

2. **Check coverage weekly**:
   ```bash
   pytest --cov=src --cov-report=html
   ```

3. **Update fixtures when data format changes**:
   - Modify `create_test_fixtures.py`
   - Regenerate: `python3 tests/create_test_fixtures.py`

4. **Add tests for new features**:
   - Write test first (TDD approach)
   - Implement feature
   - Ensure tests pass

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**Happy Testing! 🎯**
