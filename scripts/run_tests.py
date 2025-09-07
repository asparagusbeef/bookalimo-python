#!/usr/bin/env python3
"""
Comprehensive test runner for Bookalimo SDK.

This script provides various test execution modes with detailed reporting
and handles different testing scenarios for the SDK.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], description: str, check: bool = True) -> int:
    """Run a command and return the exit code."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=check)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return e.returncode
    except FileNotFoundError as e:
        print(f"❌ {description} - COMMAND NOT FOUND: {e}")
        return 1


def setup_environment():
    """Set up the test environment."""
    # Set up environment variables for testing
    test_env = {
        'PYTHONPATH': str(Path.cwd() / 'src'),
        'BOOKALIMO_TEST_MODE': '1',
    }
    
    # Add Google Places API key if available
    if 'GOOGLE_PLACES_API_KEY' in os.environ:
        test_env['GOOGLE_PLACES_API_KEY'] = os.environ['GOOGLE_PLACES_API_KEY']
    else:
        test_env['GOOGLE_PLACES_API_KEY'] = 'test-google-places-key'
    
    # Add Bookalimo testing credentials if available
    if 'BOOKALIMO_TESTING_USER' in os.environ:
        test_env['BOOKALIMO_TESTING_USER'] = os.environ['BOOKALIMO_TESTING_USER']
    
    # Update environment
    os.environ.update(test_env)
    
    print("🔧 Test environment configured")
    for key, value in test_env.items():
        if 'KEY' in key and value != 'test-google-places-key':
            print(f"   {key}: ***REDACTED***")
        elif 'BOOKALIMO_TESTING_USER' in key:
            print(f"   {key}: ***REDACTED***")
        else:
            print(f"   {key}: {value}")


def run_linting() -> int:
    """Run linting checks."""
    commands = [
        (['ruff', 'check', '.'], "Ruff linting"),
        (['ruff', 'format', '--check', '.'], "Ruff formatting check"),
    ]
    
    failed = 0
    for cmd, description in commands:
        if run_command(cmd, description, check=False) != 0:
            failed += 1
    
    return failed


def run_type_checking() -> int:
    """Run type checking."""
    return run_command(
        ['mypy', 'src/bookalimo', '--config-file', 'pyproject.toml'],
        "MyPy type checking",
        check=False
    )


def run_security_checks() -> int:
    """Run security checks."""
    commands = [
        (['bandit', '-r', 'src/', '-f', 'text'], "Bandit security scan"),
        (['safety', 'check'], "Safety vulnerability check"),
    ]
    
    failed = 0
    for cmd, description in commands:
        if run_command(cmd, description, check=False) != 0:
            failed += 1
    
    return failed


def run_tests(
    mode: str = "standard",
    coverage: bool = True,
    markers: Optional[str] = None,
    verbose: bool = True,
    fail_fast: bool = False
) -> int:
    """Run tests with specified configuration."""
    
    cmd = ['pytest']
    
    if verbose:
        cmd.append('-v')
    
    if fail_fast:
        cmd.extend(['--maxfail', '1'])
    
    if coverage:
        cmd.extend([
            '--cov=bookalimo',
            '--cov-report=term-missing',
            '--cov-report=html',
            '--cov-report=xml'
        ])
    
    if markers:
        cmd.extend(['-m', markers])
    
    # Configure test selection based on mode
    if mode == "fast":
        cmd.extend(['-m', 'not slow and not integration and not performance'])
        cmd.extend(['--maxfail', '5'])
    elif mode == "unit":
        cmd.extend(['-m', 'not integration and not performance and not slow'])
    elif mode == "integration":
        cmd.extend(['-m', 'integration'])
    elif mode == "performance":
        cmd.extend(['-m', 'performance'])
        cmd.extend(['--durations=10'])
    elif mode == "noplaces":
        cmd.extend(['-k', 'not test_google_places and not places'])
    elif mode == "all":
        # Run all tests including slow ones
        pass
    
    # Add test directory
    cmd.append('tests/')
    
    description = f"Running tests (mode: {mode})"
    return run_command(cmd, description, check=False)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for Bookalimo SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Modes:
  standard     - Standard test suite with coverage
  fast         - Quick tests, no integration/performance tests  
  unit         - Unit tests only
  integration  - Integration tests only
  performance  - Performance and load tests only
  noplaces     - Tests without Google Places integration
  all          - All tests including slow integration tests

