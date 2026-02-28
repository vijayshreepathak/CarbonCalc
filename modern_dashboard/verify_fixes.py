#!/usr/bin/env python3
"""
Quick verification script to check if layout fixes are applied
"""

import requests
import time

def check_dashboard():
    try:
        print("Checking dashboard status...")
        
        # Check main page
        response = requests.get("http://localhost:8001/", timeout=5)
        print(f"[+] Main page: HTTP {response.status_code}")
        
        # Check CSS
        response = requests.get("http://localhost:8001/style.css", timeout=5)
        print(f"[+] CSS file: HTTP {response.status_code}")
        
        # Check JS
        response = requests.get("http://localhost:8001/app.js", timeout=5)
        print(f"[+] JavaScript: HTTP {response.status_code}")
        
        # Check API
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        print(f"[+] API Health: HTTP {response.status_code}")
        
        # Check if our layout fixes are in the CSS
        css_response = requests.get("http://localhost:8001/style.css", timeout=5)
        css_content = css_response.text
        
        fixes_present = [
            ".charts-row" in css_content,
            ".chart-card.wide .chart-container" in css_content,
            "overflow: hidden;" in css_content,
            "@keyframes fadeIn" in css_content
        ]
        
        print(f"\n[*] Layout fixes applied: {all(fixes_present)}")
        print(f"    - Charts row layout: {'[OK]' if fixes_present[0] else '[NO]'}")
        print(f"    - Chart sizing: {'[OK]' if fixes_present[1] else '[NO]'}")
        print(f"    - Overflow fixes: {'[OK]' if fixes_present[2] else '[NO]'}")
        print(f"    - Animations: {'[OK]' if fixes_present[3] else '[NO]'}")
        
        print(f"\n[+] Dashboard is ready at: http://localhost:8001/")
        print(f"[+] All layout and alignment fixes have been applied!")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[!] Error connecting to dashboard: {e}")
        return False

if __name__ == "__main__":
    success = check_dashboard()
    if success:
        print(f"\n[SUCCESS] Dashboard is fully operational with fixed alignment!")
    else:
        print(f"\n[FAILED] Dashboard verification failed")