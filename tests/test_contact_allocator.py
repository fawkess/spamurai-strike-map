#!/usr/bin/env python3
"""
Unit tests for ContactAllocator class
Tests all core allocation functionality
"""

import pytest
import os
import sys
import logging
import tempfile
import pandas as pd
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from contact_allocator import ContactAllocator

# Test fixtures directory
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


@pytest.fixture
def logger():
    """Create test logger"""
    logger = logging.getLogger('test')
    logger.setLevel(logging.INFO)
    return logger


@pytest.fixture
def temp_output():
    """Create temporary output file"""
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        yield tmp.name
    # Cleanup
    if os.path.exists(tmp.name):
        os.remove(tmp.name)


class TestBasicAllocation:
    """Test basic allocation without centers"""

    def test_basic_allocation(self, logger, temp_output):
        """Test basic round-robin allocation"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()

        is_valid, error_msg = allocator.validate_data()
        assert is_valid, f"Validation failed: {error_msg}"

        allocator.preprocess_data()
        result = allocator.allocate()

        # Check result structure
        assert 'spamurai_allocations' in result
        assert 'unallocated' in result
        assert 'summary' in result

        # Should have 2 Spamurais
        assert len(result['spamurai_allocations']) == 2
        assert 'Rahul' in result['spamurai_allocations']
        assert 'Priya' in result['spamurai_allocations']

        # All 6 contacts should be allocated
        total_allocated = sum(len(contacts) for contacts in result['spamurai_allocations'].values())
        assert total_allocated == 6

        # No unallocated
        assert len(result['unallocated']) == 0

        # Round-robin should distribute evenly: 3 each
        assert len(result['spamurai_allocations']['Rahul']) == 3
        assert len(result['spamurai_allocations']['Priya']) == 3

    def test_priority_ordering(self, logger, temp_output):
        """Test that higher priority contacts are allocated first"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # Get all allocated contacts in order
        all_allocated = []
        for spamurai_name, contacts in result['spamurai_allocations'].items():
            all_allocated.extend(contacts)

        # Priority 1 (Workshop) contacts should come first
        # We have Alice, Charlie, Eve with Workshop (Priority 1)
        workshop_phones = {'1111111111', '3333333333', '5555555555'}
        first_three = {c['Phone Number'] for c in all_allocated[:3]}

        # First 3 allocated should be all workshop contacts
        assert first_three == workshop_phones

    def test_excel_output(self, logger, temp_output):
        """Test Excel file is created with correct structure"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        allocator.allocate()
        allocator.write_to_excel(temp_output)

        # Check file exists
        assert os.path.exists(temp_output)

        # Read and verify structure
        excel_file = pd.ExcelFile(temp_output)
        sheet_names = excel_file.sheet_names

        # Should have INPUT tabs
        assert 'All Contacts' in sheet_names
        assert 'Spamurais' in sheet_names
        assert 'Source Priorities' in sheet_names

        # Should have OUTPUT tabs
        assert 'Summary' in sheet_names
        assert 'Rahul' in sheet_names
        assert 'Priya' in sheet_names

        # Check Summary tab has data
        summary = pd.read_excel(excel_file, sheet_name='Summary')
        assert len(summary) > 0

        # Check Spamurai tabs have contacts
        rahul_df = pd.read_excel(excel_file, sheet_name='Rahul')
        priya_df = pd.read_excel(excel_file, sheet_name='Priya')

        assert len(rahul_df) == 3
        assert len(priya_df) == 3


class TestCenterBasedAllocation:
    """Test allocation with center matching"""

    def test_center_matching(self, logger, temp_output):
        """Test contacts are only allocated to matching centers"""
        fixture = os.path.join(FIXTURES_DIR, 'center_based_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # Check Mumbai Spamurais only get Mumbai contacts
        rahul_contacts = result['spamurai_allocations']['Rahul']
        arjun_contacts = result['spamurai_allocations']['Arjun']

        for contact in rahul_contacts:
            assert contact['Center'] == 'Mumbai'

        for contact in arjun_contacts:
            assert contact['Center'] == 'Mumbai'

        # Check Delhi Spamurai only gets Delhi contacts
        priya_contacts = result['spamurai_allocations']['Priya']
        for contact in priya_contacts:
            assert contact['Center'] == 'Delhi'

    def test_unallocated_center_mismatch(self, logger, temp_output):
        """Test contacts with no matching center go to unallocated"""
        fixture = os.path.join(FIXTURES_DIR, 'unallocated_contacts.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # Charlie (Bangalore) should be unallocated
        assert len(result['unallocated']) == 1
        assert result['unallocated'][0]['Name'] == 'Charlie'
        assert result['unallocated'][0]['Center'] == 'Bangalore'
        assert 'No Spamurai with center' in result['unallocated'][0]['Reason']

        # Other 3 should be allocated
        total_allocated = sum(len(contacts) for contacts in result['spamurai_allocations'].values())
        assert total_allocated == 3

    def test_center_validation_contacts_mixed(self, logger):
        """Test validation fails when some contacts have centers and some don't"""
        fixture = os.path.join(FIXTURES_DIR, 'invalid_contacts_centers.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()

        is_valid, error_msg = allocator.validate_data()
        assert not is_valid
        assert 'CONTACTS' in error_msg
        assert 'some have Center' in error_msg

    def test_center_validation_spamurais_mixed(self, logger):
        """Test validation fails when some Spamurais have centers and some don't"""
        fixture = os.path.join(FIXTURES_DIR, 'invalid_spamurais_centers.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()

        is_valid, error_msg = allocator.validate_data()
        assert not is_valid
        assert 'SPAMURAIS' in error_msg
        assert 'some have Center' in error_msg


class TestDeduplication:
    """Test deduplication at various levels"""

    def test_input_deduplication(self, logger, temp_output):
        """Test duplicate phone numbers are removed from input"""
        fixture = os.path.join(FIXTURES_DIR, 'duplicates_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()

        # Original has 5 contacts, but 2 duplicates (1111111111 twice, 2222222222 twice)
        # After deduplication should have 3 unique contacts
        assert len(allocator.contacts) == 3

        # Check duplicate stats
        assert len(allocator.duplicate_stats['input_duplicates']) == 2

        # First occurrence should be kept
        phone_to_name = {c['Phone Number']: c['Name'] for c in allocator.contacts}
        assert phone_to_name['1111111111'] == 'Alice'  # Not 'Alice Duplicate'
        assert phone_to_name['2222222222'] == 'Bob'    # Not 'Bob Duplicate'

    def test_incremental_already_allocated_filter(self, logger, temp_output):
        """Test already-allocated contacts are skipped in incremental mode"""
        existing_file = os.path.join(FIXTURES_DIR, 'existing_allocation.xlsx')
        new_contacts_file = os.path.join(FIXTURES_DIR, 'incremental_new_contacts.xlsx')

        allocator = ContactAllocator(new_contacts_file, logger)
        allocator.load_data()
        allocator.validate_data()

        # Load existing allocations
        existing_allocations = allocator.load_existing_allocations(existing_file)
        allocator.incremental_mode = True
        allocator.existing_allocations = existing_allocations

        allocator.preprocess_data()
        allocator.filter_already_allocated()

        # New file has 5 contacts, 3 already allocated
        # Should only have 2 new contacts to allocate
        assert len(allocator.contacts) == 2

        # Should be David and Eve
        new_phones = {c['Phone Number'] for c in allocator.contacts}
        assert new_phones == {'4444444444', '5555555555'}

        # Check already_allocated stats
        assert len(allocator.duplicate_stats['already_allocated']) == 3


class TestIncrementalMode:
    """Test incremental allocation mode"""

    def test_load_existing_allocations(self, logger):
        """Test loading existing allocation file"""
        existing_file = os.path.join(FIXTURES_DIR, 'existing_allocation.xlsx')

        allocator = ContactAllocator('dummy', logger)
        existing = allocator.load_existing_allocations(existing_file)

        # Should have allocated_phones set
        assert 'allocated_phones' in existing
        assert len(existing['allocated_phones']) == 3
        assert '1111111111' in existing['allocated_phones']
        assert '2222222222' in existing['allocated_phones']
        assert '3333333333' in existing['allocated_phones']

        # Should have spamurai allocations
        assert 'spamurai_allocations' in existing
        assert 'Rahul' in existing['spamurai_allocations']
        assert 'Priya' in existing['spamurai_allocations']

        assert len(existing['spamurai_allocations']['Rahul']) == 2
        assert len(existing['spamurai_allocations']['Priya']) == 1

    def test_incremental_merge(self, logger, temp_output):
        """Test incremental mode merges old and new allocations"""
        existing_file = os.path.join(FIXTURES_DIR, 'existing_allocation.xlsx')
        new_contacts_file = os.path.join(FIXTURES_DIR, 'incremental_new_contacts.xlsx')

        allocator = ContactAllocator(new_contacts_file, logger)
        allocator.load_data()
        allocator.validate_data()

        # Enable incremental mode
        existing_allocations = allocator.load_existing_allocations(existing_file)
        allocator.incremental_mode = True
        allocator.existing_allocations = existing_allocations

        allocator.preprocess_data()
        allocator.filter_already_allocated()
        allocator.allocate()

        # Write to temp output
        allocator.write_to_excel(temp_output)

        # Read back and verify
        excel_file = pd.ExcelFile(temp_output)

        # Rahul should have 2 (old) + some (new) = more than 2
        rahul_df = pd.read_excel(excel_file, sheet_name='Rahul')
        assert len(rahul_df) >= 2

        # Priya should have 1 (old) + some (new) = more than 1
        priya_df = pd.read_excel(excel_file, sheet_name='Priya')
        assert len(priya_df) >= 1

        # Total should be 5 (3 old + 2 new)
        total = len(rahul_df) + len(priya_df)
        assert total == 5


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_missing_source_priority(self, logger, temp_output):
        """Test contacts with unknown sources get lowest priority"""
        fixture = os.path.join(FIXTURES_DIR, 'edge_cases.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()

        # Check that unknown sources got priority 999
        for contact in allocator.contacts:
            if contact['Source of Interest'] in ['', 'Unknown Source']:
                assert contact['priority'] == 999

    def test_special_characters_in_names(self, logger, temp_output):
        """Test special characters are handled correctly"""
        fixture = os.path.join(FIXTURES_DIR, 'edge_cases.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # All contacts should be allocated despite special characters
        total_allocated = sum(len(contacts) for contacts in result['spamurai_allocations'].values())
        assert total_allocated == 4

    def test_empty_contacts(self, logger):
        """Test handling of empty contacts list"""
        # Create empty fixture
        fixture_path = os.path.join(FIXTURES_DIR, 'empty_contacts.xlsx')

        contacts = pd.DataFrame({
            'Name': [],
            'Phone Number': [],
            'Center': [],
            'Source of Interest': []
        })

        spamurais = pd.DataFrame({
            'Name': ['Rahul'],
            'Center': ['']
        })

        priorities = pd.DataFrame({
            'Source of Interest': ['Workshop'],
            'Priority': [1]
        })

        with pd.ExcelWriter(fixture_path, engine='openpyxl') as writer:
            contacts.to_excel(writer, sheet_name='All Contacts', index=False)
            spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
            priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

        allocator = ContactAllocator(fixture_path, logger)
        allocator.load_data()

        is_valid, error_msg = allocator.validate_data()
        assert not is_valid
        assert 'No contacts found' in error_msg

        # Cleanup
        os.remove(fixture_path)

    def test_single_spamurai(self, logger, temp_output):
        """Test allocation with only one Spamurai"""
        # Create fixture with single Spamurai
        fixture_path = os.path.join(FIXTURES_DIR, 'single_spamurai.xlsx')

        contacts = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Phone Number': ['1111111111', '2222222222', '3333333333'],
            'Center': ['', '', ''],
            'Source of Interest': ['Workshop', 'Workshop', 'Workshop']
        })

        spamurais = pd.DataFrame({
            'Name': ['Rahul'],
            'Center': ['']
        })

        priorities = pd.DataFrame({
            'Source of Interest': ['Workshop'],
            'Priority': [1]
        })

        with pd.ExcelWriter(fixture_path, engine='openpyxl') as writer:
            contacts.to_excel(writer, sheet_name='All Contacts', index=False)
            spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
            priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

        allocator = ContactAllocator(fixture_path, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # All 3 should go to Rahul
        assert len(result['spamurai_allocations']['Rahul']) == 3

        # Cleanup
        os.remove(fixture_path)


class TestLargeScale:
    """Test performance with large datasets"""

    def test_large_scale_allocation(self, logger, temp_output):
        """Test allocation with 100 contacts and 5 Spamurais"""
        fixture = os.path.join(FIXTURES_DIR, 'large_scale_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # Should allocate all 100 contacts
        total_allocated = sum(len(contacts) for contacts in result['spamurai_allocations'].values())

        # Note: Some may be unallocated if centers don't match
        total_contacts = total_allocated + len(result['unallocated'])
        assert total_contacts == 100

        # Write Excel
        allocator.write_to_excel(temp_output)
        assert os.path.exists(temp_output)


class TestRoundRobinDistribution:
    """Test round-robin distribution is fair"""

    def test_even_distribution(self, logger, temp_output):
        """Test contacts are distributed evenly across Spamurais"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        allocator = ContactAllocator(fixture, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # Get allocation counts
        counts = [len(contacts) for contacts in result['spamurai_allocations'].values()]

        # With 6 contacts and 2 Spamurais, should be [3, 3]
        assert counts == [3, 3]

    def test_uneven_distribution(self, logger, temp_output):
        """Test round-robin handles uneven division"""
        # Create fixture with 7 contacts and 2 Spamurais
        fixture_path = os.path.join(FIXTURES_DIR, 'uneven_distribution.xlsx')

        contacts = pd.DataFrame({
            'Name': ['A', 'B', 'C', 'D', 'E', 'F', 'G'],
            'Phone Number': ['1111111111', '2222222222', '3333333333', '4444444444', '5555555555', '6666666666', '7777777777'],
            'Center': ['', '', '', '', '', '', ''],
            'Source of Interest': ['Workshop'] * 7
        })

        spamurais = pd.DataFrame({
            'Name': ['Rahul', 'Priya'],
            'Center': ['', '']
        })

        priorities = pd.DataFrame({
            'Source of Interest': ['Workshop'],
            'Priority': [1]
        })

        with pd.ExcelWriter(fixture_path, engine='openpyxl') as writer:
            contacts.to_excel(writer, sheet_name='All Contacts', index=False)
            spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
            priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

        allocator = ContactAllocator(fixture_path, logger)
        allocator.load_data()
        allocator.validate_data()
        allocator.preprocess_data()
        result = allocator.allocate()

        # Get allocation counts
        counts = [len(contacts) for contacts in result['spamurai_allocations'].values()]

        # Should be [4, 3] or [3, 4] (difference of at most 1)
        assert max(counts) - min(counts) <= 1
        assert sum(counts) == 7

        # Cleanup
        os.remove(fixture_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
