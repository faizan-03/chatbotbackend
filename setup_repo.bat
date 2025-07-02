@echo off
echo 🚀 Setting up Backend Repository for Railway Deployment
echo.

echo ✅ Step 1: Initialize Git Repository
git init
echo.

echo ✅ Step 2: Add all files
git add .
echo.

echo ✅ Step 3: Create initial commit
git commit -m "Initial commit: University Chatbot Backend for Railway deployment"
echo.

echo ✅ Step 4: Verify deployment readiness
python verify_deployment.py
echo.

echo 🎉 Repository setup complete!
echo.
echo 📝 Next steps:
echo 1. Create a new repository on GitHub
echo 2. Copy the remote URL
echo 3. Run: git remote add origin YOUR_GITHUB_URL
echo 4. Run: git push -u origin main
echo 5. Deploy on Railway dashboard
echo.
pause
