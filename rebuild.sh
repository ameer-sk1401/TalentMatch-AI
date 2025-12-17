#!/bin/bash

set -e  # Exit on error

# Configuration
export AWS_REGION=us-east-1
PYTHON_VERSION="python3.11"

echo "🔄 Rebuilding Lambda Function"
echo "================================"

# Get function name
FUNCTION_NAME=$(terraform output -raw lambda_function_name 2>/dev/null)
if [ -z "$FUNCTION_NAME" ]; then
    echo "❌ Could not get Lambda function name"
    exit 1
fi

echo "📦 Function: $FUNCTION_NAME"
echo "🌍 Region: $AWS_REGION"
echo ""

# Clean and prepare
echo "🧹 Cleaning build directory..."
cd lambda/matcher/src
rm -rf ../package
mkdir -p ../package

# Create requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "PyPDF2==3.0.1" > requirements.txt
fi

# Install dependencies
echo "📥 Installing Python dependencies..."
pip3 install -r requirements.txt -t ../package/ --upgrade --quiet

# Check if PyPDF2 was installed
if [ ! -d "../package/PyPDF2" ]; then
    echo "❌ PyPDF2 installation failed!"
    exit 1
fi

echo "✅ PyPDF2 installed"

# Copy Lambda function
echo "📄 Copying lambda_function.py..."
cp lambda_function.py ../package/

# Verify function exists
if [ ! -f "../package/lambda_function.py" ]; then
    echo "❌ lambda_function.py not found!"
    exit 1
fi

# Create zip
echo "📦 Creating deployment package..."
cd ../package
rm -f ../../../../lambda_function.zip
zip -r -q ../../../../lambda_function.zip .

cd ../../../..

# Check zip size
ZIP_SIZE=$(ls -lh lambda_function.zip | awk '{print $5}')
echo "✅ Package created: $ZIP_SIZE"

# Verify contents
echo ""
echo "📋 Package contents:"
unzip -l lambda_function.zip | grep -E "(lambda_function.py|PyPDF2)" | head -5

# Update Lambda
echo ""
echo "🚀 Updating Lambda function..."
UPDATE_OUTPUT=$(aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://lambda_function.zip \
  --region $AWS_REGION \
  --output json)

echo "⏳ Waiting for update to complete..."
sleep 10

# Verify update
echo "🔍 Verifying deployment..."
CONFIG=$(aws lambda get-function \
  --function-name $FUNCTION_NAME \
  --region $AWS_REGION \
  --query 'Configuration.[LastModified,CodeSize,Runtime]' \
  --output text)

echo ""
echo "✅ Deployment Complete!"
echo "================================"
echo "Last Modified: $(echo $CONFIG | awk '{print $1}')"
echo "Code Size: $(echo $CONFIG | awk '{print $2}') bytes"
echo "Runtime: $(echo $CONFIG | awk '{print $3}')"
echo ""
echo "🧪 Test in Telegram: /start"