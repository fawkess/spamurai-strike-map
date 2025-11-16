#!/usr/bin/env python3
"""
SPAMURAI Contact Allocator
Standalone script to allocate contacts to Spamurais based on center and priority

Usage:
    python src/allocate_contacts.py --sheet-url "YOUR_GOOGLE_SHEET_URL"
    python src/allocate_contacts.py --config config.json
    python src/allocate_contacts.py --sheet-url "URL" --dry-run
    python src/allocate_contacts.py --sheet-url "URL" --output allocation_result.xlsx
"""

import sys
import os
import argparse
import logging
import json

# Always include script directory in module search path
sys.path.append(os.path.dirname(__file__))

from contact_allocator import ContactAllocator


def setup_logger():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def load_config_file(config_path):
    """
    Load configuration from JSON file

    Args:
        config_path: Path to config JSON file

    Returns:
        Dict with config values
    """
    if not config_path:
        return {}

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    return config


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='SPAMURAI Contact Allocator - Distribute contacts to Spamurais',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python src/allocate_contacts.py --sheet-url "https://docs.google.com/spreadsheets/d/YOUR_ID/edit"

  # Use config file for defaults
  python src/allocate_contacts.py --config allocator_config.json --sheet-url "URL"

  # Custom output filename
  python src/allocate_contacts.py --sheet-url "URL" --output my_allocation.xlsx

  # Dry run (validate only, don't write Excel)
  python src/allocate_contacts.py --sheet-url "URL" --dry-run

  # Custom tab names
  python src/allocate_contacts.py --sheet-url "URL" --contacts-tab "My Contacts"

  # Limit allocations per Spamurai (e.g., max 50 contacts each)
  python src/allocate_contacts.py --sheet-url "URL" --max-allocations-per-spamurai 50

  # Override config file limit with CLI argument
  python src/allocate_contacts.py --config allocator_config.json --sheet-url "URL" --max-allocations-per-spamurai 25

Configuration:
  - Create allocator_config.json based on allocator_config.example.json
  - Config file sets default values, CLI arguments override them
  - Priority: CLI arguments > config file > built-in defaults

Output:
  - Creates an Excel file with INPUT tabs (original data) and OUTPUT tabs (allocation results)
  - Default filename: allocation_output.xlsx
  - Contains tabs: All Contacts, Spamurais, Source Priorities, Summary, [Spamurai names], Unallocated

