#!/usr/bin/env python3
"""
Test runner script for the File Organizer application.
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", coverage=True, verbose=True, markers=None):
    """Run tests with specified options."""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test paths based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "integration":
        cmd.append("tests/integration/")
    elif test_type == "all":
        cmd.append("tests/")
    else:
        print(f"Unknown test type: {test_type}")
        return 1
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=.",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-fail-under=70"
        ])
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add markers if specified
    if markers:
        cmd.extend(["-m", markers])
    
    # Add additional options
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--strict-config"
    ])
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 130
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    
    cmd = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("Test dependencies installed successfully")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return 1

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run File Organizer tests")
    
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Disable coverage reporting"
    )
    
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    parser.add_argument(
        "--markers",
        help="Run tests with specific pytest markers (e.g., 'not slow')"
    )
    
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install test dependencies before running tests"
    )
    
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Run only fast tests (excludes integration and slow tests)"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        exit_code = install_test_dependencies()
        if exit_code != 0:
            return exit_code
    
    # Set markers for fast tests
    if args.fast:
        args.markers = "not integration and not slow"
        args.type = "unit"
    
    # Run tests
    exit_code = run_tests(
        test_type=args.type,
        coverage=not args.no_coverage,
        verbose=not args.quiet,
        markers=args.markers
    )
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
        if not args.no_coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())