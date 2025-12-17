import json
import os
import boto3
from typing import Dict, List, Optional, Tuple
import urllib3
from datetime import datetime

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME')
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')

def lambda_handler(event, context):
    """Main Lambda handler for resume matching and uploads"""
    try:
        print(f"Received event: {json.dumps(event)}")
        
        body = json.loads(event.get('body', '{}'))
        
        if 'message' in body:
            return handle_telegram_message(body['message'])
        else:
            return handle_direct_api(body)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def handle_telegram_message(message: Dict):
    """Handle incoming Telegram message"""
    chat_id = message['chat']['id']
    
    # Check if message contains a document (PDF)
    if 'document' in message:
        return handle_document_upload(message)
    
    # Regular text message
    text = message.get('text', '').strip()
    print(f"Telegram message from {chat_id}: {text}")
    
    # Handle commands
    if text.startswith('/start'):
        welcome_msg = """👋 *Welcome to AI-Powered Resume Matcher Bot!*

I use *Amazon Bedrock AI* to intelligently match resumes with job descriptions!

*🎯 Two Ways to Use Me:*

*1️⃣ Smart Job Matching:*
Send me a job description and I'll:
- Use AI to extract required skills
- Perform semantic matching (understands synonyms!)
- Find the best resume with detailed analysis

*2️⃣ Resume Upload:*
Send a PDF resume and I'll:
- Extract text automatically
- Use AI to identify all skills
- Auto-detect role and save it

*✨ AI Features:*
- Understands "container orchestration" = Kubernetes
- Matches "CI/CD" with Jenkins, GitHub Actions
- Semantic skill matching, not just keywords!

*📋 Commands:*
/help - Detailed help
/list - View all resumes
/stats - System statistics

💡 *Try it:* Send a job description or upload a PDF!
"""
        send_telegram_message(chat_id, welcome_msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/help'):
        help_msg = """ℹ️ *AI Resume Matcher Help*

*🤖 Powered by Amazon Bedrock*

*📄 Upload Resume:*
1. Send me a PDF file
2. AI extracts all skills automatically
3. Auto-detects role (DevOps, Cloud, Data, etc.)
4. Saves to cloud storage

*🔍 Find Best Match:*
Send any job description like:
_"Looking for Senior DevOps Engineer with AWS, Kubernetes, and Terraform. Must have CI/CD experience."_

The AI will:
- Extract required skills intelligently
- Understand synonyms and related tech
- Match semantically, not just keywords
- Provide detailed match analysis

*📋 Commands:*
/list - View all available resumes
/stats - System statistics
/upload - Upload instructions

*💡 Example Queries:*
- "Need cloud engineer with container orchestration"
- "Hiring DevOps with infrastructure as code experience"
- "Looking for data engineer with AWS Glue and EMR"
"""
        send_telegram_message(chat_id, help_msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/list'):
        resumes = get_all_resumes()
        if not resumes:
            send_telegram_message(chat_id, "📭 No resumes in database yet. Upload one by sending a PDF!")
            return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
        msg = f"📋 *Available Resumes ({len(resumes)})*\n\n"
        for resume in resumes:
            msg += f"• *{resume['resume_id']}*\n"
            msg += f"  Role: {resume.get('role', 'N/A')}\n"
            msg += f"  Skills: {len(resume.get('skills', []))} found\n"
            msg += f"  Top: {', '.join(resume.get('skills', [])[:6])}\n\n"
        
        send_telegram_message(chat_id, msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/stats'):
        resumes = get_all_resumes()
        all_skills = set()
        for resume in resumes:
            all_skills.update(resume.get('skills', []))
        
        msg = f"📊 *System Statistics*\n\n"
        msg += f"🤖 AI Engine: Amazon Bedrock (Claude)\n"
        msg += f"📄 Total Resumes: {len(resumes)}\n"
        msg += f"🔧 Unique Skills: {len(all_skills)}\n\n"
        if all_skills:
            msg += f"Top Skills: {', '.join(sorted(list(all_skills))[:12])}"
        
        send_telegram_message(chat_id, msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/upload'):
        upload_msg = """📤 *How to Upload Resume*

1️⃣ Send me a PDF file
2️⃣ AI automatically extracts skills
3️⃣ Role is auto-detected
4️⃣ Saved to cloud storage

*That's it!* Just send a PDF now! 📄

*Supported:* Text-based PDFs (not scanned images)
"""
        send_telegram_message(chat_id, upload_msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    # Ignore other commands
    if text.startswith('/'):
        send_telegram_message(chat_id, "❓ Unknown command. Send /help for usage instructions.")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    # Empty message
    if not text:
        send_telegram_message(chat_id, "Please send me a job description or upload a PDF resume!")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    # Process as job description with AI
    return process_job_description_with_ai(chat_id, text)


def handle_document_upload(message: Dict):
    """Handle PDF resume upload from Telegram"""
    chat_id = message['chat']['id']
    document = message['document']
    
    if document.get('mime_type') != 'application/pdf':
        send_telegram_message(chat_id, "⚠️ Please send a PDF file only!")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    try:
        send_telegram_message(chat_id, "📄 Processing your resume...")
        
        file_id = document['file_id']
        file_name = document.get('file_name', 'resume.pdf')
        
        # Get file from Telegram
        file_info = get_telegram_file(file_id)
        if not file_info:
            send_telegram_message(chat_id, "❌ Error: Could not download file from Telegram")
            return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
        file_path = file_info['file_path']
        pdf_bytes = download_telegram_file(file_path)
        
        if not pdf_bytes:
            send_telegram_message(chat_id, "❌ Error: Could not download file")
            return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(pdf_bytes)
        
        if not resume_text:
            send_telegram_message(chat_id, "❌ Could not extract text from PDF. Make sure it's a text-based PDF!")
            return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
        print(f"Extracted text length: {len(resume_text)}")
        
        # Use Bedrock to extract skills
        send_telegram_message(chat_id, "🤖 Analyzing resume with AI to extract skills...")
        skills = extract_skills_with_bedrock(resume_text)
        
        if not skills:
            send_telegram_message(chat_id, "⚠️ Could not extract skills. Using fallback...")
            skills = extract_skills_fallback(resume_text)
        
        # Auto-detect role
        detected_role = detect_role_from_text(resume_text)
        
        # Generate unique resume ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        resume_id = f"resume_{timestamp}"
        
        # Upload to S3
        s3_key = f"resumes/{detected_role.lower().replace(' ', '-')}/{file_name}"
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=pdf_bytes,
            ContentType='application/pdf'
        )
        
        print(f"Uploaded to S3: {s3_key}")
        
        # Save metadata to DynamoDB
        table = dynamodb.Table(DYNAMODB_TABLE)
        table.put_item(
            Item={
                'resume_id': resume_id,
                'role': detected_role,
                'skills': skills,
                's3_key': s3_key,
                'created_at': datetime.utcnow().isoformat(),
                'filename': file_name,
                'uploaded_by': str(chat_id)
            }
        )
        
        print(f"Saved to DynamoDB: {resume_id}")
        
        # Success message
        success_msg = f"""✅ *Resume Uploaded Successfully!*

📋 *Details:*
- Resume ID: `{resume_id}`
- Detected Role: {detected_role}
- Skills Found: {len(skills)}

🔧 *Extracted Skills:*
{', '.join(skills[:20])}{'...' if len(skills) > 20 else ''}

🤖 Powered by Amazon Bedrock AI
Your resume is now available for smart matching! 🎉
"""
        send_telegram_message(chat_id, success_msg, parse_mode='Markdown')
        
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        import traceback
        traceback.print_exc()
        send_telegram_message(chat_id, f"❌ Error processing resume: {str(e)}")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}


def process_job_description_with_ai(chat_id: int, job_description: str):
    """
    Process job description using AI for intelligent matching
    """
    send_telegram_message(chat_id, "🤖 Using AI to analyze job description...")
    
    # Step 1: Extract requirements using AI
    jd_requirements = extract_jd_requirements_with_ai(job_description)
    
    if not jd_requirements or not jd_requirements.get('skills'):
        send_telegram_message(chat_id, "❌ Couldn't extract requirements from job description. Try including specific technologies.")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    required_skills = jd_requirements['skills']
    
    # Get all resumes
    resumes = get_all_resumes()
    
    if not resumes:
        send_telegram_message(chat_id, "⚠️ No resumes in database. Upload one by sending a PDF!")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    send_telegram_message(chat_id, f"🔍 Found {len(required_skills)} required skills. Performing semantic matching...")
    
    # Step 2: Semantic matching with AI for each resume
    matches = []
    for resume in resumes:
        match_result = semantic_match_with_ai(jd_requirements, resume)
        matches.append(match_result)
    
    # Sort by score
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    # Filter good matches (>=75% for AI matching, more lenient than 80%)
    good_matches = [m for m in matches if m['score'] >= 75]
    
    if not good_matches:
        top = matches[:3]
        msg = f"❌ *No strong matches found* (threshold: 75%)\n\n"
        msg += f"📋 *Required Skills:*\n{', '.join(required_skills[:10])}\n\n"
        msg += "*Top Candidates (below threshold):*\n\n"
        
        for i, m in enumerate(top, 1):
            msg += f"{i}. *{m['resume_id']}* - {m['role']}\n"
            msg += f"   Score: {m['score']}%\n"
            msg += f"   Matched: {', '.join(m.get('matched_skills', [])[:5])}\n\n"
        
        send_telegram_message(chat_id, msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    # Best match found!
    best = good_matches[0]
    url = generate_presigned_url(best['s3_key'])
    
    msg = f"✅ *Best Match Found!* (AI-Powered)\n\n"
    msg += f"📄 *Resume:* {best['resume_id']}\n"
    msg += f"👔 *Role:* {best['role']}\n"
    msg += f"🎯 *Match Score:* {best['score']}%\n\n"
    msg += f"📋 *Required Skills:* {', '.join(required_skills[:8])}\n"
    msg += f"✅ *Matched:* {', '.join(best.get('matched_skills', [])[:8])}\n\n"
    
    if best.get('explanation'):
        msg += f"💡 *AI Analysis:*\n{best['explanation'][:200]}...\n\n"
    
    if url:
        msg += f"📥 [Download Resume]({url})\n\n"
    
    if len(good_matches) > 1:
        msg += f"*Other good matches ({len(good_matches)-1}):*\n"
        for m in good_matches[1:3]:
            msg += f"• {m['resume_id']} - {m['score']}%\n"
    
    msg += f"\n🤖 *Powered by Amazon Bedrock AI*"
    
    send_telegram_message(chat_id, msg, parse_mode='Markdown')
    return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}


def extract_jd_requirements_with_ai(jd_text: str) -> Dict:
    """
    Use AI to extract requirements from job description
    """
    try:
        prompt = f"""Analyze this job description and extract key information.

Job Description:
{jd_text[:3000]}

Extract and return ONLY a JSON object with:
{{
  "skills": ["skill1", "skill2", ...],
  "role": "job title",
  "experience_level": "junior/mid/senior",
  "key_requirements": ["req1", "req2", ...]
}}

Be comprehensive - include:
- Programming languages
- Cloud platforms
- Tools and technologies
- Methodologies (DevOps, Agile, etc.)
- Related/synonym skills (e.g., if "container orchestration" mentioned, include "kubernetes", "docker")

Return ONLY valid JSON, no explanation."""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1000,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        result_text = response_body['content'][0]['text'].strip()
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        requirements = json.loads(result_text)
        print(f"Extracted JD requirements: {requirements}")
        
        return requirements
        
    except Exception as e:
        print(f"Error extracting JD requirements: {str(e)}")
        # Fallback to simple extraction
        return {
            'skills': extract_skills_fallback(jd_text),
            'role': 'Not specified',
            'experience_level': 'Not specified',
            'key_requirements': []
        }


def semantic_match_with_ai(jd_requirements: Dict, resume: Dict) -> Dict:
    """
    Use AI to perform semantic matching between JD and resume
    """
    try:
        required_skills = jd_requirements.get('skills', [])
        resume_skills = resume.get('skills', [])
        
        prompt = f"""Compare these skills and provide a match analysis.

Required Skills (from Job Description):
{', '.join(required_skills)}

Candidate Skills (from Resume):
{', '.join(resume_skills)}

Analyze the match considering:
1. Direct matches (exact skill names)
2. Semantic matches (synonyms, related technologies)
3. Skill categories (e.g., "CI/CD" matches "Jenkins", "GitHub Actions")

Return ONLY a JSON object:
{{
  "match_score": 85,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill3"],
  "explanation": "Brief explanation of the match quality"
}}

Be generous with semantic matches. Examples:
- "container orchestration" matches "kubernetes", "docker"
- "CI/CD" matches "jenkins", "github actions", "gitlab"
- "infrastructure as code" matches "terraform", "ansible"
- "cloud" matches "aws", "azure", "gcp"

Match score should be 0-100. Return ONLY valid JSON."""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 800,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        result_text = response_body['content'][0]['text'].strip()
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        
        match_data = json.loads(result_text)
        
        return {
            'resume_id': resume['resume_id'],
            'role': resume.get('role', 'N/A'),
            'score': match_data.get('match_score', 0),
            's3_key': resume['s3_key'],
            'matched_skills': match_data.get('matched_skills', []),
            'missing_skills': match_data.get('missing_skills', []),
            'explanation': match_data.get('explanation', '')
        }
        
    except Exception as e:
        print(f"Error in semantic matching: {str(e)}")
        # Fallback to simple matching
        return {
            'resume_id': resume['resume_id'],
            'role': resume.get('role', 'N/A'),
            'score': calculate_match_score_simple(jd_requirements.get('skills', []), resume.get('skills', [])),
            's3_key': resume['s3_key'],
            'matched_skills': [],
            'missing_skills': [],
            'explanation': 'Fallback matching used'
        }


def calculate_match_score_simple(required: List[str], resume: List[str]) -> float:
    """Simple fallback matching"""
    if not required:
        return 0.0
    req_set = set(s.lower() for s in required)
    res_set = set(s.lower() for s in resume)
    matched = len(req_set.intersection(res_set))
    return round((matched / len(req_set)) * 100, 2)


# Keep all existing helper functions below...
def get_telegram_file(file_id: str) -> Optional[Dict]:
    """Get file info from Telegram"""
    if not BOT_TOKEN:
        return None
    
    http = urllib3.PoolManager()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile"
    
    try:
        response = http.request(
            'POST',
            url,
            body=json.dumps({'file_id': file_id}).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        data = json.loads(response.data.decode('utf-8'))
        if data.get('ok'):
            return data['result']
        return None
    except Exception as e:
        print(f"Error getting file info: {str(e)}")
        return None


def download_telegram_file(file_path: str) -> Optional[bytes]:
    """Download file from Telegram servers"""
    if not BOT_TOKEN:
        return None
    
    http = urllib3.PoolManager()
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    
    try:
        response = http.request('GET', url)
        if response.status == 200:
            return response.data
        return None
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
        return None


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    try:
        import PyPDF2
        import io
        
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        return ""


def detect_role_from_text(text: str) -> str:
    """Auto-detect role from resume text"""
    text_lower = text.lower()
    
    roles = {
        'DevOps Engineer': ['devops', 'site reliability', 'sre', 'platform engineer'],
        'Cloud Engineer': ['cloud engineer', 'cloud architect', 'aws engineer', 'solutions architect'],
        'Data Engineer': ['data engineer', 'data scientist', 'ml engineer', 'machine learning'],
        'Full Stack Developer': ['full stack', 'fullstack', 'full-stack'],
        'Backend Developer': ['backend', 'back-end', 'server-side'],
        'Frontend Developer': ['frontend', 'front-end', 'ui developer'],
    }
    
    for role, keywords in roles.items():
        for keyword in keywords:
            if keyword in text_lower:
                return role
    
    return 'Software Engineer'


def extract_skills_with_bedrock(resume_text: str) -> List[str]:
    """Use Bedrock to extract skills with enhanced prompt"""
    try:
        prompt = f"""Analyze this resume and extract ALL technical skills, tools, technologies, and methodologies.

Resume:
{resume_text[:4000]}

Be comprehensive and include variations. For example:
- If "Kubernetes" or "K8s" mentioned, include BOTH
- If "Jenkins" or "GitHub Actions" seen, also include "ci/cd"
- If cloud platforms mentioned, include general "cloud" term
- Include certifications as skills too

Return ONLY a JSON array of skills in lowercase.
Example: ["python", "aws", "docker", "kubernetes", "k8s", "ci/cd", "devops"]

Skills:"""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1500,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        response_body = json.loads(response['body'].read())
        skills_text = response_body['content'][0]['text'].strip()
        skills_text = skills_text.replace('```json', '').replace('```', '').strip()
        
        skills = json.loads(skills_text)
        
        if isinstance(skills, list):
            return list(set([s.lower().strip() for s in skills if s]))
        
        return []
        
    except Exception as e:
        print(f"Bedrock error: {str(e)}")
        return extract_skills_fallback(resume_text)


def extract_skills_fallback(text: str) -> List[str]:
    """Fallback skill extraction"""
    common_skills = [
        'python', 'java', 'javascript', 'typescript', 'go', 'golang', 'rust', 'c++', 'c#',
        'aws', 'azure', 'gcp', 'cloud', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible',
        'react', 'angular', 'vue', 'node', 'nodejs', 'django', 'flask', 'fastapi', 'spring',
        'sql', 'mongodb', 'postgresql', 'mysql', 'dynamodb', 'redis',
        'ci/cd', 'cicd', 'devops', 'jenkins', 'github actions', 'gitlab',
        'git', 'github', 'linux', 'bash', 'prometheus', 'grafana', 'cloudwatch'
    ]
    
    text_lower = text.lower()
    return list(set([skill for skill in common_skills if skill in text_lower]))


def send_telegram_message(chat_id: int, text: str, parse_mode: str = None):
    """Send message to Telegram"""
    if not BOT_TOKEN:
        print("No BOT_TOKEN")
        return
    
    http = urllib3.PoolManager()
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {'chat_id': chat_id, 'text': text}
    if parse_mode:
        payload['parse_mode'] = parse_mode
    
    try:
        http.request('POST', url, body=json.dumps(payload).encode('utf-8'),
                    headers={'Content-Type': 'application/json'})
    except Exception as e:
        print(f"Error sending message: {e}")


def get_all_resumes() -> List[Dict]:
    """Get all resumes from DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting resumes: {e}")
        return []


def generate_presigned_url(s3_key: str) -> str:
    """Generate presigned URL"""
    try:
        return s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET, 'Key': s3_key},
            ExpiresIn=3600
        )
    except Exception as e:
        print(f"Error generating URL: {e}")
        return ""


def handle_direct_api(body: Dict):
    """Handle direct API calls"""
    jd = body.get('job_description', '')
    if not jd:
        return {'statusCode': 400, 'body': json.dumps({'error': 'job_description required'})}
    
    # Use AI for API calls too
    jd_requirements = extract_jd_requirements_with_ai(jd)
    resumes = get_all_resumes()
    
    matches = []
    for resume in resumes:
        match_result = semantic_match_with_ai(jd_requirements, resume)
        if match_result['score'] >= 75:
            matches.append(match_result)
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    if not matches:
        return {'statusCode': 404, 'body': json.dumps({
            'message': 'No match found',
            'required_skills': jd_requirements.get('skills', [])
        })}
    
    best = matches[0]
    return {'statusCode': 200, 'body': json.dumps({
        'best_match': {
            'resume_id': best['resume_id'],
            'role': best['role'],
            'score': best['score'],
            'download_url': generate_presigned_url(best['s3_key']),
            'matched_skills': best.get('matched_skills', []),
            'explanation': best.get('explanation', '')
        },
        'all_matches': matches[:5]
    })}