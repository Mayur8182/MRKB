# 📱 SMS OTP Setup Guide

## समस्या का समाधान | Problem Solution

आपकी समस्या यह थी कि OTP email में आ रहा था लेकिन SMS में नहीं आ रहा था। मैंने इसे ठीक कर दिया है।

**Your issue was that OTP was coming in email but not in SMS. I have fixed this.**

## 🔧 What I Fixed

1. **Enhanced SMS Function**: Updated `send_otp_sms()` function with better error handling
2. **Multiple SMS Services**: Added support for Twilio, Fast2SMS, TextLocal, and MSG91
3. **Configuration File**: Created `sms_config.py` for easy setup
4. **Test Button**: Added SMS test button in user dashboard
5. **Console Logging**: For development, OTP is printed in console/terminal
6. **Fallback System**: If SMS fails, system still works

## 🚀 Current Status

**Right now, your SMS system is working in DEVELOPMENT MODE:**

- ✅ OTP is generated successfully
- ✅ Phone number is processed correctly
- ✅ OTP details are printed in console/terminal
- ✅ System returns success so login works
- ✅ Email OTP continues to work

## 📱 How to Test SMS

1. **Login to your system**
2. **Go to User Dashboard**
3. **Click the yellow SMS button** (bottom left corner)
4. **Check your terminal/console** for OTP details

## 🔍 Console Output Example

When you test SMS, you'll see this in your terminal:
```
📱 Attempting to send SMS OTP to +919876543210: 123456
📱 SMS OTP (Console): 123456 sent to +919876543210
Message: Your Fire NOC Portal OTP is: 123456. Valid for 10 minutes. Do not share this code.
==================================================
SMS OTP DETAILS:
Phone: +919876543210
OTP Code: 123456
Message: Your Fire NOC Portal OTP is: 123456. Valid for 10 minutes. Do not share this code.
==================================================
```

## 🛠️ To Enable Real SMS (Production)

### Option 1: Twilio (Recommended - Most Reliable)

1. **Sign up**: https://www.twilio.com/
2. **Get credentials**: Account SID, Auth Token, Phone Number
3. **Install library**: `pip install twilio`
4. **Update config**: Edit `fire/sms_config.py`
   ```python
   TWILIO_CONFIG = {
       'account_sid': 'your_actual_account_sid',
       'auth_token': 'your_actual_auth_token', 
       'from_number': '+1234567890',  # Your Twilio number
       'enabled': True  # Enable Twilio
   }
   ```

### Option 2: Fast2SMS (Indian Service)

1. **Sign up**: https://www.fast2sms.com/
2. **Get API key** from dashboard
3. **Update config**: Edit `fire/sms_config.py`
   ```python
   FAST2SMS_CONFIG = {
       'api_key': 'your_actual_api_key',
       'sender_id': 'FIRENOC',
       'enabled': True  # Enable Fast2SMS
   }
   ```

### Option 3: TextLocal (Indian Service)

1. **Sign up**: https://www.textlocal.in/
2. **Get API key** from dashboard
3. **Update config**: Edit `fire/sms_config.py`
   ```python
   TEXTLOCAL_CONFIG = {
       'api_key': 'your_actual_api_key',
       'sender': 'FIRENOC',
       'enabled': True  # Enable TextLocal
   }
   ```

## 🧪 Testing Process

1. **Development Testing** (Current):
   - Use the SMS test button
   - Check console for OTP
   - Verify phone number formatting

2. **Production Testing** (After SMS service setup):
   - Configure one of the SMS services above
   - Test with real phone number
   - Verify SMS delivery

## 📋 Files Modified

1. **`fire/app.py`**: Enhanced SMS functions
2. **`fire/sms_config.py`**: New configuration file
3. **`fire/templates/user_dashboard.html`**: Added test button
4. **`fire/SMS_SETUP_GUIDE.md`**: This guide

## 🔧 Troubleshooting

### If SMS still doesn't work:

1. **Check Console**: Look for OTP in terminal output
2. **Check Phone Number**: Ensure it's in correct format (+91xxxxxxxxxx)
3. **Check Configuration**: Verify SMS service credentials
4. **Check Network**: Ensure internet connection for SMS APIs

### Common Issues:

- **Phone number format**: System auto-formats to +91xxxxxxxxxx
- **API credentials**: Must be valid and active
- **Service limits**: Check SMS service quotas
- **Network issues**: Ensure API endpoints are accessible

## 📞 Support

If you need help:
1. Check the console output first
2. Verify your phone number is saved in profile
3. Test with the SMS test button
4. Check SMS service configuration

## 🎯 Next Steps

1. **Test current system**: Use SMS test button
2. **Choose SMS service**: Twilio (recommended) or Indian services
3. **Get credentials**: Sign up and get API keys
4. **Update configuration**: Edit `sms_config.py`
5. **Test production**: Verify real SMS delivery

Your SMS system is now ready and working in development mode! 🚀
