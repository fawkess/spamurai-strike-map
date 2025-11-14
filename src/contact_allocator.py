"""
Contact Allocator Module for SPAMURAI
Allocates contacts to Spamurais based on center matching and priority distribution

Usage:
    from contact_allocator import ContactAllocator

    allocator = ContactAllocator(sheet_url, logger)
    allocator.load_data()
    is_valid, error = allocator.validate_data()
    if is_valid:
        result = allocator.allocate()
        allocator.write_to_sheets(output_sheet_url)
"""

import os
import random
from collections import defaultdict
import pandas as pd


class ContactAllocator:
    """Handles contact allocation logic"""

    def __init__(self, sheet_url, logger, config=None):
        """
        Initialize contact allocator

        Args:
            sheet_url: Google Sheets URL with input data
            logger: Logger instance for output
            config: Optional configuration dict
        """
        self.sheet_url = sheet_url
        self.logger = logger
        self.config = config or {}

        # Tab names from config or defaults
        self.contacts_tab = self.config.get('contacts_tab', 'All Contacts')
        self.spamurais_tab = self.config.get('spamurais_tab', 'Spamurais')
        self.priorities_tab = self.config.get('priorities_tab', 'Source Priorities')

        # Data containers
        self.contacts = []
        self.spamurais = []
        self.priorities = {}
        self.unallocated = []

        # Raw data for copying to output (preserve original)
        self.raw_contacts_data = []
        self.raw_spamurais_data = []
        self.raw_priorities_data = []

        # Incremental mode data
        self.existing_allocations = None
        self.already_allocated_contacts = []
        self.incremental_mode = False
        self.duplicate_stats = {
            'input_duplicates': [],
            'already_allocated': []
        }

        # Results
        self.allocation_result = None

    # =========================================================================
    # PHASE 1: DATA LOADING
    # =========================================================================

    def load_data(self):
        """Load all data from Google Sheets"""
        from google_sheets_client import GoogleSheetsClient

        self.logger.info("="*60)
        self.logger.info("CONTACT ALLOCATOR - Loading Data")
        self.logger.info("="*60)

        sheets_client = GoogleSheetsClient(self.logger)

        # Load contacts
        self.logger.info(f"Loading contacts from '{self.contacts_tab}' tab...")
        contacts_rows, _ = sheets_client.fetch_messages_by_tab_name(
            self.sheet_url,
            self.contacts_tab
        )
        self._parse_contacts(contacts_rows)
        self.logger.info(f"✅ Loaded {len(self.contacts)} contacts")

        # Load Spamurais
        self.logger.info(f"Loading Spamurais from '{self.spamurais_tab}' tab...")
        spamurais_rows, _ = sheets_client.fetch_messages_by_tab_name(
            self.sheet_url,
            self.spamurais_tab
        )
        self._parse_spamurais(spamurais_rows)
        self.logger.info(f"✅ Loaded {len(self.spamurais)} Spamurais")

        # Load priorities
        self.logger.info(f"Loading priorities from '{self.priorities_tab}' tab...")
        priorities_rows, _ = sheets_client.fetch_messages_by_tab_name(
            self.sheet_url,
            self.priorities_tab
        )
        self._parse_priorities(priorities_rows)
        self.logger.info(f"✅ Loaded {len(self.priorities)} priority mappings")

        self.logger.info("")

    def _parse_contacts(self, rows):
        """Parse contacts from sheet rows"""
        if not rows:
            raise Exception("No contacts data found")

        # Store raw data for output Excel (include headers)
        self.raw_contacts_data = [['Name', 'Phone Number', 'Center', 'Source of Interest']]

        # Expecting columns: Name | Phone Number | Center | Source of Interest
        for i, row in enumerate(rows):
            # Store all rows for raw data output
            self.raw_contacts_data.append(row)

            if len(row) < 2:
                continue  # Skip rows without minimum required fields

            name = row[0].strip() if len(row) > 0 else ""
            phone = str(row[1]).strip() if len(row) > 1 else ""
            center = row[2].strip() if len(row) > 2 and row[2] else None
            source = row[3].strip() if len(row) > 3 and row[3] else None

            if not name or not phone:
                continue  # Skip invalid rows

            # Normalize phone (remove .0 from Excel numbers)
            phone = phone.replace('.0', '')

            self.contacts.append({
                'name': name,
                'phone': phone,
                'center': center,
                'source': source,
                'priority': None,  # Will be resolved later
                'row_index': i + 1
            })

    def _parse_spamurais(self, rows):
        """Parse Spamurais from sheet rows"""
        if not rows:
            raise Exception("No Spamurais data found")

        # Store raw data for output Excel (include headers)
        self.raw_spamurais_data = [['Name', 'Center']]

        # Expecting columns: Name | Center
        for i, row in enumerate(rows):
            # Store all rows for raw data output
            self.raw_spamurais_data.append(row)

            if len(row) < 1:
                continue

            name = row[0].strip() if len(row) > 0 else ""
            center = row[1].strip() if len(row) > 1 and row[1] else None

            if not name:
                continue

            self.spamurais.append({
                'name': name,
                'center': center,
                'allocated_contacts': [],
                'allocation_count': 0
            })

    def _parse_priorities(self, rows):
        """Parse source priorities from sheet rows"""
        if not rows:
            self.logger.warning("No priorities data found - will use default priority 999 for all")
            self.raw_priorities_data = [['Source of Interest', 'Priority']]
            return

        # Store raw data for output Excel (include headers)
        self.raw_priorities_data = [['Source of Interest', 'Priority']]

        # Expecting columns: Source of Interest | Priority
        for i, row in enumerate(rows):
            # Store all rows for raw data output
            self.raw_priorities_data.append(row)

            if len(row) < 2:
                continue

            source = row[0].strip() if len(row) > 0 else ""
            try:
                priority = int(row[1]) if len(row) > 1 else 999
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid priority value at row {i+1}, using 999")
                priority = 999

            if source:
                self.priorities[source] = priority

    # =========================================================================
    # PHASE 2: VALIDATION
    # =========================================================================

    def validate_data(self):
        """
        Validate data integrity with strict rules

        Returns:
            (is_valid, error_message) tuple
        """
        self.logger.info("="*60)
        self.logger.info("VALIDATION")
        self.logger.info("="*60)

        # Check if we have data
        if not self.contacts:
            return (False, "No contacts found in sheet")

        if not self.spamurais:
            return (False, "No Spamurais found in sheet")

        # Validate center consistency
        is_valid, error = self._validate_center_consistency()
        if not is_valid:
            return (False, error)

        self.logger.info("✅ All validations passed")
        self.logger.info("")
        return (True, None)

    def _validate_center_consistency(self):
        """
        STRICT VALIDATION:
        - If ANY contact has center, ALL must have center
        - If ANY Spamurai has center, ALL must have center

        Returns:
            (is_valid, error_message) tuple
        """
        # Check contacts
        contacts_with_center = [c for c in self.contacts if c.get('center')]
        contacts_without_center = [c for c in self.contacts if not c.get('center')]

        if contacts_with_center and contacts_without_center:
            self.logger.error(
                f"❌ CENTER VALIDATION FAILED FOR CONTACTS:\n"
                f"   {len(contacts_with_center)} contacts have center\n"
                f"   {len(contacts_without_center)} contacts missing center\n"
                f"   Either ALL contacts must have center or NONE."
            )
            # Show examples
            self.logger.error(f"\n   Examples with center: {contacts_with_center[:3]}")
            self.logger.error(f"   Examples without center: {contacts_without_center[:3]}")

            return (False,
                    f"Center validation failed for CONTACTS: "
                    f"{len(contacts_with_center)} have center, "
                    f"{len(contacts_without_center)} missing center. "
                    f"Either ALL contacts must have center or NONE.")

        # Check Spamurais
        spamurais_with_center = [s for s in self.spamurais if s.get('center')]
        spamurais_without_center = [s for s in self.spamurais if not s.get('center')]

        if spamurais_with_center and spamurais_without_center:
            self.logger.error(
                f"❌ CENTER VALIDATION FAILED FOR SPAMURAIS:\n"
                f"   {len(spamurais_with_center)} Spamurais have center\n"
                f"   {len(spamurais_without_center)} Spamurais missing center\n"
                f"   Either ALL Spamurais must have center or NONE."
            )
            # Show examples
            self.logger.error(f"\n   With center: {[s['name'] for s in spamurais_with_center]}")
            self.logger.error(f"   Without center: {[s['name'] for s in spamurais_without_center]}")

            return (False,
                    f"Center validation failed for SPAMURAIS: "
                    f"{len(spamurais_with_center)} have center, "
                    f"{len(spamurais_without_center)} missing center. "
                    f"Either ALL Spamurais must have center or NONE.")

        # Log validation results
        if contacts_with_center:
            self.logger.info(f"✅ All {len(self.contacts)} contacts have center")
        else:
            self.logger.info(f"✅ No contacts have center (center matching disabled)")

        if spamurais_with_center:
            self.logger.info(f"✅ All {len(self.spamurais)} Spamurais have center")
        else:
            self.logger.info(f"✅ No Spamurais have center (center matching disabled)")

        return (True, None)

    # =========================================================================
    # PHASE 3: PREPROCESSING
    # =========================================================================

    def preprocess_data(self):
        """Clean and prepare data for allocation"""
        self.logger.info("="*60)
        self.logger.info("PREPROCESSING")
        self.logger.info("="*60)

        # Remove duplicates
        self._remove_duplicates()

        # Assign priorities
        self._assign_priorities()

        self.logger.info("")

    def _remove_duplicates(self):
        """Remove duplicate phone numbers (keep first occurrence)"""
        seen_phones = {}
        unique_contacts = []
        duplicates = []

        for contact in self.contacts:
            phone = contact['phone']
            if phone not in seen_phones:
                seen_phones[phone] = contact['name']
                unique_contacts.append(contact)
            else:
                duplicates.append({
                    'phone': phone,
                    'kept_name': seen_phones[phone],
                    'duplicate_name': contact['name']
                })
                self.duplicate_stats['input_duplicates'].append(contact)

        if duplicates:
            self.logger.info(f"⚠️  Removed {len(duplicates)} duplicate phone numbers (kept first occurrence)")
            if len(duplicates) <= 5:
                for dup in duplicates:
                    self.logger.info(f"     {dup['phone']}: kept '{dup['kept_name']}', removed '{dup['duplicate_name']}'")
            else:
                self.logger.info(f"     (showing first 5)")
                for dup in duplicates[:5]:
                    self.logger.info(f"     {dup['phone']}: kept '{dup['kept_name']}', removed '{dup['duplicate_name']}'")

        self.contacts = unique_contacts
        self.logger.info(f"✅ {len(self.contacts)} unique contacts after deduplication")

    def _assign_priorities(self):
        """Assign priority to each contact based on source"""
        no_source_count = 0
        unknown_sources = set()

        for contact in self.contacts:
            source = contact.get('source')

            if not source:
                # No source = lowest priority
                contact['priority'] = 999
                no_source_count += 1
            elif source in self.priorities:
                # Known source
                contact['priority'] = self.priorities[source]
            else:
                # Unknown source = lowest priority
                contact['priority'] = 999
                unknown_sources.add(source)

        if no_source_count > 0:
            self.logger.info(f"ℹ️  {no_source_count} contacts without source (assigned priority 999)")

        if unknown_sources:
            self.logger.info(f"ℹ️  Unknown sources assigned priority 999: {unknown_sources}")

        self.logger.info(f"✅ Priorities assigned to all contacts")

    # =========================================================================
    # PHASE 3B: INCREMENTAL MODE SUPPORT
    # =========================================================================

    def load_existing_allocations(self, output_filename):
        """
        Load existing allocations from output Excel file

        Args:
            output_filename: Path to existing Excel file

        Returns:
            dict with allocated_phones set and spamurai_allocations
        """
        import pandas as pd

        if not os.path.exists(output_filename):
            self.logger.info(f"No existing output file found: {output_filename}")
            return {
                'allocated_phones': set(),
                'spamurai_allocations': {},
                'inactive_spamurais': []
            }

        self.logger.info(f"Loading existing allocations from: {output_filename}")

        allocated_phones = set()
        spamurai_allocations = {}

        try:
            # Read Excel file to get all sheet names
            excel_file = pd.ExcelFile(output_filename)
            all_sheets = excel_file.sheet_names

            # Identify input tabs and special tabs to skip
            skip_tabs = {
                self.contacts_tab,
                self.spamurais_tab,
                self.priorities_tab,
                'Summary',
                'Unallocated'
            }

            # Process each Spamurai tab
            spamurai_tabs = [sheet for sheet in all_sheets if sheet not in skip_tabs]

            for tab_name in spamurai_tabs:
                # Read tab data
                df = pd.read_excel(output_filename, sheet_name=tab_name)

                # Extract contacts
                contacts = []
                for _, row in df.iterrows():
                    if pd.notna(row.get('Name')) and pd.notna(row.get('Phone Number')):
                        phone = str(row['Phone Number']).strip().replace('.0', '')
                        contact = {
                            'name': str(row['Name']).strip(),
                            'phone': phone
                        }
                        contacts.append(contact)
                        allocated_phones.add(phone)

                spamurai_allocations[tab_name] = contacts

            self.logger.info(f"✅ Loaded {len(allocated_phones)} existing allocations across {len(spamurai_allocations)} Spamurais")

            # Identify inactive Spamurais (in file but not in current input)
            current_spamurai_names = {s['name'] for s in self.spamurais}
            inactive_spamurais = [name for name in spamurai_allocations.keys()
                                 if name not in current_spamurai_names]

            if inactive_spamurais:
                self.logger.warning(f"⚠️  Found {len(inactive_spamurais)} inactive Spamurais (in file but not in input): {inactive_spamurais}")

            return {
                'allocated_phones': allocated_phones,
                'spamurai_allocations': spamurai_allocations,
                'inactive_spamurais': inactive_spamurais
            }

        except Exception as e:
            self.logger.error(f"Failed to load existing allocations: {str(e)}")
            return {
                'allocated_phones': set(),
                'spamurai_allocations': {},
                'inactive_spamurais': []
            }

    def filter_already_allocated(self):
        """
        Remove contacts that are already allocated (for incremental mode)

        Updates self.contacts to only include new contacts
        Stores already-allocated contacts in self.already_allocated_contacts
        """
        if not self.existing_allocations or not self.existing_allocations['allocated_phones']:
            return  # Nothing to filter

        new_contacts = []
        already_allocated = []

        for contact in self.contacts:
            if contact['phone'] in self.existing_allocations['allocated_phones']:
                already_allocated.append(contact)
                self.duplicate_stats['already_allocated'].append(contact)
            else:
                new_contacts.append(contact)

        self.logger.info("")
        self.logger.info(f"📊 Incremental Mode Filtering:")
        self.logger.info(f"   Total contacts in input:     {len(self.contacts)}")
        self.logger.info(f"   Already allocated (skipped): {len(already_allocated)}")
        self.logger.info(f"   NEW contacts to allocate:    {len(new_contacts)}")

        self.contacts = new_contacts
        self.already_allocated_contacts = already_allocated

    # =========================================================================
    # PHASE 4: ALLOCATION ALGORITHM
    # =========================================================================

    def allocate(self):
        """
        Main allocation logic

        Returns:
            Allocation result dictionary
        """
        self.logger.info("="*60)
        self.logger.info("ALLOCATION")
        self.logger.info("="*60)

        # Step 1: Sort contacts by priority (ascending)
        sorted_contacts = sorted(self.contacts, key=lambda c: c['priority'])

        # Step 2: Group by priority
        priority_groups = defaultdict(list)
        for contact in sorted_contacts:
            priority_groups[contact['priority']].append(contact)

        # Step 3: Allocate each priority group
        for priority in sorted(priority_groups.keys()):
            contacts_at_priority = priority_groups[priority]
            self.logger.info(f"Allocating priority {priority}: {len(contacts_at_priority)} contacts")
            self._allocate_priority_group(contacts_at_priority)

        # Step 4: Build allocation result
        self.allocation_result = self._build_allocation_result()

        # Step 5: Print summary
        self._print_summary()

        return self.allocation_result

    def _allocate_priority_group(self, contacts):
        """
        Allocate contacts within a single priority level using round-robin

        Args:
            contacts: List of contacts at same priority
        """
        spamurai_index = 0

        for contact in contacts:
            # Get eligible Spamurais for this contact
            eligible = self._get_eligible_spamurais(contact)

            if not eligible:
                # No eligible Spamurai - add to unallocated
                reason = self._get_unallocation_reason(contact)
                self.unallocated.append({
                    'contact': contact,
                    'reason': reason
                })
                continue

            # Round-robin assignment
            selected_spamurai = eligible[spamurai_index % len(eligible)]
            selected_spamurai['allocated_contacts'].append(contact)
            selected_spamurai['allocation_count'] += 1

            spamurai_index += 1

    def _get_eligible_spamurais(self, contact):
        """
        Get Spamurais eligible for this contact

        Rules:
        - If both have centers: must match exactly
        - If neither has centers: all eligible

        Args:
            contact: Contact dictionary

        Returns:
            List of eligible Spamurai dictionaries
        """
        eligible = []
        contact_center = contact.get('center')

        for spamurai in self.spamurais:
            spamurai_center = spamurai.get('center')

            # Both have centers - must match
            if contact_center and spamurai_center:
                if contact_center == spamurai_center:
                    eligible.append(spamurai)
            # Neither has centers - eligible
            elif not contact_center and not spamurai_center:
                eligible.append(spamurai)

        return eligible

    def _get_unallocation_reason(self, contact):
        """Get reason why contact couldn't be allocated"""
        contact_center = contact.get('center')

        if contact_center:
            # Check if any Spamurai has this center
            spamurai_centers = [s.get('center') for s in self.spamurais if s.get('center')]
            if contact_center not in spamurai_centers:
                return f"No Spamurai with center '{contact_center}'"

        return "Unknown reason"

    def _build_allocation_result(self):
        """Build allocation result dictionary"""
        # Calculate totals
        total_contacts = len(self.contacts)
        allocated = sum(s['allocation_count'] for s in self.spamurais)
        unallocated_count = len(self.unallocated)

        # Build Spamurai breakdown
        spamurai_breakdown = {}
        for spamurai in self.spamurais:
            spamurai_breakdown[spamurai['name']] = {
                'count': spamurai['allocation_count'],
                'center': spamurai.get('center')
            }

        # Build priority distribution
        priority_distribution = defaultdict(int)
        for spamurai in self.spamurais:
            for contact in spamurai['allocated_contacts']:
                priority_distribution[contact['priority']] += 1

        return {
            'spamurai_allocations': {s['name']: s['allocated_contacts'] for s in self.spamurais},
            'unallocated': self.unallocated,
            'summary': {
                'total_contacts': total_contacts,
                'allocated': allocated,
                'unallocated': unallocated_count,
                'spamurai_breakdown': spamurai_breakdown,
                'priority_distribution': dict(priority_distribution)
            }
        }

    def _print_summary(self):
        """Print allocation summary to logger"""
        self.logger.info("")
        self.logger.info("="*60)
        if self.incremental_mode:
            self.logger.info("ALLOCATION SUMMARY (Incremental Mode)")
        else:
            self.logger.info("ALLOCATION SUMMARY")
        self.logger.info("="*60)

        summary = self.allocation_result['summary']

        # Show incremental mode statistics if applicable
        if self.incremental_mode and self.existing_allocations:
            existing_count = len(self.existing_allocations['allocated_phones'])
            input_duplicates = len(self.duplicate_stats['input_duplicates'])
            already_allocated = len(self.duplicate_stats['already_allocated'])

            self.logger.info("")
            self.logger.info("Input Statistics:")
            self.logger.info(f"  Contacts from Google Sheet:  {len(self.contacts) + already_allocated + input_duplicates}")
            if input_duplicates > 0:
                self.logger.info(f"  Duplicates removed:           {input_duplicates}")
            if already_allocated > 0:
                self.logger.info(f"  Already allocated (skipped):  {already_allocated}")
            self.logger.info(f"  NEW contacts to allocate:     {summary['total_contacts']}")
            self.logger.info("")
            self.logger.info("Allocation Results (NEW contacts only):")
        else:
            self.logger.info("")

        self.logger.info(f"  Total Contacts:         {summary['total_contacts']}")
        self.logger.info(f"  Successfully Allocated: {summary['allocated']}")
        self.logger.info(f"  Unallocated:            {summary['unallocated']}")

        if self.incremental_mode and self.existing_allocations:
            existing_count = len(self.existing_allocations['allocated_phones'])
            total_cumulative = existing_count + summary['allocated']
            self.logger.info("")
            self.logger.info("Cumulative Totals:")
            self.logger.info(f"  Previously allocated:   {existing_count}")
            self.logger.info(f"  Newly allocated:        {summary['allocated']}")
            self.logger.info(f"  TOTAL allocated:        {total_cumulative}")

        self.logger.info("")
        self.logger.info("Per-Spamurai Breakdown (NEW allocations):")
        self.logger.info("-" * 60)
        for name, stats in summary['spamurai_breakdown'].items():
            center_info = f"({stats['center']})" if stats['center'] else "(Any)"
            self.logger.info(f"  {name:20s} {center_info:15s} {stats['count']:3d} new contacts")

        if summary['priority_distribution']:
            self.logger.info("")
            self.logger.info("Priority Distribution:")
            self.logger.info("-" * 60)
            for priority in sorted(summary['priority_distribution'].keys()):
                count = summary['priority_distribution'][priority]
                self.logger.info(f"  Priority {priority:3d}: {count:3d} contacts")

        if self.unallocated:
            self.logger.info("")
            self.logger.info(f"⚠️  {len(self.unallocated)} Unallocated Contacts:")
            self.logger.info("-" * 60)
            for item in self.unallocated[:10]:  # Show first 10
                contact = item['contact']
                self.logger.info(f"  {contact['name']:20s} {contact['phone']:15s} - {item['reason']}")
            if len(self.unallocated) > 10:
                self.logger.info(f"  ... and {len(self.unallocated) - 10} more")

        # Show inactive Spamurais warning
        if self.incremental_mode and self.existing_allocations:
            inactive = self.existing_allocations.get('inactive_spamurais', [])
            if inactive:
                self.logger.info("")
                self.logger.info(f"⚠️  Inactive Spamurais (preserved in output):")
                self.logger.info("-" * 60)
                for name in inactive:
                    existing_count = len(self.existing_allocations['spamurai_allocations'].get(name, []))
                    self.logger.info(f"  {name:20s} {existing_count:3d} existing contacts (no new allocations)")

        self.logger.info("="*60)

    # =========================================================================
    # PHASE 5: OUTPUT TO EXCEL FILE
    # =========================================================================

    def write_to_excel(self, output_filename='allocation_output.xlsx'):
        """
        Write allocation results to Excel file
        Includes both input tabs and output tabs

        Args:
            output_filename: Output Excel filename

        Excel Structure:
            INPUT TABS:
            - All Contacts (original data)
            - Spamurais (original data)
            - Source Priorities (original data)

            OUTPUT TABS:
            - Summary (allocation statistics)
            - [Spamurai Name] (one tab per Spamurai with allocated contacts)
            - Unallocated (contacts that couldn't be allocated)
        """
        import pandas as pd

        self.logger.info("")
        self.logger.info("="*60)
        self.logger.info("WRITING OUTPUT TO EXCEL FILE")
        self.logger.info("="*60)
        self.logger.info(f"Output file: {output_filename}")
        self.logger.info("")

        # Create Excel writer
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            # ===== INPUT TABS (copy original data) =====

            # Tab 1: All Contacts (original)
            self.logger.info(f"Writing '{self.contacts_tab}' tab (original data)...")
            df_contacts = pd.DataFrame(self.raw_contacts_data[1:], columns=self.raw_contacts_data[0])
            df_contacts.to_excel(writer, sheet_name=self.contacts_tab, index=False)

            # Tab 2: Spamurais (original)
            self.logger.info(f"Writing '{self.spamurais_tab}' tab (original data)...")
            df_spamurais = pd.DataFrame(self.raw_spamurais_data[1:], columns=self.raw_spamurais_data[0])
            df_spamurais.to_excel(writer, sheet_name=self.spamurais_tab, index=False)

            # Tab 3: Source Priorities (original)
            self.logger.info(f"Writing '{self.priorities_tab}' tab (original data)...")
            df_priorities = pd.DataFrame(self.raw_priorities_data[1:], columns=self.raw_priorities_data[0])
            df_priorities.to_excel(writer, sheet_name=self.priorities_tab, index=False)

            # ===== OUTPUT TABS (allocation results) =====

            # Tab 4: Summary
            self.logger.info("Writing 'Summary' tab...")
            summary_data = self._build_summary_data()
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False, header=False)

            # Tab 5+: One tab per Spamurai (merge with existing if incremental)
            for spamurai in self.spamurais:
                tab_name = spamurai['name']
                new_contacts = spamurai['allocated_contacts']

                # In incremental mode, merge with existing allocations
                if self.incremental_mode and self.existing_allocations:
                    existing_contacts = self.existing_allocations['spamurai_allocations'].get(tab_name, [])

                    # Merge: existing + new
                    all_contacts = existing_contacts + new_contacts

                    # Deduplicate by phone (keep first occurrence)
                    seen_phones = set()
                    deduplicated_contacts = []
                    for contact in all_contacts:
                        if contact['phone'] not in seen_phones:
                            seen_phones.add(contact['phone'])
                            deduplicated_contacts.append(contact)

                    total_count = len(deduplicated_contacts)
                    new_count = len(new_contacts)
                    existing_count = len(existing_contacts)

                    self.logger.info(f"Writing '{tab_name}' tab ({existing_count} existing + {new_count} new = {total_count} total)...")
                    final_contacts = deduplicated_contacts
                else:
                    final_contacts = new_contacts
                    self.logger.info(f"Writing '{tab_name}' tab ({len(final_contacts)} contacts)...")

                # Prepare data for Excel
                contacts_data = []
                for contact in final_contacts:
                    contacts_data.append({
                        'Name': contact['name'],
                        'Phone Number': contact['phone']
                    })

                if contacts_data:
                    df_spamurai = pd.DataFrame(contacts_data)
                else:
                    # Empty tab
                    df_spamurai = pd.DataFrame(columns=['Name', 'Phone Number'])

                df_spamurai.to_excel(writer, sheet_name=tab_name, index=False)

            # Write tabs for inactive Spamurais (preserve their data)
            if self.incremental_mode and self.existing_allocations:
                inactive_spamurais = self.existing_allocations.get('inactive_spamurais', [])
                for spamurai_name in inactive_spamurais:
                    existing_contacts = self.existing_allocations['spamurai_allocations'].get(spamurai_name, [])

                    if existing_contacts:
                        self.logger.info(f"Writing '{spamurai_name}' tab (INACTIVE - {len(existing_contacts)} existing contacts preserved)...")

                        contacts_data = []
                        for contact in existing_contacts:
                            contacts_data.append({
                                'Name': contact['name'],
                                'Phone Number': contact['phone']
                            })

                        df_inactive = pd.DataFrame(contacts_data)
                        df_inactive.to_excel(writer, sheet_name=spamurai_name, index=False)

            # Last Tab: Unallocated (if any)
            if self.unallocated:
                self.logger.info(f"Writing 'Unallocated' tab ({len(self.unallocated)} contacts)...")

                unallocated_data = []
                for item in self.unallocated:
                    contact = item['contact']
                    unallocated_data.append({
                        'Name': contact['name'],
                        'Phone Number': contact['phone'],
                        'Center': contact.get('center') or '',
                        'Source': contact.get('source') or '',
                        'Reason': item['reason']
                    })

                df_unallocated = pd.DataFrame(unallocated_data)
                df_unallocated.to_excel(writer, sheet_name='Unallocated', index=False)

        self.logger.info("")
        self.logger.info("✅ Excel file created successfully!")
        self.logger.info(f"📄 Output: {output_filename}")
        self.logger.info("="*60)

    def _build_summary_data(self):
        """Build summary data for Excel output"""
        summary = self.allocation_result['summary']

        data = [
            ['ALLOCATION SUMMARY', '', ''],
            ['', '', ''],
            ['Metric', 'Value', ''],
            ['Total Contacts', summary['total_contacts'], ''],
            ['Successfully Allocated', summary['allocated'], ''],
            ['Unallocated', summary['unallocated'], ''],
            ['Total Spamurais', len(self.spamurais), ''],
            ['', '', ''],
            ['SPAMURAI BREAKDOWN', '', ''],
            ['Spamurai', 'Center', 'Contacts Allocated'],
        ]

        for name, stats in summary['spamurai_breakdown'].items():
            data.append([name, stats['center'] or 'Any', stats['count']])

        data.append(['', '', ''])
        data.append(['PRIORITY DISTRIBUTION', '', ''])
        data.append(['Priority', 'Contacts', ''])

        for priority in sorted(summary['priority_distribution'].keys()):
            count = summary['priority_distribution'][priority]
            data.append([f'Priority {priority}', count, ''])

        return data
