#!/usr/bin/env python3
"""
Enhanced SMS Service for Fire NOC System
Supports multiple SMS providers: Twilio, MSG91, Fast2SMS, TextLocal
"""

import requests
import random
import string
from datetime import datetime, timedelta
from sms_config import TWILIO_CONFIG, MSG91_CONFIG, FAST2SMS_CONFIG, TEXTLOCAL_CONFIG, SMS_SETTINGS

class SMSService:
    def __init__(self):
        self.otp_storage = {}  # In production, use Redis or database

    def generate_otp(self, length=6):
        """Generate a random OTP"""
        return ''.join(random.choices(string.digits, k=length))

    def store_otp(self, phone_number, otp):
        """Store OTP with expiry time"""
        expiry_time = datetime.now() + timedelta(minutes=SMS_SETTINGS['otp_validity_minutes'])
        self.otp_storage[phone_number] = {
            'otp': otp,
            'expiry': expiry_time,
            'attempts': 0
        }

    def verify_otp(self, phone_number, entered_otp):
        """Verify the entered OTP"""
        if phone_number not in self.otp_storage:
            return False, "OTP not found or expired"

        stored_data = self.otp_storage[phone_number]

        # Check if OTP has expired
        if datetime.now() > stored_data['expiry']:
            del self.otp_storage[phone_number]
            return False, "OTP has expired"

        # Check attempts
        if stored_data['attempts'] >= SMS_SETTINGS['max_retry_attempts']:
            del self.otp_storage[phone_number]
            return False, "Maximum attempts exceeded"

        # Verify OTP
        if stored_data['otp'] == entered_otp:
            del self.otp_storage[phone_number]
            return True, "OTP verified successfully"
        else:
            stored_data['attempts'] += 1
            return False, f"Invalid OTP. {SMS_SETTINGS['max_retry_attempts'] - stored_data['attempts']} attempts remaining"

    def format_phone_number(self, phone_number):
        """Format phone number with country code"""
        if not phone_number.startswith('+'):
            if phone_number.startswith('0'):
                phone_number = phone_number[1:]  # Remove leading 0
            phone_number = SMS_SETTINGS['default_country_code'] + phone_number
        return phone_number

    def send_otp_twilio(self, phone_number, otp):
        """Send OTP using Twilio SMS API (not Verify API) to use custom OTP"""
        try:
            from twilio.rest import Client

            client = Client(TWILIO_CONFIG['account_sid'], TWILIO_CONFIG['auth_token'])

            # Create custom message with our OTP
            message_body = f"Your Fire NOC System OTP is: {otp}. Valid for {SMS_SETTINGS['otp_validity_minutes']} minutes. Do not share this OTP."

            # Send SMS using Twilio Messages API (not Verify API)
            message = client.messages.create(
                body=message_body,
                from_=TWILIO_CONFIG.get('from_number', '+12345678901'),  # You need to set this
                to=phone_number
            )

            print(f"✅ Twilio: Custom OTP {otp} sent successfully to {phone_number}")
            print(f"Message SID: {message.sid}")
            return True, f"OTP {otp} sent successfully via Twilio SMS"

        except Exception as e:
            print(f"❌ Twilio Error: {str(e)}")
            return False, f"Twilio error: {str(e)}"

    def verify_otp_twilio(self, phone_number, otp):
        """Verify OTP using our local verification (not Twilio Verify API)"""
        # Since we're now using custom OTP, use our local verification
        return self.verify_otp(phone_number, otp)

    def send_otp_msg91(self, phone_number, otp):
        """Send OTP using MSG91 API"""
        try:
            # Remove country code for MSG91 (it expects 10-digit Indian numbers)
            if phone_number.startswith('+91'):
                phone_number = phone_number[3:]
            elif phone_number.startswith('91'):
                phone_number = phone_number[2:]

            url = "https://api.msg91.com/api/v5/otp"

            payload = {
                "template_id": MSG91_CONFIG.get('template_id', ''),
                "mobile": phone_number,
                "authkey": MSG91_CONFIG['api_key'],
                "otp": otp,
                "sender": MSG91_CONFIG['sender_id'],
                "route": MSG91_CONFIG['route']
            }

            # If no template_id, send as simple SMS
            if not MSG91_CONFIG.get('template_id'):
                url = "https://api.msg91.com/api/sendhttp.php"
                message = f"Your Fire NOC System OTP is: {otp}. Valid for {SMS_SETTINGS['otp_validity_minutes']} minutes. Do not share this OTP."
                payload = {
                    "authkey": MSG91_CONFIG['api_key'],
                    "mobiles": phone_number,
                    "message": message,
                    "sender": MSG91_CONFIG['sender_id'],
                    "route": MSG91_CONFIG['route']
                }

            response = requests.post(url, data=payload)

            if response.status_code == 200:
                try:
                    # Try to parse as JSON
                    result = response.json()
                    if result.get('type') == 'success' or 'success' in str(result).lower():
                        print(f"✅ MSG91: OTP sent successfully to {phone_number}")
                        return True, "OTP sent successfully via MSG91"
                    else:
                        print(f"❌ MSG91 Error: {result}")
                        return False, f"MSG91 error: {result}"
                except ValueError:
                    # If JSON parsing fails, check response text
                    response_text = response.text.strip()
                    print(f"📱 MSG91 Response: {response_text}")
                    if 'success' in response_text.lower() or response_text.isdigit():
                        print(f"✅ MSG91: OTP sent successfully to {phone_number}")
                        return True, "OTP sent successfully via MSG91"
                    else:
                        print(f"❌ MSG91 Error: {response_text}")
                        return False, f"MSG91 error: {response_text}"
            else:
                print(f"❌ MSG91 HTTP Error: {response.status_code}")
                return False, f"MSG91 HTTP error: {response.status_code}"

        except Exception as e:
            print(f"❌ MSG91 Exception: {str(e)}")
            return False, f"MSG91 error: {str(e)}"

    def send_otp_fast2sms(self, phone_number, otp):
        """Send OTP using Fast2SMS API"""
        try:
            # Remove country code for Fast2SMS
            if phone_number.startswith('+91'):
                phone_number = phone_number[3:]
            elif phone_number.startswith('91'):
                phone_number = phone_number[2:]

            url = "https://www.fast2sms.com/dev/bulkV2"

            message = f"Your Fire NOC System OTP is {otp}. Valid for {SMS_SETTINGS['otp_validity_minutes']} minutes. Do not share this OTP."

            payload = {
                "authorization": FAST2SMS_CONFIG['api_key'],
                "sender_id": FAST2SMS_CONFIG['sender_id'],
                "message": message,
                "language": "english",
                "route": "q",
                "numbers": phone_number
            }

            headers = {
                'authorization': FAST2SMS_CONFIG['api_key'],
                'Content-Type': "application/x-www-form-urlencoded",
                'Cache-Control': "no-cache",
            }

            response = requests.post(url, data=payload, headers=headers)

            if response.status_code == 200:
                result = response.json()
                if result.get('return'):
                    print(f"✅ Fast2SMS: OTP sent successfully to {phone_number}")
                    return True, "OTP sent successfully via Fast2SMS"
                else:
                    print(f"❌ Fast2SMS Error: {result}")
                    return False, f"Fast2SMS error: {result}"
            else:
                print(f"❌ Fast2SMS HTTP Error: {response.status_code}")
                return False, f"Fast2SMS HTTP error: {response.status_code}"

        except Exception as e:
            print(f"❌ Fast2SMS Exception: {str(e)}")
            return False, f"Fast2SMS error: {str(e)}"

    def send_otp_textlocal(self, phone_number, otp):
        """Send OTP using TextLocal API"""
        try:
            # Remove country code for TextLocal
            if phone_number.startswith('+91'):
                phone_number = phone_number[3:]
            elif phone_number.startswith('91'):
                phone_number = phone_number[2:]

            url = "https://api.textlocal.in/send/"

            message = f"Your Fire NOC System OTP is {otp}. Valid for {SMS_SETTINGS['otp_validity_minutes']} minutes. Do not share this OTP."

            payload = {
                'apikey': TEXTLOCAL_CONFIG['api_key'],
                'numbers': phone_number,
                'message': message,
                'sender': TEXTLOCAL_CONFIG['sender']
            }

            response = requests.post(url, data=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    print(f"✅ TextLocal: OTP sent successfully to {phone_number}")
                    return True, "OTP sent successfully via TextLocal"
                else:
                    print(f"❌ TextLocal Error: {result}")
                    return False, f"TextLocal error: {result}"
            else:
                print(f"❌ TextLocal HTTP Error: {response.status_code}")
                return False, f"TextLocal HTTP error: {response.status_code}"

        except Exception as e:
            print(f"❌ TextLocal Exception: {str(e)}")
            return False, f"TextLocal error: {str(e)}"

    def send_otp(self, phone_number, custom_otp=None):
        """Send OTP using the first available SMS service"""
        phone_number = self.format_phone_number(phone_number)
        otp = custom_otp or self.generate_otp()

        # Store OTP for verification (except for Twilio which handles its own verification)
        self.store_otp(phone_number, otp)

        print(f"📱 Attempting to send OTP to {phone_number}")

        # Try services in order of preference
        services = [
            ('Twilio', TWILIO_CONFIG, self.send_otp_twilio),
            ('MSG91', MSG91_CONFIG, self.send_otp_msg91),
            ('Fast2SMS', FAST2SMS_CONFIG, self.send_otp_fast2sms),
            ('TextLocal', TEXTLOCAL_CONFIG, self.send_otp_textlocal)
        ]

        for service_name, config, send_function in services:
            if config.get('enabled', False):
                print(f"🔄 Trying {service_name}...")
                success, message = send_function(phone_number, otp)
                if success:
                    return True, otp, message
                else:
                    print(f"❌ {service_name} failed: {message}")

        # Fallback to console logging
        if SMS_SETTINGS.get('fallback_to_console', True):
            print(f"📱 CONSOLE FALLBACK: OTP for {phone_number} is: {otp}")
            return True, otp, "OTP logged to console (fallback mode)"

        return False, None, "All SMS services failed"

# Global SMS service instance
sms_service = SMSService()