Requirements:
  - Google Sheet must have tabs: All Contacts, Spamurais, Source Priorities
  - Google Sheet must be shared as "Anyone with the link can view"
  - Dependencies: pip install pandas openpyxl requests
        """
    )

    parser.add_argument(
        '--config',
        default=None,
        help='Path to config JSON file (optional, for setting defaults)'
    )

    parser.add_argument(
        '--sheet-url',
        required=True,
        help='Google Sheets URL (input sheet with contacts, spamurais, priorities)'
    )

    parser.add_argument(
        '--output',
        default='allocation_output.xlsx',
        help='Output Excel filename (default: allocation_output.xlsx)'
    )

    parser.add_argument(
        '--contacts-tab',
        default='All Contacts',
        help='Name of contacts tab (default: "All Contacts")'
    )

    parser.add_argument(
        '--spamurais-tab',
        default='Spamurais',
        help='Name of Spamurais tab (default: "Spamurais")'
    )

    parser.add_argument(
        '--priorities-tab',
        default='Source Priorities',
        help='Name of priorities tab (default: "Source Priorities")'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate and preview allocation without creating Excel file'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--max-allocations-per-spamurai',
        type=int,
        default=None,
        help='Maximum number of contacts each Spamurai can receive (default: unlimited)'
    )

    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    logger = setup_logger()

    # Print header
    print()
    print("="*70)
    print("🥷⚡ SPAMURAI CONTACT ALLOCATOR")
    print("="*70)
    print()

    # Load config file if provided
    file_config = {}
    if args.config:
        try:
            file_config = load_config_file(args.config)
            logger.info(f"Loaded config from: {args.config}")
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            sys.exit(1)

    # Merge config: CLI arguments override config file values
    # Tab names
    contacts_tab = args.contacts_tab or file_config.get('contacts_tab', 'All Contacts')
    spamurais_tab = args.spamurais_tab or file_config.get('spamurais_tab', 'Spamurais')
    priorities_tab = args.priorities_tab or file_config.get('priorities_tab', 'Source Priorities')

    # Allocation limit: CLI > config file > None (unlimited)
    max_allocations = args.max_allocations_per_spamurai
    if max_allocations is None and 'max_allocations_per_spamurai' in file_config:
        max_allocations = file_config['max_allocations_per_spamurai']

    # Build config dict
    sheet_url = args.sheet_url
    config = {
        'contacts_tab': contacts_tab,
        'spamurais_tab': spamurais_tab,
        'priorities_tab': priorities_tab
    }

    logger.info(f"Input Sheet: {sheet_url}")
    if not args.dry_run:
        logger.info(f"Output File: {args.output}")
    if max_allocations:
        source = "CLI" if args.max_allocations_per_spamurai else "config"
        logger.info(f"Allocation Limit: {max_allocations} contacts per Spamurai (from {source})")
    logger.info("")

    # Create allocator
    allocator = ContactAllocator(
        sheet_url,
        logger,
        config=config,
        max_allocations_per_spamurai=max_allocations
    )

    try:
        # Step 1: Load data
        allocator.load_data()

        # Step 2: Validate
        is_valid, error_msg = allocator.validate_data()
        if not is_valid:
            logger.error("")
            logger.error("="*70)
            logger.error("❌ VALIDATION FAILED")
            logger.error("="*70)
            logger.error(f"Error: {error_msg}")
            logger.error("")
            logger.error("Please fix the data issues and try again.")
            logger.error("="*70)
            sys.exit(1)

        # Step 2B: Check for incremental mode (auto-detect existing file)
        use_incremental = False
        if os.path.exists(args.output) and not args.dry_run:
            logger.info("")
            logger.info("="*70)
            logger.info("📂 EXISTING ALLOCATION FILE DETECTED")
            logger.info("="*70)
            logger.info(f"File: {args.output}")
            logger.info("")

            # Try to load existing allocations to show stats
            existing_allocations = allocator.load_existing_allocations(args.output)
            existing_count = len(existing_allocations['allocated_phones'])
            existing_spamurais = len(existing_allocations['spamurai_allocations'])

            if existing_count > 0:
                logger.info(f"Existing allocations: {existing_count} contacts across {existing_spamurais} Spamurais")
                logger.info("")
                logger.info("Options:")
                logger.info("  1. INCREMENTAL - Add new contacts to existing allocations (recommended)")
                logger.info("  2. FRESH - Start over and replace all allocations")
                logger.info("")

                while True:
                    try:
                        choice = input("Enter choice (1/2): ").strip()
                        if choice == '1':
                            use_incremental = True
                            allocator.incremental_mode = True
                            allocator.existing_allocations = existing_allocations
                            logger.info("")
                            logger.info("✅ Using INCREMENTAL mode")
                            logger.info("")
                            break
                        elif choice == '2':
                            use_incremental = False
                            logger.info("")
                            logger.info("✅ Using FRESH mode (existing file will be replaced)")
                            logger.info("")
                            break
                        else:
                            print("Invalid choice. Please enter 1 or 2.")
                    except (EOFError, KeyboardInterrupt):
                        logger.info("")
                        logger.warning("⚠️  Operation cancelled by user")
                        sys.exit(1)

        # Step 3: Preprocess
        allocator.preprocess_data()

        # Step 3B: Filter already-allocated contacts (if incremental mode)
        if use_incremental:
            allocator.filter_already_allocated()

        # Step 4: Allocate
        result = allocator.allocate()

        # Step 5: Write output (unless dry-run)
        if args.dry_run:
            logger.info("")
            logger.info("="*70)
            logger.info("🔍 DRY RUN MODE - No Excel file created")
            logger.info("="*70)
            logger.info("")
            logger.info("Allocation preview completed successfully!")
            logger.info("Remove --dry-run flag to create Excel output.")
        else:
            allocator.write_to_excel(args.output)

            logger.info("")
            logger.info("="*70)
            logger.info("✅ ALLOCATION COMPLETED SUCCESSFULLY!")
            logger.info("="*70)
            logger.info("")
            logger.info("📊 Excel File Structure:")
            logger.info("  INPUT TABS (original data):")
            logger.info(f"    - {allocator.contacts_tab}")
            logger.info(f"    - {allocator.spamurais_tab}")
            logger.info(f"    - {allocator.priorities_tab}")
            logger.info("")
            logger.info("  OUTPUT TABS (allocation results):")
            logger.info("    - Summary (statistics)")
            for spamurai in allocator.spamurais:
                count = spamurai['allocation_count']
                logger.info(f"    - {spamurai['Name']:20s} ({count} contacts)")
            if allocator.unallocated:
                logger.info(f"    - Unallocated          ({len(allocator.unallocated)} contacts)")
            logger.info("")
            logger.info("📄 You can now:")
            logger.info("   1. Open the Excel file to review allocations")
            logger.info("   2. Upload to Google Drive if needed")
            logger.info("   3. Share specific tabs with each Spamurai")
            logger.info("")

        print("="*70)
        print()

    except KeyboardInterrupt:
        logger.info("")
        logger.warning("⚠️  Operation cancelled by user")
        sys.exit(1)

    except Exception as e:
        logger.error("")
        logger.error("="*70)
        logger.error("❌ ALLOCATION FAILED")
        logger.error("="*70)
        logger.error(f"Error: {str(e)}")
        logger.error("")
        if "No module named 'openpyxl'" in str(e):
            logger.error("Missing dependency. Install with:")
            logger.error("  pip install openpyxl")
        elif "Failed to download" in str(e):
            logger.error("Troubleshooting:")
            logger.error("  1. Check that Google Sheet URL is correct")
            logger.error("  2. Ensure sheet is shared as 'Anyone with the link can view'")
            logger.error("  3. Check your internet connection")
        else:
            logger.error("Please check the error message above and try again.")
        logger.error("="*70)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
