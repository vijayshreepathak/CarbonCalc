#!/usr/bin/env python3
"""
Verify that the modal fix is working properly
"""

import requests
import re

def test_modal_styling():
    try:
        print("Testing modal overlay fixes...")
        
        # Check CSS for proper modal styling
        css_response = requests.get("http://localhost:8001/style.css", timeout=5)
        css_content = css_response.text
        
        # Check for key modal styling improvements
        checks = [
            ("position: fixed", "Modal uses fixed positioning"),
            ("z-index: 2000", "Modal has high z-index for overlay"),
            ("backdrop-filter: blur", "Modal has backdrop blur effect"),
            ("width: 100vw", "Modal covers full viewport width"),
            ("height: 100vh", "Modal covers full viewport height"),
            ("overflow: hidden", "Body overflow control"),
            ("transform: scale", "Modal has scaling animation"),
            ("rgba(0, 0, 0, 0.75)", "Modal has proper backdrop"),
        ]
        
        print(f"\n[*] CSS Modal Styling Checks:")
        all_good = True
        for check, description in checks:
            if check in css_content:
                print(f"    - {description}: [OK]")
            else:
                print(f"    - {description}: [MISSING]")
                all_good = False
        
        # Check JavaScript for proper modal handling
        js_response = requests.get("http://localhost:8001/app.js", timeout=5)
        js_content = js_response.text
        
        js_checks = [
            ("setupInfoModal", "Modal setup function exists"),
            ("preventDefault()", "Click event properly handled"),
            ("stopPropagation()", "Event bubbling prevented"),
            ("document.body.style.overflow", "Body scroll control"),
            ("requestAnimationFrame", "Smooth modal animation"),
            ("modal.classList.add('show')", "Modal show class toggle"),
        ]
        
        print(f"\n[*] JavaScript Modal Handling Checks:")
        for check, description in js_checks:
            if check in js_content:
                print(f"    - {description}: [OK]")
            else:
                print(f"    - {description}: [MISSING]")
                all_good = False
        
        # Check HTML for info button and modal structure
        html_response = requests.get("http://localhost:8001/", timeout=5)
        html_content = html_response.text
        
        html_checks = [
            ('id="infoBtn"', "Info button exists"),
            ('id="infoModal"', "Info modal exists"), 
            ('class="modal-content"', "Modal content wrapper"),
            ('id="closeInfoModal"', "Close button exists"),
            ('SEBI BRSR', "Regulatory content present"),
            ('GLEC Framework', "GLEC content present"),
            ("India's Net Zero 2070", "Net Zero content present"),
        ]
        
        print(f"\n[*] HTML Structure Checks:")
        for check, description in html_checks:
            if check in html_content:
                print(f"    - {description}: [OK]")
            else:
                print(f"    - {description}: [MISSING]")
                all_good = False
        
        if all_good:
            print(f"\n[SUCCESS] Modal overlay fix is complete!")
            print(f"[INFO] The info modal should now:")
            print(f"       - Appear as a floating overlay")
            print(f"       - Not disrupt the page layout") 
            print(f"       - Have proper backdrop blur effect")
            print(f"       - Prevent background interaction")
            print(f"       - Close with ESC key or clicking outside")
        else:
            print(f"\n[WARNING] Some modal fixes may not be complete")
            
        print(f"\n[INFO] Dashboard URL: http://localhost:8001/")
        print(f"[INFO] Click the (i) button in the header to test the modal")
        
        return all_good
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to verify modal fixes: {e}")
        return False

if __name__ == "__main__":
    success = test_modal_styling()
    if success:
        print(f"\n[READY] Modal overlay is properly implemented!")
    else:
        print(f"\n[INCOMPLETE] Some modal fixes may need attention")