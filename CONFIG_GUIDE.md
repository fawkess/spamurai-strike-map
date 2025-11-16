# Configuration Guide for SPAMURAI Contact Allocator

## Overview

The SPAMURAI Contact Allocator supports configuration through both a JSON config file and command-line arguments. This provides flexibility in setting default values while allowing override on a per-run basis.

## Configuration Priority

The system follows this priority order (highest to lowest):

1. **CLI Arguments** - Direct command-line parameters
2. **Config File** - Values from `allocator_config.json`
3. **Built-in Defaults** - Hardcoded fallback values

## Setup

### 1. Create Your Config File

```bash
# Copy the example config
cp allocator_config.example.json allocator_config.json

# Edit with your preferred settings
nano allocator_config.json  # or use your preferred editor
```

### 2. Config File Structure

```json
{
  "max_allocations_per_spamurai": 50,
  "contacts_tab": "All Contacts",
  "spamurais_tab": "Spamurais",
  "priorities_tab": "Source Priorities"
}
```

## Configuration Options

### `max_allocations_per_spamurai`

- **Type**: Integer or `null`
- **Default**: `null` (unlimited)
- **Description**: Maximum number of contacts each Spamurai can receive **per run**
- **Important**: This is a **per-run limit**, not a lifetime limit
  - If a Spamurai already has 100 contacts from previous runs
  - And you set `max_allocations_per_spamurai: 25`
  - They will receive up to 25 **new** contacts in this run
- **Example Use Cases**:
  - Batch processing: `"max_allocations_per_spamurai": 50` for controlled batches
  - Load balancing: `"max_allocations_per_spamurai": 100` to prevent overload
  - Testing: `"max_allocations_per_spamurai": 5` for small test runs

### `contacts_tab`

- **Type**: String
- **Default**: `"All Contacts"`
- **Description**: Name of the Google Sheets tab containing contact data
- **Required Columns**: Name, Phone Number, Center, Source of Interest

### `spamurais_tab`

- **Type**: String
- **Default**: `"Spamurais"`
- **Description**: Name of the Google Sheets tab containing Spamurai list
- **Required Columns**: Name, Center

### `priorities_tab`

- **Type**: String
- **Default**: `"Source Priorities"`
- **Description**: Name of the Google Sheets tab containing source priority mappings
- **Required Columns**: Source of Interest, Priority

## Usage Examples

### Example 1: Use Config File Defaults

```bash
python src/allocate_contacts.py --config allocator_config.json --sheet-url "YOUR_SHEET_URL"
```

**Result**: Uses all values from `allocator_config.json`

### Example 2: Override Allocation Limit

```bash
python src/allocate_contacts.py \
  --config allocator_config.json \
  --sheet-url "YOUR_SHEET_URL" \
  --max-allocations-per-spamurai 25
```

**Config file**: `"max_allocations_per_spamurai": 50`
**CLI argument**: `--max-allocations-per-spamurai 25`
**Result**: Uses **25** (CLI overrides config)

### Example 3: Override Tab Names

```bash
python src/allocate_contacts.py \
  --config allocator_config.json \
  --sheet-url "YOUR_SHEET_URL" \
  --contacts-tab "My Contacts"
```

**Config file**: `"contacts_tab": "All Contacts"`
**CLI argument**: `--contacts-tab "My Contacts"`
**Result**: Uses **"My Contacts"** tab (CLI overrides config)

### Example 4: No Config File

```bash
python src/allocate_contacts.py \
  --sheet-url "YOUR_SHEET_URL" \
  --max-allocations-per-spamurai 30
```

**Result**: Uses CLI values and built-in defaults (no config file needed)

### Example 5: Unlimited Allocations

To run without limits, either:

**Option A**: Omit the parameter entirely
```bash
python src/allocate_contacts.py --config allocator_config.json --sheet-url "YOUR_SHEET_URL"
```
(Ensure config file has `"max_allocations_per_spamurai": null`)

