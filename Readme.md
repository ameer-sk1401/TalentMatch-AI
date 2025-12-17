# 🤖 TalentMatch-AI : AI-Powered Resume Matcher

A serverless, AI-driven resume matching system built on AWS that intelligently matches resumes with job descriptions using Amazon Bedrock and delivers results via Telegram bot.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Technologies Used](#technologies-used)
- [AWS Services](#aws-services)
- [System Design](#system-design)
- [Features](#features)
- [Cost Analysis](#cost-analysis)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

The AI-Powered Resume Matcher is a production-ready serverless application that automates the resume matching process. Users can upload resumes via Telegram, and the system uses AI to extract skills automatically. When a job description is submitted, the system performs intelligent semantic matching to find the best-fitting resume.

**Key Capabilities:**

- 📤 Upload resumes via Telegram (PDF format)
- 🤖 AI-powered skill extraction using Amazon Bedrock
- 🔍 Semantic matching (understands synonyms and related technologies)
- 📊 Detailed match analysis with explanations
- 💾 Automatic storage in AWS S3 and DynamoDB
- 📥 Direct download links for matched resumes

---

## 🏗️ Architecture

                            ```
                                            ┌─────────────┐
                                            │   Telegram  │
                                            │     Bot     │
                                            └──────┬──────┘
                                                │ HTTPS Webhook
                                                ▼
                                        ┌─────────────────┐
                                        │  API Gateway    │ ◄── Public HTTPS Endpoint
                                        │   (HTTP API)    │
                                        └────────┬────────┘
                                                │
                                                ▼
                            ┌─────────────────────────────────────────────┐
                            │           AWS Lambda Function               │
                            │  ┌─────────────────────────────────────┐   │
                            │  │   Resume Upload Handler             │   │
                            │  │   • PDF Download from Telegram      │   │
                            │  │   • Text Extraction (PyPDF2)        │   │
                            │  │   • AI Skill Extraction (Bedrock)   │   │
                            │  │   • S3 Upload                       │   │
                            │  │   • DynamoDB Metadata Save          │   │
                            │  └─────────────────────────────────────┘   │
                            │                                             │
                            │  ┌─────────────────────────────────────┐   │
                            │  │   Job Matching Handler              │   │
                            │  │   • AI JD Parsing (Bedrock)         │   │
                            │  │   • Semantic Skill Matching (AI)    │   │
                            │  │   • Score Calculation               │   │
                            │  │   • Generate Download Links         │   │
                            │  └─────────────────────────────────────┘   │
                            └───┬─────────────┬──────────────┬───────────┘
                                │             │              │
                                ▼             ▼              ▼
                            ┌────────┐  ┌──────────┐  ┌─────────────┐
                            │   S3   │  │ DynamoDB │  │   Bedrock   │
                            │ Bucket │  │  Table   │  │ (Claude AI) │
                            └────────┘  └──────────┘  └─────────────┘
                            ```

---

## 🛠️ Technologies Used

### **Infrastructure & Deployment**

- **Terraform** - Infrastructure as Code (IaC) for all AWS resources
- **AWS CLI** - Command-line management and verification
- **Git/GitHub** - Version control and collaboration

### **Backend & Runtime**

- **Python 3.11** - Lambda function runtime
- **PyPDF2** - PDF text extraction
- **boto3** - AWS SDK for Python
- **urllib3** - HTTP client for Telegram API

### **AI/ML**

- **Amazon Bedrock** - AI service for skill extraction and semantic matching
- **Claude 3 Haiku** - Fast and cost-effective LLM model

### **Communication**

- **Telegram Bot API** - User interface and file handling

---

## ☁️ AWS Services

| Service                | Purpose                                  | Configuration                                                   |
| ---------------------- | ---------------------------------------- | --------------------------------------------------------------- |
| **Amazon S3**          | Resume storage with versioning           | Bucket with versioning enabled, server-side encryption (AES256) |
| **Amazon DynamoDB**    | Metadata storage (resume info, skills)   | On-demand billing, GSI on role field                            |
| **AWS Lambda**         | Serverless compute for business logic    | Python 3.11, 512MB-1GB memory, 30-60s timeout                   |
| **Amazon API Gateway** | HTTP API endpoint for Telegram webhook   | HTTP API with CORS, Lambda proxy integration                    |
| **Amazon Bedrock**     | AI-powered skill extraction and matching | Claude 3 Haiku model                                            |
| **AWS IAM**            | Security and permissions                 | Least-privilege policies for Lambda                             |
| **CloudWatch Logs**    | Logging and monitoring                   | 7-day retention for Lambda logs                                 |

---

## 🔧 System Design

### **Design Principles**

1. **Serverless Architecture** - No server management, automatic scaling
2. **Event-Driven** - Triggered by Telegram messages via webhook
3. **AI-First** - Leverage Amazon Bedrock for intelligent matching
4. **Cost-Optimized** - Pay-per-use, minimal idle costs
5. **Security-Focused** - IAM roles, encryption, private data storage
6. **Modular IaC** - Reusable Terraform modules

### **Data Flow**

#### **Resume Upload Flow:**

```
User uploads PDF → Telegram → API Gateway → Lambda
    ↓
Lambda extracts text (PyPDF2)
    ↓
Bedrock extracts skills (AI)
    ↓
Save PDF to S3 + Metadata to DynamoDB
    ↓
Return confirmation to user
```

#### **Job Matching Flow:**

```
User sends JD → Telegram → API Gateway → Lambda
    ↓
Bedrock parses JD requirements (AI)
    ↓
Query all resumes from DynamoDB
    ↓
Bedrock performs semantic matching for each resume (AI)
    ↓
Calculate scores, sort, filter (≥75% threshold)
    ↓
Generate S3 presigned URL for best match
    ↓
Return match details + download link
```

---

## ✨ Features

### **Core Features**

- ✅ **PDF Resume Upload** - Direct upload via Telegram bot
- ✅ **AI Skill Extraction** - Automatically identifies technologies, tools, frameworks
- ✅ **Semantic Matching** - Understands synonyms (e.g., "container orchestration" = Kubernetes)
- ✅ **Role Detection** - Auto-identifies job role (DevOps, Cloud Engineer, etc.)
- ✅ **Smart Scoring** - AI-powered match percentage with explanations
- ✅ **Instant Downloads** - Secure, time-limited download links

### **User Commands**

- `/start` - Welcome message and instructions
- `/help` - Detailed usage guide
- `/list` - View all available resumes
- `/stats` - System statistics (total resumes, skills)
- `/upload` - Upload instructions
- Send PDF - Upload new resume
- Send text - Match job description

### **AI Capabilities**

- **Synonym Recognition** - "CI/CD" matches "Jenkins", "GitHub Actions"
- **Related Skills** - "IaC" matches "Terraform", "Ansible"
- **Context Understanding** - "Cloud experience" matches "AWS", "Azure"
- **Detailed Explanations** - AI provides reasoning for match scores

---

## 💰 Cost Analysis

### **Monthly Cost Breakdown** (500 matches, 50 uploads)

| Service                     | Usage                  | Cost             |
| --------------------------- | ---------------------- | ---------------- |
| **S3 Storage**              | 1GB storage, 50 PUTs   | $0.02            |
| **DynamoDB**                | On-demand, light usage | $0.01            |
| **Lambda**                  | Free tier eligible     | $0.00            |
| **API Gateway**             | Free tier eligible     | $0.00            |
| **Bedrock (Resume Upload)** | 50 uploads × ~$0.0006  | $0.03            |
| **Bedrock (JD Parsing)**    | 500 × ~$0.00026        | $0.13            |
| **Bedrock (Matching)**      | 500 × ~$0.00045        | $0.23            |
| **CloudWatch Logs**         | 7-day retention        | $0.01            |
| **Total**                   |                        | **~$0.54/month** |

**Annual Cost:** ~$6.48/year (less than 2 coffees! ☕)

### **Cost at Scale**

| Monthly Matches | Estimated Cost |
| --------------- | -------------- |
| 100             | $0.18          |
| 500             | $0.54          |
| 1,000           | $0.90          |
| 5,000           | $3.00          |
| 10,000          | $5.50          |

---

## 📋 Prerequisites

### **Required Accounts & Tools**

1. **AWS Account** - With appropriate permissions (AdministratorAccess or custom policy)
2. **Terraform** - Version 1.0+ ([Install Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli))
3. **AWS CLI** - Version 2.x ([Install Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
4. **Python 3.11+** - For Lambda function packaging
5. **pip** - Python package manager
6. **Telegram Account** - To create and test bot

### **AWS Permissions Required**

- S3: CreateBucket, PutObject, GetObject
- DynamoDB: CreateTable, PutItem, Query, Scan
- Lambda: CreateFunction, UpdateFunctionCode
- API Gateway: CreateApi, CreateRoute, CreateIntegration
- IAM: CreateRole, AttachRolePolicy
- Bedrock: InvokeModel
- CloudWatch Logs: CreateLogGroup, PutLogEvents

### **Knowledge Prerequisites**

- Basic understanding of AWS services
- Terraform fundamentals
- Command-line proficiency
- Basic Python (for customization)

---

## 🚀 Setup Instructions

### **Step 1: Clone the Repository**

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/aws-resume-matcher.git
cd aws-resume-matcher

# Review the structure
ls -la
```

---

### **Step 2: Configure AWS Credentials**

```bash
# Configure AWS CLI with your credentials
aws configure

# Enter when prompted:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region: us-east-1
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

**Output should show:**

```json
{
  "UserId": "AIDAXXXXXXXXXXXXXXXXX",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

---

### **Step 3: Create Telegram Bot**

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Enter bot name: `My Resume Matcher`
4. Enter username: `my_resume_matcher_bot` (must end with `_bot`)
5. **Save the bot token** (looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Important:** Keep this token secure! Don't commit it to version control.

---

### **Step 4: Enable Amazon Bedrock**

1. Go to AWS Console → Amazon Bedrock
2. Navigate to **Model access**
3. Click **Manage model access**
4. Enable **Claude 3 Haiku** by Anthropic
5. Click **Save changes**
6. Wait for status to show "Access granted" (takes 1-2 minutes)

---

### **Step 5: Prepare Lambda Function**

```bash
# Navigate to Lambda source directory
cd lambda/matcher/src

# Ensure requirements.txt exists
cat > requirements.txt << EOF
PyPDF2==3.0.1
EOF

# Go back to project root
cd ../../..
```

---

### **Step 6: Build Lambda Deployment Package**

```bash
# Clean previous builds
rm -rf lambda/matcher/package
mkdir lambda/matcher/package

# Install Python dependencies
pip3 install -r lambda/matcher/src/requirements.txt -t lambda/matcher/package/

# Copy Lambda function
cp lambda/matcher/src/lambda_function.py lambda/matcher/package/

# Create deployment ZIP
cd lambda/matcher/package
zip -r ../../../lambda_function.zip .
cd ../../..

# Verify ZIP was created (should be ~1-2 MB)
ls -lh lambda_function.zip
```

**Expected output:**

```
-rw-r--r--  1 user  staff   1.2M Dec 17 10:30 lambda_function.zip
```

---

### **Step 7: Configure Terraform Variables**

Create `terraform.tfvars` file:

```bash
cat > terraform.tfvars << EOF
telegram_bot_token = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
EOF
```

**⚠️ Important:** Add to `.gitignore`:

```bash
echo "terraform.tfvars" >> .gitignore
```

---

### **Step 8: Initialize Terraform**

```bash
# Initialize Terraform (downloads providers and modules)
terraform init

# Validate configuration
terraform validate

# Review what will be created
terraform plan
```

**Expected output:**

```
Plan: 15 to add, 0 to change, 0 to destroy.
```

---

### **Step 9: Deploy Infrastructure**

```bash
# Deploy all resources
terraform apply

# Review the plan and type: yes
```

**Deployment takes ~2-3 minutes**

**Expected output:**

```
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:

api_gateway_url = "https://abc123xyz.execute-api.us-east-1.amazonaws.com"
api_invoke_url = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/match"
dynamodb_table_name = "resume-matcher-metadata-dev"
lambda_matcher_name = "resume-matcher-matcher-dev"
s3_bucket_name = "resume-analyzer-dev-123456789012"
```

**Save these outputs!** You'll need them for the next step.

---

### **Step 10: Configure Telegram Webhook**

```bash
# Get your API Gateway URL
API_URL=$(terraform output -raw api_invoke_url)
echo "API URL: $API_URL"

# Set webhook (replace YOUR_BOT_TOKEN with actual token)
curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${API_URL}\"}"
```

**Expected response:**

```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

**Verify webhook:**

```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

---

### **Step 11: Test the System**

Open Telegram and search for your bot by username (e.g., `@my_resume_matcher_bot`)

**Test Commands:**

1. **Send:** `/start`

   - **Expected:** Welcome message with instructions

2. **Send:** `/help`

   - **Expected:** Detailed help information

3. **Upload a PDF resume**

   - **Expected:**
     - "Processing your resume..."
     - "Analyzing with AI..."
     - "Resume Uploaded Successfully!"
     - Skills extracted and displayed

4. **Send:** `/list`

   - **Expected:** List of uploaded resumes

5. **Send a job description:**
   ```
   Looking for DevOps Engineer with AWS, Docker, Kubernetes, and Terraform
   ```
   - **Expected:**
     - "Using AI to analyze..."
     - "Best Match Found!"
     - Match score and details
     - Download link

---

## 📂 Project Structure

```
aws-resume-matcher/
├── modules/                          # Terraform modules
│   ├── s3_bucket/                   # S3 bucket module
│   │   ├── main.tf                  # S3 resources
│   │   ├── variables.tf             # Input variables
│   │   └── outputs.tf               # Output values
│   ├── dynamodb/                    # DynamoDB module
│   │   ├── main.tf                  # DynamoDB table
│   │   ├── variables.tf             # Input variables
│   │   └── outputs.tf               # Output values
│   ├── iam/                         # IAM roles module
│   │   ├── main.tf                  # IAM roles & policies
│   │   ├── variables.tf             # Input variables
│   │   └── outputs.tf               # Output values
│   ├── lambda/                      # Lambda function module
│   │   ├── main.tf                  # Lambda resources
│   │   ├── variables.tf             # Input variables
│   │   └── outputs.tf               # Output values
│   └── api_gateway/                 # API Gateway module
│       ├── main.tf                  # API Gateway resources
│       ├── variables.tf             # Input variables
│       └── outputs.tf               # Output values
├── lambda/                          # Lambda function code
│   └── matcher/                     # Matcher function
│       ├── src/                     # Source code
│       │   ├── lambda_function.py   # Main handler
│       │   └── requirements.txt     # Python dependencies
│       └── package/                 # Build directory (generated)
├── main.tf                          # Root Terraform config
├── providers.tf                     # AWS provider config
├── variables.tf                     # Root variables
├── outputs.tf                       # Root outputs
├── versions.tf                      # Terraform version constraints
├── terraform.tfvars                 # Variable values (git-ignored)
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
└── LICENSE                          # Project license
```

---

## 🔄 How It Works

### **1. Resume Upload Process**

```
User → Uploads PDF to Telegram Bot
  ↓
API Gateway → Receives webhook POST request
  ↓
Lambda Function:
  1. Downloads PDF from Telegram servers
  2. Extracts text using PyPDF2
  3. Sends text to Amazon Bedrock (Claude 3 Haiku)
  4. Bedrock returns extracted skills as JSON
  5. Auto-detects role based on keywords
  6. Uploads PDF to S3 bucket
  7. Saves metadata to DynamoDB
  ↓
Response → Confirmation with skill list sent to user
```

**DynamoDB Schema:**

```json
{
  "resume_id": "resume_20251217_123456",
  "role": "DevOps Engineer",
  "skills": ["aws", "terraform", "docker", "kubernetes", ...],
  "s3_key": "resumes/devops-engineer/john_doe.pdf",
  "filename": "john_doe.pdf",
  "created_at": "2025-12-17T12:34:56Z",
  "uploaded_by": "telegram_chat_id"
}
```

---

### **2. Job Matching Process**

```
User → Sends job description text
  ↓
API Gateway → Receives webhook POST request
  ↓
Lambda Function:
  1. Sends JD to Bedrock for requirement extraction
     → Bedrock returns: required skills, role, experience level

  2. Queries all resumes from DynamoDB

  3. For each resume:
     - Sends (JD requirements + resume skills) to Bedrock
     - Bedrock performs semantic matching
     - Returns: match_score, matched_skills, explanation

  4. Sorts results by match score (descending)

  5. Filters matches ≥75% threshold

  6. For best match:
     - Generates S3 presigned URL (1-hour expiry)
     - Formats detailed response
  ↓
Response → Match details + download link sent to user
```

**Semantic Matching Examples:**

- JD: "container orchestration" → Matches: "kubernetes", "docker"
- JD: "CI/CD" → Matches: "jenkins", "github actions", "gitlab"
- JD: "infrastructure as code" → Matches: "terraform", "ansible"
- JD: "cloud platforms" → Matches: "aws", "azure", "gcp"

---

### **3. AI Prompting Strategy**

#### **Skill Extraction Prompt:**

```
Analyze this resume and extract ALL technical skills...
Include: programming languages, cloud platforms, tools, databases, frameworks
Return ONLY a JSON array: ["skill1", "skill2", ...]
```

#### **JD Parsing Prompt:**

```
Extract key information from this job description:
{
  "skills": [...],
  "role": "...",
  "experience_level": "...",
  "key_requirements": [...]
}
```

#### **Semantic Matching Prompt:**

```
Compare these skills considering:
1. Direct matches (exact names)
2. Semantic matches (synonyms, related tech)
3. Skill categories (CI/CD includes Jenkins, GitHub Actions)

Return match_score (0-100), matched_skills, explanation
```

---

## 🧪 Testing

### **Manual Testing via Telegram**

#### **Test 1: Resume Upload**

1. Send a PDF resume to bot
2. Verify AI extracts skills correctly
3. Check `/list` shows the new resume

#### **Test 2: Keyword Matching**

```
Looking for DevOps Engineer with AWS and Docker
```

- Should match if resume has these exact skills

#### **Test 3: Semantic Matching**

```
Need engineer with container orchestration experience
```

- Should match Kubernetes/Docker even without exact phrase

#### **Test 4: Complex Query**

```
Senior Cloud Engineer with infrastructure automation, monitoring solutions, and CI/CD pipelines
```

- Should match Terraform, Prometheus, Jenkins semantically

---

### **Testing via AWS CLI**

#### **Invoke Lambda Directly:**

```bash
aws lambda invoke \
  --function-name $(terraform output -raw lambda_matcher_name) \
  --payload '{"body": "{\"job_description\": \"DevOps with AWS\"}"}' \
  --region us-east-1 \
  response.json

cat response.json
```

#### **Test API Gateway:**

```bash
API_URL=$(terraform output -raw api_invoke_url)

curl -X POST $API_URL \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Cloud Engineer with AWS and Terraform"}'
```

---

### **Monitoring & Debugging**

#### **View Lambda Logs:**

```bash
aws logs tail "/aws/lambda/$(terraform output -raw lambda_matcher_name)" \
  --region us-east-1 \
  --follow
```

#### **Check DynamoDB Contents:**

```bash
aws dynamodb scan \
  --table-name $(terraform output -raw dynamodb_table_name) \
  --region us-east-1
```

#### **List S3 Resumes:**

```bash
aws s3 ls s3://$(terraform output -raw s3_bucket_name)/resumes/ \
  --recursive \
  --region us-east-1
```

---

## 🐛 Troubleshooting

### **Issue: Bot doesn't respond**

**Check 1: Webhook configured?**

```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

- Should show your API Gateway URL
- If not, run webhook setup again

**Check 2: Lambda has bot token?**

```bash
aws lambda get-function-configuration \
  --function-name $(terraform output -raw lambda_matcher_name) \
  --region us-east-1 \
  --query 'Environment.Variables.TELEGRAM_BOT_TOKEN'
```

- Should show your actual token, not "BOT_TOKEN"

**Check 3: Lambda logs for errors:**

```bash
aws logs tail "/aws/lambda/$(terraform output -raw lambda_matcher_name)" \
  --region us-east-1 \
  --since 5m
```

---

### **Issue: "Could not extract text from PDF"**

**Cause:** Lambda doesn't have PyPDF2 or PDF is image-based

**Solution 1: Rebuild Lambda package:**

```bash
cd lambda/matcher/src
rm -rf ../package
mkdir ../package
pip3 install -r requirements.txt -t ../package/
cp lambda_function.py ../package/
cd ../package
zip -r ../../../../lambda_function.zip .
cd ../../../..
terraform apply -var="telegram_bot_token=YOUR_TOKEN"
```

**Solution 2: Verify PDF:**

- Open PDF and try to select text
- If you can't select text, it's a scanned image (use OCR or different PDF)

---

### **Issue: Low match scores**

**Cause:** Skills not extracted properly or threshold too high

**Check extracted skills:**

```
Send /list in Telegram → View extracted skills
```

**Adjust threshold:**
In `lambda_function.py`, change:

```python
good_matches = [m for m in matches if m['score'] >= 60]  # Lowered from 75
```

---

### **Issue: Bedrock AccessDeniedException**

**Cause:** Model access not enabled

**Solution:**

1. Go to AWS Console → Bedrock → Model access
2. Enable "Claude 3 Haiku"
3. Wait for "Access granted" status
4. Retry operation

---

### **Issue: High AWS costs**

**Check Bedrock usage:**

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvocationCount \
  --start-time 2025-12-01T00:00:00Z \
  --end-time 2025-12-17T23:59:59Z \
  --period 86400 \
  --statistics Sum \
  --region us-east-1
```

**Reduce costs:**

- Implement caching for common queries
- Use fallback keyword matching for simple queries
- Set usage quotas in AWS Budgets

---

## 🚀 Deployment

### **Production Deployment Checklist**

- [ ] Enable versioning on S3 bucket
- [ ] Configure DynamoDB point-in-time recovery
- [ ] Set up CloudWatch alarms for errors
- [ ] Implement API rate limiting
- [ ] Add authentication/authorization
- [ ] Configure custom domain name
- [ ] Set up CI/CD pipeline
- [ ] Enable AWS X-Ray tracing
- [ ] Configure backup strategy
- [ ] Document runbooks
- [ ] Set up monitoring dashboards
- [ ] Configure alerts (SNS/Slack)

### **Environment Variables**

| Variable              | Description            | Required   |
| --------------------- | ---------------------- | ---------- |
| `TELEGRAM_BOT_TOKEN`  | Telegram bot API token | Yes        |
| `S3_BUCKET_NAME`      | S3 bucket for resumes  | Yes (auto) |
| `DYNAMODB_TABLE_NAME` | DynamoDB table name    | Yes (auto) |
| `ENVIRONMENT`         | Deployment environment | Yes (auto) |

### **Updating the System**

```bash
# Pull latest changes
git pull origin main

# Rebuild Lambda if code changed
cd lambda/matcher/src
rm -rf ../package && mkdir ../package
pip3 install -r requirements.txt -t ../package/
cp lambda_function.py ../package/
cd ../package && zip -r ../../../../lambda_function.zip . && cd ../../../..

# Apply changes
terraform apply -var="telegram_bot_token=YOUR_TOKEN"
```

---

## 🔮 Future Enhancements

### **Planned Features**

- [ ] **Multi-language support** - Resumes in different languages
- [ ] **Resume templates** - Generate formatted resumes
- [ ] **Experience matching** - Match years of experience
- [ ] **Location filtering** - Geographic preferences
- [ ] **Salary range matching** - Budget constraints
- [ ] **Interview scheduling** - Calendar integration
- [ ] **Email notifications** - Alert on new matches
- [ ] **Analytics dashboard** - Match statistics, trends
- [ ] **Batch processing** - Upload multiple resumes at once
- [ ] **Resume versioning** - Track changes over time

### **Technical Improvements**

- [ ] Implement caching layer (Redis/ElastiCache)
- [ ] Add vector embeddings for better semantic search
- [ ] Implement A/B testing for matching algorithms
- [ ] Add resume scoring/ranking system
- [ ] Implement feedback loop for ML improvements
- [ ] Add support for DOCX/TXT formats
- [ ] Implement OCR for scanned PDFs
- [ ] Add resume anonymization feature
- [ ] Implement audit logging
- [ ] Add data export functionality

### **Integration Opportunities**

- Slack bot integration
- WhatsApp Business API
- LinkedIn integration
- ATS (Applicant Tracking System) integration
- Job board API integration
- Calendar API for scheduling
- Email service integration (SendGrid/SES)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### **How to Contribute**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### **Development Guidelines**

- Follow existing code style and conventions
- Add tests for new features
- Update documentation as needed
- Keep commits atomic and well-described
- Ensure Terraform validates before submitting

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📧 Contact

**Project Maintainer:** Ameer Shaik

---

## 🙏 Acknowledgments

- **Amazon Web Services** - For providing serverless infrastructure
- **Anthropic** - For Claude AI model via Amazon Bedrock
- **Terraform** - For infrastructure as code capabilities
- **Telegram** - For bot API and platform
- **PyPDF2** - For PDF text extraction

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Built with ❤️ using AWS, Terraform, and AI**
