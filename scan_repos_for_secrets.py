#!/usr/bin/env python3
"""
GitHub Repository Secret Scanner
Scans all original (non-forked) repositories for exposed API keys and secrets
"""

import os
import requests
import re
import json
from typing import List, Dict, Set

# GitHub API token — never hardcode; export GITHUB_TOKEN before running
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
if not GITHUB_TOKEN:
    raise SystemExit("Set GITHUB_TOKEN in the environment (do not commit tokens).")
GITHUB_API = "https://api.github.com"

# Patterns to search for
SECRET_PATTERNS = {
    'Gemini API Key': r'AIzaSy[A-Za-z0-9_-]{33}',
    'GitHub Token': r'ghp_[A-Za-z0-9]{36}',
    'AWS Access Key': r'AKIA[0-9A-Z]{16}',
    'OpenAI API Key': r'sk-[A-Za-z0-9]{48}',
    'Generic API Key': r'api[_-]?key["\']?\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})',
    'Password in Code': r'password["\']?\s*[:=]\s*["\']([^"\']{8,})',
    'SMTP Password': r'smtp[_-]?password["\']?\s*[:=]\s*["\']([^"\']{8,})',
    'Database URL': r'postgresql://[^:]+:[^@]+@[^/]+',
    'JWT Secret': r'jwt[_-]?secret["\']?\s*[:=]\s*["\']([^"\']{20,})',
}

def get_user_repos() -> List[Dict]:
    """Get all non-forked repositories"""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(f"{GITHUB_API}/user/repos?per_page=100&type=owner", headers=headers)
    
    if response.status_code != 200:
        print(f"Error fetching repos: {response.status_code}")
        return []
    
    repos = response.json()
    # Filter out forked repos
    return [repo for repo in repos if not repo['fork']]

def search_repo_code(repo_name: str, pattern: str, secret_type: str) -> List[Dict]:
    """Search for pattern in repository code"""
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # GitHub Code Search API
    query = f"{pattern} repo:Zaferturan/{repo_name}"
    url = f"{GITHUB_API}/search/code?q={query}"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            results = response.json()
            if results.get('total_count', 0) > 0:
                return [{
                    'type': secret_type,
                    'repo': repo_name,
                    'file': item['path'],
                    'url': item['html_url']
                } for item in results.get('items', [])]
    except Exception as e:
        print(f"Error searching {repo_name}: {e}")
    
    return []

def scan_all_repos():
    """Scan all repositories for secrets"""
    print("=" * 80)
    print("🔍 GITHUB REPOSITORY SECRET SCANNER")
    print("=" * 80)
    
    repos = get_user_repos()
    print(f"\n📦 Scanning {len(repos)} original repositories...\n")
    
    all_findings = []
    
    for repo in repos:
        repo_name = repo['name']
        visibility = "🔒 Private" if repo['private'] else "🌐 Public"
        
        print(f"Scanning: {repo_name} {visibility}")
        
        # Only scan public repos via API (private repos need different approach)
        if not repo['private']:
            for secret_type, pattern in SECRET_PATTERNS.items():
                findings = search_repo_code(repo_name, pattern, secret_type)
                all_findings.extend(findings)
    
    print("\n" + "=" * 80)
    print("📊 SCAN RESULTS")
    print("=" * 80)
    
    if all_findings:
        print(f"\n⚠️  Found {len(all_findings)} potential secrets:\n")
        for finding in all_findings:
            print(f"❌ {finding['type']}")
            print(f"   Repo: {finding['repo']}")
            print(f"   File: {finding['file']}")
            print(f"   URL: {finding['url']}")
            print()
    else:
        print("\n✅ No obvious secrets found in public repositories!")
        print("\n💡 Note: This scanner only checks public repos via GitHub API.")
        print("   Private repos and local files need manual review.")
    
    print("=" * 80)

if __name__ == "__main__":
    scan_all_repos()
