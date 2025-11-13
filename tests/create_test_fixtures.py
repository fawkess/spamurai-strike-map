#!/usr/bin/env python3
"""
Script to create test fixture Excel files
Run this once to generate test data files
"""

import pandas as pd
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
os.makedirs(FIXTURES_DIR, exist_ok=True)


def create_basic_allocation_fixture():
    """Basic allocation test - no centers, simple priority"""

    # All Contacts
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank'],
        'Phone Number': ['1111111111', '2222222222', '3333333333', '4444444444', '5555555555', '6666666666'],
        'Center': [''] * 6,
        'Source of Interest': ['Workshop', 'Website', 'Workshop', 'Social Media', 'Workshop', 'Website']
    })

    # Spamurais
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['', '']
    })

    # Source Priorities
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website', 'Social Media'],
        'Priority': [1, 2, 3]
    })

    filepath = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_center_based_fixture():
    """Center-based allocation test"""

    # All Contacts
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry'],
        'Phone Number': ['1111111111', '2222222222', '3333333333', '4444444444', '5555555555', '6666666666', '7777777777', '8888888888'],
        'Center': ['Mumbai', 'Delhi', 'Mumbai', 'Delhi', 'Mumbai', 'Delhi', 'Bangalore', 'Mumbai'],
        'Source of Interest': ['Workshop', 'Workshop', 'Website', 'Website', 'Workshop', 'Social Media', 'Workshop', 'Website']
    })

    # Spamurais
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya', 'Arjun'],
        'Center': ['Mumbai', 'Delhi', 'Mumbai']
    })

    # Source Priorities
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website', 'Social Media'],
        'Priority': [1, 2, 3]
    })

    filepath = os.path.join(FIXTURES_DIR, 'center_based_allocation.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_duplicates_fixture():
    """Test duplicate handling"""

    # All Contacts (with duplicates)
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Alice Duplicate', 'Bob', 'Charlie', 'Bob Duplicate'],
        'Phone Number': ['1111111111', '1111111111', '2222222222', '3333333333', '2222222222'],
        'Center': ['', '', '', '', ''],
        'Source of Interest': ['Workshop', 'Website', 'Workshop', 'Website', 'Social Media']
    })

    # Spamurais
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['', '']
    })

    # Source Priorities
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website', 'Social Media'],
        'Priority': [1, 2, 3]
    })

    filepath = os.path.join(FIXTURES_DIR, 'duplicates_allocation.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_unallocated_fixture():
    """Test unallocated contacts (center mismatch)"""

    # All Contacts
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'David'],
        'Phone Number': ['1111111111', '2222222222', '3333333333', '4444444444'],
        'Center': ['Mumbai', 'Delhi', 'Bangalore', 'Mumbai'],
        'Source of Interest': ['Workshop', 'Workshop', 'Workshop', 'Website']
    })

    # Spamurais (no Bangalore Spamurai)
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['Mumbai', 'Delhi']
    })

    # Source Priorities
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website'],
        'Priority': [1, 2]
    })

    filepath = os.path.join(FIXTURES_DIR, 'unallocated_contacts.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_validation_error_fixtures():
    """Create fixtures for validation error testing"""

    # Fixture 1: Some contacts have center, some don't
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Phone Number': ['1111111111', '2222222222', '3333333333'],
        'Center': ['Mumbai', '', 'Delhi'],  # Mixed
        'Source of Interest': ['Workshop', 'Workshop', 'Workshop']
    })

    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['Mumbai', 'Delhi']
    })

    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop'],
        'Priority': [1]
    })

    filepath = os.path.join(FIXTURES_DIR, 'invalid_contacts_centers.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")

    # Fixture 2: Some Spamurais have center, some don't
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Phone Number': ['1111111111', '2222222222', '3333333333'],
        'Center': ['Mumbai', 'Mumbai', 'Delhi'],
        'Source of Interest': ['Workshop', 'Workshop', 'Workshop']
    })

    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya', 'Arjun'],
        'Center': ['Mumbai', '', 'Delhi']  # Mixed
    })

    filepath = os.path.join(FIXTURES_DIR, 'invalid_spamurais_centers.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_incremental_existing_allocation():
    """Create existing allocation file for incremental mode testing"""

    # INPUT TABS
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Phone Number': ['1111111111', '2222222222', '3333333333'],
        'Center': ['', '', ''],
        'Source of Interest': ['Workshop', 'Workshop', 'Website']
    })

    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['', '']
    })

    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website'],
        'Priority': [1, 2]
    })

    # OUTPUT TABS - Previous allocations
    summary = pd.DataFrame({
        'Metric': ['Total Contacts', 'Successfully Allocated', 'Unallocated'],
        'Count': [3, 3, 0]
    })

    rahul_contacts = pd.DataFrame({
        'Name': ['Alice', 'Charlie'],
        'Phone Number': ['1111111111', '3333333333']
    })

    priya_contacts = pd.DataFrame({
        'Name': ['Bob'],
        'Phone Number': ['2222222222']
    })

    filepath = os.path.join(FIXTURES_DIR, 'existing_allocation.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Input tabs
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

        # Output tabs
        summary.to_excel(writer, sheet_name='Summary', index=False)
        rahul_contacts.to_excel(writer, sheet_name='Rahul', index=False)
        priya_contacts.to_excel(writer, sheet_name='Priya', index=False)

    print(f"✅ Created: {filepath}")


def create_incremental_new_contacts():
    """Create new contacts file for incremental testing"""

    # All Contacts (includes old + new)
    contacts = pd.DataFrame({
        'Name': ['Alice', 'Bob', 'Charlie', 'David', 'Eve'],
        'Phone Number': ['1111111111', '2222222222', '3333333333', '4444444444', '5555555555'],
        'Center': ['', '', '', '', ''],
        'Source of Interest': ['Workshop', 'Workshop', 'Website', 'Workshop', 'Website']
    })

    # Spamurais
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['', '']
    })

    # Source Priorities
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website'],
        'Priority': [1, 2]
    })

    filepath = os.path.join(FIXTURES_DIR, 'incremental_new_contacts.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_large_scale_fixture():
    """Create large dataset for performance testing"""

    # 100 contacts
    names = [f'Contact_{i}' for i in range(1, 101)]
    phones = [f'{str(i).zfill(10)}' for i in range(1000000000, 1000000100)]
    centers = ['Mumbai', 'Delhi', 'Bangalore'] * 33 + ['Mumbai']
    sources = ['Workshop', 'Website', 'Social Media', 'Event'] * 25

    contacts = pd.DataFrame({
        'Name': names,
        'Phone Number': phones,
        'Center': centers,
        'Source of Interest': sources
    })

    # 5 Spamurais
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya', 'Arjun', 'Sneha', 'Vikram'],
        'Center': ['Mumbai', 'Delhi', 'Mumbai', 'Bangalore', 'Delhi']
    })

    # Priorities
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Event', 'Website', 'Social Media'],
        'Priority': [1, 2, 3, 4]
    })

    filepath = os.path.join(FIXTURES_DIR, 'large_scale_allocation.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


def create_edge_cases_fixture():
    """Edge cases: missing sources, special characters, etc."""

    # All Contacts with edge cases
    contacts = pd.DataFrame({
        'Name': ['Alice 🥷', 'Bob O\'Brien', 'Charlie-Dave', 'Eve & Co'],
        'Phone Number': ['1111111111', '2222222222', '3333333333', '4444444444'],
        'Center': ['', '', '', ''],
        'Source of Interest': ['Workshop', 'Unknown Source', '', 'Website']
    })

    # Spamurais
    spamurais = pd.DataFrame({
        'Name': ['Rahul', 'Priya'],
        'Center': ['', '']
    })

    # Source Priorities (doesn't include all sources)
    priorities = pd.DataFrame({
        'Source of Interest': ['Workshop', 'Website'],
        'Priority': [1, 2]
    })

    filepath = os.path.join(FIXTURES_DIR, 'edge_cases.xlsx')
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        contacts.to_excel(writer, sheet_name='All Contacts', index=False)
        spamurais.to_excel(writer, sheet_name='Spamurais', index=False)
        priorities.to_excel(writer, sheet_name='Source Priorities', index=False)

    print(f"✅ Created: {filepath}")


if __name__ == '__main__':
    print("Creating test fixtures...")
    print("=" * 70)

    create_basic_allocation_fixture()
    create_center_based_fixture()
    create_duplicates_fixture()
    create_unallocated_fixture()
    create_validation_error_fixtures()
    create_incremental_existing_allocation()
    create_incremental_new_contacts()
    create_large_scale_fixture()
    create_edge_cases_fixture()

    print("=" * 70)
    print("✅ All test fixtures created successfully!")
    print(f"Location: {FIXTURES_DIR}")
