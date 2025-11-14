"""
Pytest configuration and custom reporting
"""

import pytest
from collections import defaultdict


# Store test results for health reporting
test_results = defaultdict(lambda: {'passed': [], 'failed': [], 'skipped': []})


def pytest_configure(config):
    """Configure pytest with custom markers and settings"""
    config.addinivalue_line(
        "markers", "unit: Unit tests for core functionality"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for CLI and workflows"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests with large datasets"
    )


def pytest_collection_modifyitems(config, items):
    """Auto-mark tests based on module names"""
    for item in items:
        # Auto-mark unit tests
        if "test_contact_allocator" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "test_google_sheets_client" in item.nodeid:
            item.add_marker(pytest.mark.unit)

        # Auto-mark integration tests
        if "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Auto-mark slow tests
        if "large" in item.name.lower() or "performance" in item.name.lower():
            item.add_marker(pytest.mark.slow)


def pytest_runtest_logreport(report):
    """Collect test results for health summary"""
    if report.when == 'call':
        # Extract category from test path
        parts = report.nodeid.split('::')
        if len(parts) >= 2:
            test_file = parts[0].split('/')[-1].replace('.py', '')
            test_class = parts[1] if len(parts) >= 2 else 'Other'
            category = f"{test_file}/{test_class}"

            if report.outcome == 'passed':
                test_results[category]['passed'].append(report.nodeid)
            elif report.outcome == 'failed':
                test_results[category]['failed'].append({
                    'test': report.nodeid,
                    'error': str(report.longrepr) if hasattr(report, 'longrepr') else 'Unknown error'
                })
            elif report.outcome == 'skipped':
                test_results[category]['skipped'].append(report.nodeid)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print custom health summary at end of test run"""
    terminalreporter.write_sep("=", "SPAMURAI Test Health Summary", bold=True)

    # Collect overall stats
    total_passed = 0
    total_failed = 0
    total_skipped = 0

    # Group by functionality
    functionality_status = {}

    for category, results in sorted(test_results.items()):
        passed = len(results['passed'])
        failed = len(results['failed'])
        skipped = len(results['skipped'])
        total = passed + failed + skipped

        total_passed += passed
        total_failed += failed
        total_skipped += skipped

        if total > 0:
            status = "✅ HEALTHY" if failed == 0 else "❌ BROKEN"
            percentage = (passed / total) * 100 if total > 0 else 0
            functionality_status[category] = {
                'status': status,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'total': total,
                'percentage': percentage
            }

    # Print functionality health
    terminalreporter.write_line("")
    terminalreporter.write_line("📊 Functionality Health:", bold=True)
    terminalreporter.write_line("-" * 80)

    for category, stats in sorted(functionality_status.items()):
        status_icon = stats['status']
        percentage = stats['percentage']
        passed = stats['passed']
        failed = stats['failed']
        total = stats['total']

        terminalreporter.write_line(
            f"{status_icon}  {category:50s} {passed}/{total} ({percentage:5.1f}%)"
        )

        # Show failed test details for broken functionality
        if failed > 0:
            results = test_results[category]
            for fail in results['failed'][:3]:  # Show first 3 failures
                test_name = fail['test'].split('::')[-1]
                terminalreporter.write_line(f"      ↳ {test_name}", red=True)

    # Overall health score
    terminalreporter.write_line("")
    terminalreporter.write_line("-" * 80)
    total_tests = total_passed + total_failed + total_skipped
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0

    if total_failed == 0:
        health_status = "🎉 EXCELLENT"
        color = "green"
    elif overall_percentage >= 80:
        health_status = "✅ GOOD"
        color = "green"
    elif overall_percentage >= 60:
        health_status = "⚠️  FAIR"
        color = "yellow"
    else:
        health_status = "❌ POOR"
        color = "red"

    terminalreporter.write_line(
        f"Overall Health: {health_status} - {total_passed}/{total_tests} tests passing ({overall_percentage:.1f}%)",
        **{color: True, 'bold': True}
    )

    # Broken functionality summary
    if total_failed > 0:
        terminalreporter.write_line("")
        terminalreporter.write_line("🔧 Broken Functionality:", red=True, bold=True)
        for category, stats in sorted(functionality_status.items()):
            if stats['failed'] > 0:
                terminalreporter.write_line(f"   • {category} ({stats['failed']} failures)", red=True)

    # What's working summary
    if total_passed > 0:
        terminalreporter.write_line("")
        terminalreporter.write_line("✅ Working Functionality:", green=True, bold=True)
        for category, stats in sorted(functionality_status.items()):
            if stats['failed'] == 0 and stats['total'] > 0:
                terminalreporter.write_line(f"   • {category} (all {stats['total']} tests passing)", green=True)

    terminalreporter.write_line("")
