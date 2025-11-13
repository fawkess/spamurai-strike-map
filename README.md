# 🎯 SPAMURAI Strike Map

Automated contact distribution tool that allocates contacts to Spamurais based on center matching and source priorities.

## 📋 Overview

The Contact Allocator reads contact data from a Google Sheet and automatically distributes contacts to Spamurais using intelligent allocation rules:

- **Center Matching**: Matches contacts to Spamurais based on geographic center
- **Priority-Based Distribution**: Processes high-priority sources first
- **Round-Robin Allocation**: Ensures even distribution across eligible Spamurais
- **Complete Reporting**: Generates comprehensive allocation statistics

## 🚀 Quick Start

### 1. Prepare Your Google Sheet

Create a Google Sheet with these three tabs:

#### Tab 1: "All Contacts"
| Name | Phone Number | Center | Source of Interest |
|------|--------------|--------|-------------------|
| John | 1234567890 | Mumbai | Workshop |
| Sarah | 0987654321 | Delhi | Website |
| Mike | 5555555555 | Mumbai | Social Media |

#### Tab 2: "Spamurais"
| Name | Center |
|------|--------|
| Rahul | Mumbai |
| Priya | Delhi |
| Arjun | Mumbai |

#### Tab 3: "Source Priorities"
| Source of Interest | Priority |
|--------------------|----------|
| Workshop | 1 |
| Website | 2 |
| Social Media | 3 |

**Important**: Share the sheet as "Anyone with the link can view"

### 2. Run the Allocator

```bash
# Basic usage
python src/allocate_contacts.py --sheet-url "YOUR_GOOGLE_SHEET_URL"

# Custom output filename
python src/allocate_contacts.py --sheet-url "URL" --output my_allocation.xlsx

# Dry run (preview only, no Excel output)
python src/allocate_contacts.py --sheet-url "URL" --dry-run
```

### 3. Review the Output

The script creates `allocation_output.xlsx` with:

**INPUT TABS** (original data):
- All Contacts
- Spamurais
- Source Priorities