**Option B**: Don't use a config file
```bash
python src/allocate_contacts.py --sheet-url "YOUR_SHEET_URL"
```

## Common Workflows

### Workflow 1: Daily Batch Processing

**Setup**: `allocator_config.json`
```json
{
  "max_allocations_per_spamurai": 50
}
```

**Daily Run**:
```bash
python src/allocate_contacts.py --config allocator_config.json --sheet-url "URL"
```

Each run allocates max 50 contacts per Spamurai.

### Workflow 2: Testing Before Production

**Test Run** (small batch):
```bash
python src/allocate_contacts.py \
  --config allocator_config.json \
  --sheet-url "URL" \
  --max-allocations-per-spamurai 5 \
  --dry-run
```

**Production Run** (use config default):
```bash
python src/allocate_contacts.py --config allocator_config.json --sheet-url "URL"
```

### Workflow 3: Different Limits for Different Campaigns

**Campaign A** (high priority):
```bash
python src/allocate_contacts.py \
  --sheet-url "URL" \
  --max-allocations-per-spamurai 100 \
  --output campaign_a.xlsx
```

**Campaign B** (lower priority):
```bash
python src/allocate_contacts.py \
  --sheet-url "URL" \
  --max-allocations-per-spamurai 30 \
  --output campaign_b.xlsx
```

## Output Indicators

When using allocation limits, the system provides clear feedback:

### 1. Configuration Display

```
Input Sheet: https://docs.google.com/...
Output File: allocation_output.xlsx
Allocation Limit: 50 contacts per Spamurai (from config)
```

### 2. Summary Report

```
==============================================================
ALLOCATION SUMMARY
==============================================================

Allocation Limit: 50 contacts per Spamurai

Total Contacts:         200
Successfully Allocated: 150
Unallocated:            50

Per-Spamurai Breakdown (NEW allocations):
------------------------------------------------------------
  Rahul                (Mumbai)        50 new contacts [AT LIMIT]
  Priya                (Delhi)         50 new contacts [AT LIMIT]
  Arjun                (Mumbai)        50 new contacts [AT LIMIT]
```

### 3. Unallocated Contacts

If contacts can't be allocated due to limits, check the "Unallocated" tab in the Excel output:

| Name | Phone Number | Center | Source of Interest | Reason |
|------|--------------|--------|-------------------|---------|
| John | 1234567890 | Mumbai | Workshop | All eligible Spamurais have reached max allocation limit (50) |

## Troubleshooting

### Issue: Config file not found

**Error**: `Config file not found: allocator_config.json`

**Solution**:
```bash
cp allocator_config.example.json allocator_config.json
```

### Issue: Too many unallocated contacts

**Symptom**: Many contacts in "Unallocated" tab with reason "reached max allocation limit"

**Solutions**:
1. Increase the limit: `--max-allocations-per-spamurai 100`
2. Run in multiple batches
3. Add more Spamurais to the Google Sheet

### Issue: Limit not being applied

**Check**:
1. Verify config file syntax: `cat allocator_config.json`
2. Ensure value is a number: `"max_allocations_per_spamurai": 50` (not `"50"`)
3. Check if CLI is overriding: Remove `--max-allocations-per-spamurai` from command

## Best Practices

1. **Version Control**: Keep `allocator_config.example.json` in git, exclude `allocator_config.json`
2. **Team Sharing**: Share config settings via the example file
3. **Testing**: Always use `--dry-run` when testing new limits
4. **Documentation**: Comment your config choices in team docs
5. **Incremental Mode**: Use incremental mode to add more contacts if initial allocation hits limits

## Files

- `allocator_config.example.json` - Template config file (tracked in git)
- `allocator_config.json` - Your actual config (gitignored, created locally)
- `.gitignore` - Configured to ignore `allocator_config.json`

## Need Help?

Run the help command to see all options:
```bash
python src/allocate_contacts.py --help
```
