# 🚀 Fire Safety NOC System - Complete Render Deployment Guide

## 📋 Render Dashboard Settings

### 1. Service Configuration

- **Service Type**: Web Service
- **Name**: fire-safety-noc-system
- **Environment**: Python
- **Region**: Choose the region closest to your users (e.g., Ohio for US users)

### 2. Build and Start Commands

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT simple_wsgi:application`

### 3. Advanced Settings

- **Auto-Deploy**: Yes
- **Branch**: main
- **Root Directory**: Leave empty (or specify if your app is in a subdirectory)

## 🔧 Environment Variables

Add the following environment variables in the Render dashboard:

### Core Configuration
```
FLASK_APP=app.py
FLASK_ENV=production
FLASK_DEBUG=False
PORT=5000
HOST=0.0.0.0
```

### Database Configuration
```
MONGODB_URI=mongodb+srv://mkbharvad8080:Mkb%408080@cluster0.a82h2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
DB_NAME=aek_noc
```

### Security Configuration
```
SECRET_KEY=your_super_secure_secret_key_change_this_in_production_2024_render
SESSION_PERMANENT=True
SESSION_LIFETIME_DAYS=7
```

### Email Configuration
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=mkbharvad534@gmail.com
MAIL_PASSWORD=dwtp fmiq miyl ccvq
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_DEFAULT_SENDER=mkbharvad534@gmail.com
```

### SMS Configuration
```
MSG91_AUTH_KEY=YOUR_MSG91_API_KEY
MSG91_SENDER_ID=FIRNOC
MSG91_ROUTE=4
MSG91_TEMPLATE_ID=YOUR_TEMPLATE_ID
```

### File Upload Configuration
```
UPLOAD_FOLDER=static/profile_images
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=png,jpg,jpeg,gif,pdf
```

## 🛠️ Deployment Process

1. **Prepare Your Code**:
   - Ensure your code is in a GitHub repository
   - Make sure you have the correct `requirements.txt` file
   - Verify you have the correct `runtime.txt` file with `python-3.10.13`

2. **Create a New Web Service in Render**:
   - Connect your GitHub repository
   - Configure the service as described above
   - Add all environment variables

3. **Deploy Your Application**:
   - Click "Create Web Service"
   - Wait for the build and deployment to complete

4. **Verify Deployment**:
   - Check the logs for any errors
   - Visit your application URL to ensure it's working correctly

## 🔍 Troubleshooting Common Issues

### 1. Dependency Installation Failures

If you encounter issues with dependencies:

- Try using older versions of problematic packages (like we did with Pillow)
- Comment out non-essential dependencies
- Check if any packages require system-level dependencies

### 2. Port Binding Issues

If you see "No open ports detected" or similar errors:

- Ensure your application is binding to `0.0.0.0:$PORT`
- Try different start commands from `render_start_commands.txt`
- Verify the `PORT` environment variable is being used correctly

### 3. Database Connection Issues

If your application can't connect to MongoDB:

- Verify your MongoDB URI is correct
- Ensure your IP address is whitelisted in MongoDB Atlas
- Check if your database credentials are correct

### 4. File Upload Issues

If file uploads aren't working:

- Ensure the `UPLOAD_FOLDER` exists and is writable
- Verify the `MAX_CONTENT_LENGTH` is set appropriately
- Check if the `ALLOWED_EXTENSIONS` includes all required file types

## 📱 Testing Your Deployment

After deployment, test the following features:

1. User registration and login
2. OTP verification
3. File uploads
4. Form submissions
5. Email notifications
6. SMS notifications
7. Certificate generation and verification

## 🔄 Updating Your Deployment

To update your deployment:

1. Push changes to your GitHub repository
2. Render will automatically deploy the changes (if auto-deploy is enabled)
3. Monitor the logs for any issues during the update

## 📊 Monitoring and Scaling

- Use Render's dashboard to monitor your application's performance
- Set up alerts for high CPU or memory usage
- Consider upgrading your plan if you need more resources

## 🔒 Security Considerations

- Regularly update your dependencies
- Use environment variables for sensitive information
- Implement rate limiting for API endpoints
- Set up proper authentication and authorization

## 📞 Support and Resources

- [Render Documentation](https://render.com/docs)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [MongoDB Atlas Documentation](https://www.mongodb.com/docs/atlas/)
- [Python on Render](https://render.com/docs/deploy-python)