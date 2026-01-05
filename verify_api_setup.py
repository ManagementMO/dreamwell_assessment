"""
Dreamwell YouTube API Setup Verification Script (Python version)
Cross-platform alternative to verify_api_setup.sh
"""

import os
import sys
import json
import requests
from pathlib import Path


def print_header(text):
    """Print section header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)


def check_mark(passed):
    """Return check mark or X based on status"""
    return "✓" if passed else "✗"


def main():
    print_header("Dreamwell YouTube API Setup Verification")

    all_good = True
    issues = []

    # 1. Check .env file
    print("\n1. Checking .env file...")
    env_path = Path(".env")

    if env_path.exists():
        print(f"   {check_mark(True)} .env file exists")

        with open(env_path) as f:
            env_content = f.read()

        # Check YouTube API key
        youtube_key = None
        for line in env_content.split("\n"):
            if line.startswith("YOUTUBE_API_KEY="):
                youtube_key = line.split("=", 1)[1].strip()
                break

        if not youtube_key:
            print(f"   {check_mark(False)} YOUTUBE_API_KEY is empty in .env")
            issues.append("Add YOUTUBE_API_KEY to .env")
            all_good = False
        elif youtube_key == "your_youtube_api_key_here":
            print(f"   ⚠ YOUTUBE_API_KEY is still placeholder")
            print(f"      → Update with real API key for YouTube API testing")
            print(f"      → Fallback will be used (local JSON data)")
            issues.append("Replace placeholder YOUTUBE_API_KEY with real key")
            all_good = False
        else:
            print(f"   {check_mark(True)} YOUTUBE_API_KEY is configured")
            print(f"      Key: {youtube_key[:20]}...")

        # Check OpenAI key
        openai_key = None
        for line in env_content.split("\n"):
            if line.startswith("OPENAI_API_KEY="):
                openai_key = line.split("=", 1)[1].strip()
                break

        if not openai_key:
            print(f"   {check_mark(False)} OPENAI_API_KEY is empty in .env")
            issues.append("Add OPENAI_API_KEY to .env")
            all_good = False
        elif not openai_key.startswith("sk-"):
            print(f"   ⚠ OPENAI_API_KEY might be invalid (doesn't start with 'sk-')")
            issues.append("Verify OPENAI_API_KEY is correct")
            all_good = False
        else:
            print(f"   {check_mark(True)} OPENAI_API_KEY is configured")
    else:
        print(f"   {check_mark(False)} .env file not found")
        print(f"      → Copy .env.example to .env and add your API keys")
        issues.append("Create .env file from .env.example")
        all_good = False

    # 2. Check if backend is running
    print("\n2. Checking if backend is running...")
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            print(f"   {check_mark(True)} Backend is running on http://localhost:8000")

            # 3. Test health endpoint
            print("\n3. Testing API health endpoint...")
            health_response = requests.get("http://localhost:8000/api/health", timeout=2)

            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   {check_mark(True)} Health endpoint responding")

                # YouTube API status
                youtube_status = health_data["components"]["youtube_api"]["status"]
                will_use = health_data["components"]["youtube_api"]["will_use"]

                if youtube_status == "configured":
                    print(f"   {check_mark(True)} YouTube API: configured")
                    print(f"      Will use: {will_use}")
                else:
                    print(f"   ⚠ YouTube API: not configured")
                    print(f"      Will use: local_fallback")

                # MCP status
                mcp_status = health_data["components"]["mcp_server"]["status"]
                tool_count = health_data["components"]["mcp_server"]["tools_available"]

                if mcp_status == "up":
                    print(f"   {check_mark(True)} MCP Server: running ({tool_count} tools available)")
                else:
                    print(f"   {check_mark(False)} MCP Server: down")
                    issues.append("MCP server is not running")
                    all_good = False
            else:
                print(f"   {check_mark(False)} Health endpoint not responding")
                issues.append("Health endpoint error")
                all_good = False
        else:
            print(f"   {check_mark(False)} Backend responded with status {response.status_code}")
            issues.append("Backend not healthy")
            all_good = False
    except requests.exceptions.ConnectionError:
        print(f"   {check_mark(False)} Backend is not running")
        print(f"      → Start with: python backend_main.py")
        issues.append("Start backend server")
        all_good = False
    except requests.exceptions.Timeout:
        print(f"   {check_mark(False)} Backend request timed out")
        issues.append("Backend not responding")
        all_good = False

    # 4. Check Python dependencies
    print("\n4. Checking Python dependencies...")
    try:
        import mcp
        import openai
        import googleapiclient

        print(f"   {check_mark(True)} All Python packages installed")
    except ImportError as e:
        print(f"   ⚠ Some Python packages might be missing: {e}")
        print(f"      → Run: pip install -r requirements.txt")
        issues.append("Install missing Python packages")

    # 5. Check test data files
    print("\n5. Checking test data files...")

    email_fixtures = Path("data/email_fixtures.json")
    if email_fixtures.exists():
        with open(email_fixtures) as f:
            emails = json.load(f)
        email_count = len(emails)
        print(f"   {check_mark(True)} email_fixtures.json found ({email_count} emails)")

        # Check for API test emails
        api_test_count = sum(1 for email in emails if "REAL API TEST" in email.get("influencer_name", ""))
        if api_test_count > 0:
            print(f"   {check_mark(True)} Found {api_test_count} test emails with real YouTube channels")
    else:
        print(f"   {check_mark(False)} email_fixtures.json not found")
        issues.append("Missing email_fixtures.json")
        all_good = False

    youtube_profiles = Path("data/youtube_profiles.json")
    if youtube_profiles.exists():
        with open(youtube_profiles) as f:
            profiles = json.load(f)
        profile_count = len(profiles)
        print(f"   {check_mark(True)} youtube_profiles.json found ({profile_count} profiles)")
    else:
        print(f"   {check_mark(False)} youtube_profiles.json not found")
        issues.append("Missing youtube_profiles.json")
        all_good = False

    # Final summary
    print_header("Summary")

    if all_good:
        print("\n✓ All checks passed!\n")
        print("Ready to test YouTube API integration:")
        print("  1. Run: python test_youtube_api.py")
        print("  2. Or test via HTTP: curl http://localhost:8000/api/test-youtube/@Fireship")
        print("  3. Or use the frontend UI at http://localhost:5173")
    else:
        print("\n⚠ Some issues detected\n")
        print("Issues to fix:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")

        print("\nQuick fix steps:")
        print("  1. Add YOUTUBE_API_KEY to .env file")
        print("  2. Restart backend: python backend_main.py")
        print("  3. Run verification again: python verify_api_setup.py")

    print("=" * 60)

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
