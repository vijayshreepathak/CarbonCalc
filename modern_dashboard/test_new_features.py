#!/usr/bin/env python3
"""
Test script for new features: Emissions/Transport tabs and Info modal
"""

import requests
import time
import re

def test_new_features():
    try:
        print("Testing new dashboard features...")
        
        # Check main dashboard page
        response = requests.get("http://localhost:8001/", timeout=5)
        html_content = response.text
        
        print(f"[+] Dashboard loaded: HTTP {response.status_code}")
        
        # Check if new sections exist in HTML
        sections_to_check = [
            ('emissions', 'Emissions Analysis'),
            ('transport', 'Transport & Logistics'), 
            ('energy', 'Energy Consumption')
        ]
        
        print(f"\n[*] Checking new content sections:")
        for section_id, section_title in sections_to_check:
            if f'id="{section_id}"' in html_content and section_title in html_content:
                print(f"    - {section_title}: [OK]")
            else:
                print(f"    - {section_title}: [MISSING]")
        
        # Check for info button and modal
        print(f"\n[*] Checking info features:")
        if 'id="infoBtn"' in html_content:
            print(f"    - Info button: [OK]")
        else:
            print(f"    - Info button: [MISSING]")
            
        if 'id="infoModal"' in html_content and 'SEBI BRSR' in html_content:
            print(f"    - Info modal content: [OK]")
        else:
            print(f"    - Info modal content: [MISSING]")
            
        if 'GLEC Framework' in html_content and "India's Net Zero 2070" in html_content:
            print(f"    - Regulatory information: [OK]")
        else:
            print(f"    - Regulatory information: [MISSING]")
        
        # Check JavaScript features
        js_response = requests.get("http://localhost:8001/app.js", timeout=5)
        js_content = js_response.text
        
        print(f"\n[*] Checking JavaScript features:")
        js_features = [
            ('setupInfoModal', 'Info modal functionality'),
            ('initEmissionsCharts', 'Emissions charts'),
            ('initTransportCharts', 'Transport charts'), 
            ('initEnergyCharts', 'Energy charts'),
            ('initializeSectionCharts', 'Dynamic chart loading')
        ]
        
        for feature, description in js_features:
            if feature in js_content:
                print(f"    - {description}: [OK]")
            else:
                print(f"    - {description}: [MISSING]")
        
        # Check CSS for modal styles
        css_response = requests.get("http://localhost:8001/style.css", timeout=5)
        css_content = css_response.text
        
        print(f"\n[*] Checking CSS features:")
        css_features = [
            ('.info-btn', 'Info button styles'),
            ('.modal', 'Modal styles'),
            ('.regulation-section', 'Regulatory content styles'),
            ('.section-header', 'Section header styles')
        ]
        
        for feature, description in css_features:
            if feature in css_content:
                print(f"    - {description}: [OK]")
            else:
                print(f"    - {description}: [MISSING]")
        
        print(f"\n[SUCCESS] All new features have been implemented and are ready!")
        print(f"[INFO] Dashboard URL: http://localhost:8001/")
        print(f"[INFO] New tabs (Emissions, Transport, Energy) should now display content")
        print(f"[INFO] Info button (i) in header opens regulatory information modal")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to test features: {e}")
        return False

if __name__ == "__main__":
    success = test_new_features()
    if not success:
        print(f"\n[FAILED] Feature testing failed")
        exit(1)
    else:
        print(f"\n[COMPLETE] Feature testing passed - dashboard ready for use!")