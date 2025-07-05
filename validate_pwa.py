#!/usr/bin/env python3
"""
Validate PWA readiness for APK generation
"""

import requests
import json
import os

def check_url_accessibility(url):
    """Check if URL is accessible"""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)

def check_manifest(base_url):
    """Check manifest.json"""
    manifest_url = f"{base_url}/static/manifest.json"
    try:
        response = requests.get(manifest_url, timeout=10)
        if response.status_code == 200:
            manifest = response.json()
            required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
            missing_fields = [field for field in required_fields if field not in manifest]
            return True, manifest, missing_fields
        else:
            return False, None, [f"HTTP {response.status_code}"]
    except Exception as e:
        return False, None, [str(e)]

def check_service_worker(base_url):
    """Check service worker"""
    sw_url = f"{base_url}/service-worker.js"
    try:
        response = requests.get(sw_url, timeout=10)
        return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)

def check_icons(base_url, manifest):
    """Check if icons are accessible"""
    if not manifest or 'icons' not in manifest:
        return False, "No icons in manifest"
    
    icon_results = []
    for icon in manifest['icons']:
        icon_url = base_url + icon['src']
        try:
            response = requests.get(icon_url, timeout=10)
            icon_results.append({
                'src': icon['src'],
                'sizes': icon['sizes'],
                'accessible': response.status_code == 200,
                'status': response.status_code
            })
        except Exception as e:
            icon_results.append({
                'src': icon['src'],
                'sizes': icon['sizes'],
                'accessible': False,
                'status': str(e)
            })
    
    return icon_results

def main():
    """Validate PWA for APK generation"""
    base_url = "https://mrkb.onrender.com"
    
    print("🔥 Fire Shakti PWA Validation for APK Generation")
    print("=" * 60)
    print(f"🌐 Checking: {base_url}")
    print()
    
    # Check main URL
    print("1. 🌐 Main URL Accessibility:")
    accessible, status = check_url_accessibility(base_url)
    if accessible:
        print(f"   ✅ {base_url} - Accessible (HTTP {status})")
    else:
        print(f"   ❌ {base_url} - Not accessible ({status})")
        return
    
    # Check manifest
    print("\n2. 📋 Manifest.json:")
    manifest_ok, manifest, missing = check_manifest(base_url)
    if manifest_ok:
        print(f"   ✅ Manifest accessible")
        print(f"   📱 App Name: {manifest.get('name', 'N/A')}")
        print(f"   🏷️ Short Name: {manifest.get('short_name', 'N/A')}")
        print(f"   🎯 Start URL: {manifest.get('start_url', 'N/A')}")
        print(f"   📺 Display: {manifest.get('display', 'N/A')}")
        
        if missing:
            print(f"   ⚠️ Missing fields: {', '.join(missing)}")
        else:
            print("   ✅ All required fields present")
    else:
        print(f"   ❌ Manifest not accessible: {missing}")
        return
    
    # Check service worker
    print("\n3. ⚙️ Service Worker:")
    sw_ok, sw_status = check_service_worker(base_url)
    if sw_ok:
        print(f"   ✅ Service worker accessible (HTTP {sw_status})")
    else:
        print(f"   ❌ Service worker not accessible ({sw_status})")
    
    # Check icons
    print("\n4. 🎨 Icons:")
    icon_results = check_icons(base_url, manifest)
    if icon_results:
        accessible_icons = [icon for icon in icon_results if icon['accessible']]
        print(f"   📊 Total icons: {len(icon_results)}")
        print(f"   ✅ Accessible: {len(accessible_icons)}")
        print(f"   ❌ Not accessible: {len(icon_results) - len(accessible_icons)}")
        
        print("\n   Icon Details:")
        for icon in icon_results:
            status_icon = "✅" if icon['accessible'] else "❌"
            print(f"   {status_icon} {icon['sizes']} - {icon['src']} ({icon['status']})")
    
    # APK Generation Readiness
    print("\n" + "=" * 60)
    print("📱 APK Generation Readiness:")
    
    readiness_score = 0
    total_checks = 4
    
    if accessible:
        readiness_score += 1
        print("✅ Main URL accessible")
    else:
        print("❌ Main URL not accessible")
    
    if manifest_ok and not missing:
        readiness_score += 1
        print("✅ Manifest complete and valid")
    else:
        print("❌ Manifest issues found")
    
    if sw_ok:
        readiness_score += 1
        print("✅ Service worker available")
    else:
        print("⚠️ Service worker not accessible (optional)")
    
    if icon_results and len([i for i in icon_results if i['accessible']]) >= 2:
        readiness_score += 1
        print("✅ Icons available")
    else:
        print("❌ Insufficient icons")
    
    print(f"\n🎯 Readiness Score: {readiness_score}/{total_checks}")
    
    if readiness_score >= 3:
        print("🎉 Your PWA is ready for APK generation!")
        print("\n📱 Recommended APK Generation Methods:")
        print("1. PWA2APK: https://www.pwa2apk.com/")
        print("2. PWABuilder: https://www.pwabuilder.com/")
        print("3. Bubblewrap CLI (advanced)")
        
        print(f"\n🔧 APK Configuration:")
        print(f"   URL: {base_url}")
        print(f"   Package ID: com.fireshakti.nocportal")
        print(f"   App Name: {manifest.get('name', 'Fire Shakti NOC Portal')}")
        print(f"   Version: 1.0.0")
    else:
        print("⚠️ PWA needs improvements before APK generation")
        print("Please fix the issues above and try again.")

if __name__ == "__main__":
    main()