**OUTPUT TABS** (allocation results):
- Summary (statistics and breakdown)
- Rahul (contacts allocated to Rahul)
- Priya (contacts allocated to Priya)
- Arjun (contacts allocated to Arjun)
- Unallocated (contacts that couldn't be allocated, if any)

## ⚙️ Configuration

### Using config.json

Add to your `config.json`:

```json
{
  "contact_allocator": {
    "input_sheet_url": "https://docs.google.com/spreadsheets/d/YOUR_ID/edit",
    "contacts_tab": "All Contacts",
    "spamurais_tab": "Spamurais",
    "priorities_tab": "Source Priorities",
    "output_filename": "allocation_output.xlsx"
  }
}
```

Then run:
```bash
python src/allocate_contacts.py --config config.json
```

### Command Line Options

```
--sheet-url           Google Sheets URL (required if not using --config)
--output              Output Excel filename (default: allocation_output.xlsx)
--config              Path to config.json file
--contacts-tab        Name of contacts tab (default: "All Contacts")
--spamurais-tab       Name of Spamurais tab (default: "Spamurais")
--priorities-tab      Name of priorities tab (default: "Source Priorities")
--dry-run             Preview allocation without creating Excel file
--verbose             Enable verbose output
```

## 🎯 Allocation Rules

### 1. Center Matching (STRICT)

**Validation Rules**:
- If ANY contact has a center → ALL contacts MUST have a center
- If ANY Spamurai has a center → ALL Spamurais MUST have a center
- Validation fails if inconsistent → Script exits with clear error

**Matching Rules**:
- Contact center MUST match Spamurai center exactly
- If no centers defined: all Spamurais eligible for all contacts
- Mixed scenarios not allowed (enforced by validation)

### 2. Priority-Based Distribution

1. Sort contacts by Source of Interest priority (1, 2, 3, ...)
2. Process Priority 1 contacts first, then Priority 2, etc.
3. Missing/unknown sources assigned Priority 999 (lowest)

### 3. Round-Robin Allocation

Within each priority level:
- Distribute contacts evenly across eligible Spamurais
- Round-robin ensures fair distribution
- Example: 100 contacts, 3 Spamurais → each gets ~33 contacts

### 4. Unallocated Handling

Contacts are unallocated if:
- No Spamurai matches their center
- Example: Contact has "Bangalore" center, no Spamurai has "Bangalore"

Unallocated contacts appear in "Unallocated" tab with reason.

## 📊 Output Structure

### Summary Tab

Contains:
- **Total Contacts**: Number of contacts processed
- **Successfully Allocated**: Contacts assigned to Spamurais
- **Unallocated**: Contacts that couldn't be allocated
- **Spamurai Breakdown**: Per-Spamurai allocation counts
- **Priority Distribution**: Contacts per priority level

### Spamurai Tabs

Each Spamurai gets a dedicated tab with:
- Name
- Phone Number

Only allocated contacts appear (sorted as allocated).

### Unallocated Tab

If any contacts couldn't be allocated:
- Name
- Phone Number
- Center
- Source
- Reason (why it wasn't allocated)

## 🔍 Examples

### Example 1: Center-Based Allocation

**Input**:
- 10 Mumbai contacts, 5 Delhi contacts
- 2 Mumbai Spamurais, 1 Delhi Spamurai

**Output**:
- Spamurai 1 (Mumbai): 5 contacts
- Spamurai 2 (Mumbai): 5 contacts
- Spamurai 3 (Delhi): 5 contacts

### Example 2: Priority-Based

**Input**:
- 5 Workshop contacts (Priority 1)
- 10 Website contacts (Priority 2)
- 3 Spamurais (no centers)

**Output**:
- All 5 Workshop contacts allocated first (round-robin)
- Then 10 Website contacts allocated (round-robin)
- Final: Each Spamurai gets 5 contacts total

### Example 3: Unallocated Contacts

**Input**:
- Contact: "John", Center: "Bangalore"
- Spamurais: Mumbai, Delhi (no Bangalore)

**Output**:
- John appears in "Unallocated" tab
- Reason: "No Spamurai with center 'Bangalore'"

## 🛠️ Troubleshooting

### Error: "Center validation failed for CONTACTS"

**Problem**: Some contacts have centers, some don't

**Solution**: Either:
- Add centers to ALL contacts, OR
- Remove centers from ALL contacts

### Error: "Center validation failed for SPAMURAIS"

**Problem**: Some Spamurais have centers, some don't

**Solution**: Either:
- Add centers to ALL Spamurais, OR
- Remove centers from ALL Spamurais

### Error: "Tab 'All Contacts' not found"

**Problem**: Tab name doesn't match

**Solution**:
- Check tab name in Google Sheet
- Use `--contacts-tab "Your Tab Name"` to specify

### Error: "No module named 'openpyxl'"

**Problem**: Missing dependency

**Solution**:
```bash
pip install openpyxl
```

### Error: "Failed to download from Google Sheets"

**Problem**: Sheet not accessible

**Solution**:
- Ensure sheet is shared as "Anyone with the link can view"
- Check internet connection
- Verify URL is correct

## 📦 Dependencies

```bash
pip install pandas openpyxl requests
```

All dependencies already included in main `requirements.txt`.

## 💡 Tips

1. **Review Dry Run First**: Use `--dry-run` to preview allocation before creating Excel
2. **Check Summary Tab**: Always review Summary tab for overall statistics
3. **Validate Input Data**: Ensure no duplicate phone numbers in input
4. **Center Consistency**: Double-check all contacts and Spamurais have (or don't have) centers
5. **Upload to Google Drive**: You can upload the output Excel to Google Drive for cloud access

## 🔄 Workflow

```
1. Prepare Google Sheet with 3 tabs
   ↓
2. Share sheet (Anyone with link can view)
   ↓
3. Run allocator script
   ↓
4. Review allocation_output.xlsx
   ↓
5. Upload to Google Drive (optional)
   ↓
6. Share Spamurai tabs with respective team members
```

## 📝 Notes

- **No Credentials Required**: Uses public Google Sheets API (no authentication needed)
- **Local Output**: Excel file created locally, easy to review before sharing
- **Self-Contained**: Output includes both input and results in one file
- **Rerunnable**: Can rerun anytime with updated data
- **No Data Loss**: Original input tabs preserved in output

## 🧪 Testing

The project includes a comprehensive test suite with 40+ test cases covering all functionality.

### Run Tests

```bash
# Quick test run
pytest

# With coverage report
./run_tests.sh --coverage

# Verbose output
./run_tests.sh --verbose
```

### Test Coverage

- Unit tests for all core allocation logic
- Integration tests for CLI and end-to-end workflows
- 10 reusable test fixtures covering various scenarios
- Performance tests with large datasets

See [TESTING.md](TESTING.md) for complete testing documentation.

## 🆘 Support

If you encounter issues:

1. Run with `--verbose` for detailed error messages
2. Check `TROUBLESHOOTING.md` for common issues
3. Verify Google Sheet structure matches requirements
4. Ensure all dependencies installed

---

**Happy Allocating! 🥷⚡**
