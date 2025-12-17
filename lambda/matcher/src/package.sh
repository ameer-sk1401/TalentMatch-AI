#!/bin/bash

# Create package directory
rm -rf package
mkdir -p package

# Install dependencies
pip install -r requirements.txt -t package/

# Copy Lambda code
cp lambda_function.py package/

# Create zip
cd package
zip -r ../../../../lambda_matcher.zip .
cd ..

# Clean up
rm -rf package

echo "✅ Lambda package created: lambda_matcher.zip"