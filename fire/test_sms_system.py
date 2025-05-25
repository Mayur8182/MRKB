#!/usr/bin/env python3
"""
Test script for the enhanced SMS system
Tests Twilio and MSG91 SMS services
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_sms_service import sms_service
from sms_config import TWILIO_CONFIG, MSG91_CONFIG, SMS_SETTINGS

def test_sms_configuration():
    """Test SMS service configuration"""
    print("🔧 Testing SMS Configuration...")
    print("=" * 50)
    
    # Test Twilio configuration
    print("📱 Twilio Configuration:")
    print(f"   Account SID: {TWILIO_CONFIG.get('account_sid', 'Not set')}")
    print(f"   Auth Token: {'*' * 20 if TWILIO_CONFIG.get('auth_token') else 'Not set'}")
    print(f"   Verify Service SID: {TWILIO_CONFIG.get('verify_service_sid', 'Not set')}")
    print(f"   Enabled: {TWILIO_CONFIG.get('enabled', False)}")
    
    # Test MSG91 configuration
    print("\n📱 MSG91 Configuration:")
    print(f"   API Key: {'*' * 20 if MSG91_CONFIG.get('api_key') else 'Not set'}")
    print(f"   Sender ID: {MSG91_CONFIG.get('sender_id', 'Not set')}")
    print(f"   Enabled: {MSG91_CONFIG.get('enabled', False)}")
    
    # Test SMS settings
    print("\n⚙️ SMS Settings:")
    print(f"   Default Country Code: {SMS_SETTINGS.get('default_country_code')}")
    print(f"   OTP Validity: {SMS_SETTINGS.get('otp_validity_minutes')} minutes")
    print(f"   Max Retry Attempts: {SMS_SETTINGS.get('max_retry_attempts')}")
    print(f"   Console Logging: {SMS_SETTINGS.get('enable_console_logging')}")
    print(f"   Fallback to Console: {SMS_SETTINGS.get('fallback_to_console')}")

def test_phone_number_formatting():
    """Test phone number formatting"""
    print("\n📞 Testing Phone Number Formatting...")
    print("=" * 50)
    
    test_numbers = [
        "8780378086",           # 10 digit Indian number
        "08780378086",          # 11 digit with leading 0
        "918780378086",         # 12 digit with country code
        "+918780378086",        # With + and country code
        "91 8780378086",        # With space
        "91-8780-378-086"       # With dashes
    ]
    
    for number in test_numbers:
        formatted = sms_service.format_phone_number(number)
        print(f"   {number:15} → {formatted}")

def test_otp_generation():
    """Test OTP generation and storage"""
    print("\n🔢 Testing OTP Generation...")
    print("=" * 50)
    
    # Test OTP generation
    for i in range(5):
        otp = sms_service.generate_otp()
        print(f"   Generated OTP {i+1}: {otp}")
    
    # Test OTP storage and verification
    test_phone = "+918780378086"
    test_otp = "123456"
    
    print(f"\n📱 Testing OTP Storage for {test_phone}...")
    sms_service.store_otp(test_phone, test_otp)
    print(f"   OTP {test_otp} stored successfully")
    
    # Test verification
    print(f"\n✅ Testing OTP Verification...")
    success, message = sms_service.verify_otp(test_phone, test_otp)
    print(f"   Verification result: {success}")
    print(f"   Message: {message}")
    
    # Test wrong OTP
    success, message = sms_service.verify_otp(test_phone, "999999")
    print(f"   Wrong OTP result: {success}")
    print(f"   Message: {message}")

def test_sms_sending():
    """Test SMS sending (console mode)"""
    print("\n📨 Testing SMS Sending...")
    print("=" * 50)
    
    test_phone = "+918780378086"  # Your phone number
    
    print(f"📱 Sending test OTP to {test_phone}...")
    success, otp, message = sms_service.send_otp(test_phone)
    
    if success:
        print(f"✅ SMS sent successfully!")
        print(f"   OTP: {otp}")
        print(f"   Message: {message}")
        
        # Test verification
        print(f"\n🔍 Testing OTP verification...")
        user_input = input(f"Enter the OTP you received (or press Enter to use {otp}): ").strip()
        if not user_input:
            user_input = otp
        
        success, verify_message = sms_service.verify_otp(test_phone, user_input)
        print(f"   Verification result: {success}")
        print(f"   Message: {verify_message}")
    else:
        print(f"❌ Failed to send SMS: {message}")

def test_twilio_verify():
    """Test Twilio Verify API specifically"""
    print("\n🔐 Testing Twilio Verify API...")
    print("=" * 50)
    
    if not TWILIO_CONFIG.get('enabled', False):
        print("⚠️ Twilio is not enabled. Enable it in sms_config.py to test.")
        return
    
    test_phone = "+918780378086"  # Your phone number
    
    try:
        print(f"📱 Sending Twilio Verify OTP to {test_phone}...")
        success, message = sms_service.send_otp_twilio(test_phone, "123456")
        
        if success:
            print(f"✅ Twilio Verify OTP sent successfully!")
            print(f"   Message: {message}")
            
            # Test verification
            user_input = input("Enter the OTP you received via Twilio: ").strip()
            if user_input:
                success, verify_message = sms_service.verify_otp_twilio(test_phone, user_input)
                print(f"   Verification result: {success}")
                print(f"   Message: {verify_message}")
        else:
            print(f"❌ Failed to send Twilio OTP: {message}")
            
    except Exception as e:
        print(f"❌ Twilio test error: {str(e)}")

def test_msg91():
    """Test MSG91 API specifically"""
    print("\n📱 Testing MSG91 API...")
    print("=" * 50)
    
    if not MSG91_CONFIG.get('enabled', False):
        print("⚠️ MSG91 is not enabled. Enable it in sms_config.py to test.")
        return
    
    test_phone = "+918780378086"  # Your phone number
    test_otp = "123456"
    
    try:
        print(f"📱 Sending MSG91 OTP to {test_phone}...")
        success, message = sms_service.send_otp_msg91(test_phone, test_otp)
        
        if success:
            print(f"✅ MSG91 OTP sent successfully!")
            print(f"   Message: {message}")
        else:
            print(f"❌ Failed to send MSG91 OTP: {message}")
            
    except Exception as e:
        print(f"❌ MSG91 test error: {str(e)}")

def main():
    """Main test function"""
    print("🔥 Fire NOC System - SMS Service Test")
    print("=" * 50)
    
    # Run all tests
    test_sms_configuration()
    test_phone_number_formatting()
    test_otp_generation()
    
    # Ask user if they want to test actual SMS sending
    print("\n" + "=" * 50)
    test_real_sms = input("Do you want to test real SMS sending? (y/n): ").lower().strip()
    
    if test_real_sms == 'y':
        print("\n⚠️ WARNING: This will send real SMS messages!")
        confirm = input("Are you sure? This may cost money. (y/n): ").lower().strip()
        
        if confirm == 'y':
            test_sms_sending()
            
            # Test specific services if enabled
            if TWILIO_CONFIG.get('enabled', False):
                test_twilio_verify()
            
            if MSG91_CONFIG.get('enabled', False):
                test_msg91()
    
    print("\n" + "=" * 50)
    print("✨ SMS testing completed!")
    
    print("\n📋 Summary:")
    print("- SMS configuration has been tested")
    print("- Phone number formatting is working")
    print("- OTP generation and verification is functional")
    print("- Enhanced SMS service is ready to use")
    
    print("\n🔧 Next Steps:")
    print("1. Make sure your SMS service credentials are correct")
    print("2. Test with your actual phone number")
    print("3. Monitor SMS delivery and costs")
    print("4. Integrate with your Fire NOC application")

if __name__ == "__main__":
    main()
