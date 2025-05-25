# SMS Configuration File
# Configure your SMS service credentials here
#
# CURRENT STATUS:
# - Twilio: Disabled (trial account limitations)
# - MSG91: Disabled (API response parsing issues)
# - Console Fallback: ENABLED (OTP will be shown in terminal)
#
# For production, configure and enable one of the SMS services below

# Twilio Configuration (Recommended - Most Reliable)
TWILIO_CONFIG = {
    'account_sid': 'YOUR_TWILIO_ACCOUNT_SID',  # Your Twilio Account SID
    'auth_token': 'YOUR_TWILIO_AUTH_TOKEN',
    'from_number': '+15017122661',  # Twilio trial number (get your own from console)
    'verify_service_sid': 'YOUR_VERIFY_SERVICE_SID',  # Your Verify Service SID
    'enabled': False  # Disabled due to trial account limitations
}

# Fast2SMS Configuration (Indian SMS Service)
FAST2SMS_CONFIG = {
    'api_key': 'YOUR_FAST2SMS_API_KEY',  # Get from https://www.fast2sms.com/
    'sender_id': 'FIRENOC',
    'enabled': False  # Set to True when configured
}

# TextLocal Configuration (Indian SMS Service)
TEXTLOCAL_CONFIG = {
    'api_key': 'YOUR_TEXTLOCAL_API_KEY',  # Get from https://www.textlocal.in/
    'sender': 'FIRENOC',
    'enabled': False  # Set to True when configured
}

# MSG91 Configuration (Indian SMS Service)
MSG91_CONFIG = {
    'api_key': 'YOUR_MSG91_API_KEY',  # Your MSG91 API Key
    'template_id': '',  # Optional - leave empty for simple SMS
    'sender_id': 'FIRENOC',  # 6 character sender ID
    'route': '4',  # 4 for transactional SMS
    'enabled': False  # Temporarily disabled due to API issues
}

# SMS Settings
SMS_SETTINGS = {
    'default_country_code': '+91',  # India
    'otp_validity_minutes': 10,
    'max_retry_attempts': 3,
    'enable_console_logging': True,  # For development/testing
    'fallback_to_console': True  # If all services fail, log to console
}

# Instructions for setup:
"""
1. TWILIO SETUP (Recommended):
   - Sign up at https://www.twilio.com/
   - Get your Account SID and Auth Token from the dashboard
   - Buy a phone number or use the trial number
   - Update TWILIO_CONFIG above and set enabled=True

2. FAST2SMS SETUP (For India):
   - Sign up at https://www.fast2sms.com/
   - Get your API key from the dashboard
   - Update FAST2SMS_CONFIG above and set enabled=True

3. TEXTLOCAL SETUP (For India):
   - Sign up at https://www.textlocal.in/
   - Get your API key from the dashboard
   - Update TEXTLOCAL_CONFIG above and set enabled=True

4. MSG91 SETUP (For India):
   - Sign up at https://msg91.com/
   - Get your API key and create an OTP template
   - Update MSG91_CONFIG above and set enabled=True

5. For testing without real SMS service:
   - Keep all services disabled (enabled=False)
   - Set enable_console_logging=True
   - OTP will be printed in the console/terminal
"""
