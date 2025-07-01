# 🚀 Fire Safety NOC System - Deployment Guide

## 🔧 Fixing Deployment Issues

If you're encountering deployment issues on Render, follow these steps to resolve them:

### 1. Python Version

Ensure you're using Python 3.10.13 instead of Python 3.13.4. The `runtime.txt` file has been updated to specify this version.

```
python-3.10.13
```

### 2. Dependencies

The following changes have been made to the dependencies:

- Downgraded Pillow from 10.0.1 to 9.0.1 for better compatibility
- Commented out tensorflow and keras dependencies as they may cause issues
- Downgraded pandas from 2.1.4 to 2.0.3 for better compatibility
- Added pip, setuptools, and wheel with specific versions
- Added build package

### 3. Deployment Steps

1. Run the `fix_deployment.bat` script to update dependencies and check if they're installed correctly.
2. Deploy to Render using the following build command:

```
pip install -r requirements.txt
```

3. Use the following start command:

```
gunicorn --bind 0.0.0.0:$PORT simple_wsgi:application
```

### 4. Troubleshooting

If you still encounter issues, try the following:

- Check the Render logs for specific error messages
- Install dependencies one by one to identify problematic packages
- Use an older version of Python (3.9 or 3.8) if 3.10.13 doesn't work
- Remove or comment out non-essential dependencies

### 5. Environment Variables

Ensure all required environment variables are set in the Render dashboard:

- `MONGODB_URI`: MongoDB connection string
- `SECRET_KEY`: Secret key for Flask
- `MAIL_SERVER`: SMTP server for email notifications
- `MAIL_PORT`: SMTP port
- `MAIL_USERNAME`: SMTP username
- `MAIL_PASSWORD`: SMTP password
- `MAIL_DEFAULT_SENDER`: Default sender email
- `MSG91_AUTH_KEY`: MSG91 authentication key for SMS
- `MSG91_TEMPLATE_ID`: MSG91 template ID
- `MSG91_SENDER_ID`: MSG91 sender ID
- `MSG91_ROUTE`: MSG91 route
- `UPLOAD_FOLDER`: Folder for uploaded files
- `MAX_CONTENT_LENGTH`: Maximum content length

## 📋 Additional Resources

- [Render Python Deployment Documentation](https://render.com/docs/deploy-python)
- [Render Environment Variables](https://render.com/docs/environment-variables)
- [Render Poetry Version](https://render.com/docs/poetry-version)