Examples:
  python scripts/run_tests.py                    # Standard tests
  python scripts/run_tests.py --mode fast       # Quick test run
  python scripts/run_tests.py --lint --typecheck # Code quality only
  python scripts/run_tests.py --all             # Full validation
        """
    )
    
    # Test execution options
    parser.add_argument(
        '--mode', 
        choices=['standard', 'fast', 'unit', 'integration', 'performance', 'noplaces', 'all'],
        default='standard',
        help='Test execution mode'
    )
    
    parser.add_argument('--no-coverage', action='store_true', help='Disable coverage reporting')
    parser.add_argument('--fail-fast', action='store_true', help='Stop on first failure')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    parser.add_argument('-m', '--markers', help='Pytest markers to select tests')
    
    # Code quality options
    parser.add_argument('--lint', action='store_true', help='Run linting checks')
    parser.add_argument('--typecheck', action='store_true', help='Run type checking')
    parser.add_argument('--security', action='store_true', help='Run security checks')
    
    # Workflow options
    parser.add_argument('--pre-commit', action='store_true', help='Run pre-commit checks')
    parser.add_argument('--ci', action='store_true', help='Run CI pipeline checks')
    parser.add_argument('--all', action='store_true', help='Run all checks and tests')
    
    args = parser.parse_args()
    
    # Set up environment
    setup_environment()
    
    print("\n🧪 Bookalimo SDK Test Runner")
    print("=" * 60)
    
    failed_checks = 0
    
    # Handle workflow modes
    if args.all or args.ci:
        print("🔄 Running complete validation pipeline...")
        if run_linting() > 0:
            failed_checks += 1
        if run_type_checking() > 0:
            failed_checks += 1
        if run_security_checks() > 0:
            failed_checks += 1
        if run_tests(mode='all', coverage=not args.no_coverage, verbose=not args.quiet, fail_fast=args.fail_fast) > 0:
            failed_checks += 1
    
    elif args.pre_commit:
        print("🔄 Running pre-commit checks...")
        # Auto-format first
        run_command(['ruff', 'format', '.'], "Auto-formatting code", check=False)
        
        if run_linting() > 0:
            failed_checks += 1
        if run_type_checking() > 0:
            failed_checks += 1
        if run_tests(mode='fast', coverage=not args.no_coverage, verbose=not args.quiet, fail_fast=True) > 0:
            failed_checks += 1
    
    else:
        # Individual check modes
        if args.lint:
            if run_linting() > 0:
                failed_checks += 1
        
        if args.typecheck:
            if run_type_checking() > 0:
                failed_checks += 1
        
        if args.security:
            if run_security_checks() > 0:
                failed_checks += 1
        
        # Run tests if no specific check flags or if any test-related args
        if not any([args.lint, args.typecheck, args.security]) or args.mode or args.markers:
            if run_tests(
                mode=args.mode,
                coverage=not args.no_coverage,
                markers=args.markers,
                verbose=not args.quiet,
                fail_fast=args.fail_fast
            ) > 0:
                failed_checks += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    if failed_checks == 0:
        print("🎉 ALL CHECKS PASSED! ✅")
        print("\nYour code is ready for:")
        print("  • Commit and push")
        print("  • Pull request creation")  
        print("  • Production deployment")
        sys.exit(0)
    else:
        print(f"❌ {failed_checks} CHECK(S) FAILED!")
        print("\nPlease fix the issues above before:")
        print("  • Committing changes")
        print("  • Creating pull requests")
        print("  • Deploying to production")
        sys.exit(1)


if __name__ == "__main__":
    main()