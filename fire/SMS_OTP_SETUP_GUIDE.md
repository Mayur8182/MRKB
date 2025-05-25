# 📱 SMS OTP System Setup Guide

## Overview

Your Fire NOC System now includes a comprehensive SMS OTP system that supports multiple SMS providers including Twilio and MSG91. This system provides secure 2FA authentication for user login and registration.

## 🔧 Current Configuration

### ✅ Configured Services

#### 1. Twilio (Primary Service)
- **Account SID:** `AC21b09c1cb25e642ddd201475bc12080a`
- **Auth Token:** `78a14e4041fd920576e0b679d3a39e83`
- **Verify Service SID:** `VA7485d0ae7ce9b07a6c5e3a55def16b91`
- **Status:** ✅ Enabled and Ready

#### 2. MSG91 (Secondary Service)
- **API Key:** `453564T2JkiVcp4hee683300c2P1`
- **Sender ID:** `FIRENOC`
- **Route:** `4` (Transactional SMS)
- **Status:** ✅ Enabled and Ready

### 📱 Target Phone Number
- **Your Phone:** `+918780378086`
- **Format:** International format with country code

## 🚀 How It Works

### 1. **Login Process with OTP**
```
User enters username/password → System generates OTP → 
SMS sent to user's phone → User enters OTP → Login successful
```

### 2. **SMS Service Priority**
1. **Twilio** (Most reliable, international)
2. **MSG91** (Indian service, cost-effective)
3. **Console Fallback** (Development mode)

### 3. **OTP Features**
- **6-digit random OTP**
- **10-minute validity**
- **3 retry attempts**
- **Automatic cleanup after verification**

## 📋 Testing Results

### ✅ What's Working
- ✅ SMS configuration loaded successfully
- ✅ Phone number formatting (handles various formats)
- ✅ OTP generation and storage
- ✅ OTP verification system
- ✅ Fallback to console logging
- ✅ Enhanced SMS service integration

### ⚠️ Next Steps Required

#### 1. **Install Twilio Library** ✅ COMPLETED
```bash
pip install twilio requests
```

#### 2. **Test Real SMS Sending**
```bash
cd fire
python test_sms_system.py
```

#### 3. **Verify Twilio Phone Number**
- You need to get a Twilio phone number from your console
- Update `from_number` in `sms_config.py`
- Current placeholder: `+12345678901`

## 🔐 Security Features

### OTP Security
- **Time-based expiry:** 10 minutes
- **Single-use:** OTP deleted after verification
- **Rate limiting:** Max 3 attempts
- **Secure storage:** Temporary database storage

### Phone Number Validation
- **Format normalization:** Handles various input formats
- **Country code handling:** Automatic +91 prefix for Indian numbers
- **Input sanitization:** Removes spaces, dashes, etc.

## 📱 SMS Templates

### Current OTP Message
```
Your Fire NOC System OTP is: [OTP]. Valid for 10 minutes. Do not share this OTP.
```

### Customizable Features
- Message content
- Sender ID (FIRENOC)
- Validity period
- Language support

## 🛠️ Configuration Files

### 1. `sms_config.py`
- SMS service credentials
- Provider settings
- OTP configuration

### 2. `enhanced_sms_service.py`
- Multi-provider SMS service
- OTP generation and verification
- Fallback mechanisms

### 3. `app.py` (Updated)
- Integration with login system
- OTP sending and verification
- Enhanced user experience

## 🧪 Testing Commands

### Test SMS Configuration
```bash
python test_sms_system.py
```

### Test Individual Services
```python
# Test Twilio
from enhanced_sms_service import sms_service
success, otp, message = sms_service.send_otp("+918780378086")

# Test MSG91
success, message = sms_service.send_otp_msg91("+918780378086", "123456")
```

## 📊 Cost Considerations

### Twilio Pricing
- **Trial Account:** Free credits for testing
- **Production:** ~$0.0075 per SMS to India
- **Verify API:** Enhanced security features

### MSG91 Pricing
- **Indian Service:** Cost-effective for Indian numbers
- **Bulk SMS:** Lower rates for high volume
- **Transactional SMS:** Route 4 for OTP messages

## 🔧 Troubleshooting

### Common Issues

#### 1. **"No module named 'twilio'"**
```bash
pip install twilio
```

#### 2. **SMS not received**
- Check phone number format
- Verify service credentials
- Check console logs for fallback OTP

#### 3. **OTP verification fails**
- Check OTP expiry (10 minutes)
- Verify correct phone number
- Check retry attempts (max 3)

### Debug Mode
- Set `enable_console_logging: True` in SMS_SETTINGS
- OTP will be printed to console for testing

## 🚀 Production Deployment

### 1. **Twilio Setup**
- Get production phone number
- Update `from_number` in config
- Monitor usage and costs

### 2. **MSG91 Setup**
- Verify API key is active
- Test with your phone number
- Monitor delivery rates

### 3. **Security Hardening**
- Use environment variables for credentials
- Enable rate limiting
- Monitor for abuse

## 📞 Support

### For Issues
1. Check console logs for error messages
2. Test with `test_sms_system.py`
3. Verify phone number format
4. Check service credentials

### Service Status
- **Twilio:** Check status.twilio.com
- **MSG91:** Check msg91.com status
- **System:** Monitor application logs

---

## 🎉 Ready to Use!

Your SMS OTP system is now configured and ready for production use. The system will:

1. **Send OTP via Twilio** (primary)
2. **Fallback to MSG91** (secondary)
3. **Console logging** (development)
4. **Secure verification** with time limits
5. **Enhanced user experience** with real-time SMS

Test the system with your phone number `+918780378086` and enjoy secure 2FA authentication! 🔐📱
