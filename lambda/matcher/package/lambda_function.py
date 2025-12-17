import json
import os
import boto3
from typing import Dict, List, Optional
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
    """
    Main Lambda handler for resume matching and uploads
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Parse input
        body = json.loads(event.get('body', '{}'))
        
        # Check if this is a Telegram message
        if 'message' in body:
            return handle_telegram_message(body['message'])
        else:
            # Direct API call
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
    """
    Handle incoming Telegram message
    """
    chat_id = message['chat']['id']
    
    # Check if message contains a document (PDF)
    if 'document' in message:
        return handle_document_upload(message)
    
    # Regular text message
    text = message.get('text', '').strip()
    print(f"Telegram message from {chat_id}: {text}")
    
    # Handle commands
    if text.startswith('/start'):
        welcome_msg = """👋 *Welcome to Resume Matcher Bot!*

I can help you in two ways:

*1️⃣ Find Matching Resume:*
Send me a job description and I'll find the best matching resume!

*2️⃣ Upload New Resume:*
Send me a PDF resume file and I'll automatically:
- Extract skills using AI
- Save it to the system
- Make it available for matching

*Commands:*
/help - Get help
/list - See all available resumes
/stats - System statistics
/upload - Upload instructions

Just send a job description or a PDF file to get started! 🚀
"""
        send_telegram_message(chat_id, welcome_msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/help'):
        help_msg = """ℹ️ *Resume Matcher Bot Help*

*📄 To Upload Resume:*
1. Send me a PDF file
2. I'll extract skills automatically using AI
3. Done! Resume is saved

*🔍 To Find Match:*
Just send a job description like:
_"Looking for DevOps Engineer with AWS, Kubernetes, Docker"_

*📋 Commands:*
/list - View all resumes
/stats - System statistics
/upload - Upload instructions
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
            msg += f"  Skills: {', '.join(resume.get('skills', [])[:8])}\n\n"
        
        send_telegram_message(chat_id, msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/stats'):
        resumes = get_all_resumes()
        all_skills = set()
        for resume in resumes:
            all_skills.update(resume.get('skills', []))
        
        msg = f"📊 *System Statistics*\n\n"
        msg += f"Total Resumes: {len(resumes)}\n"
        msg += f"Total Unique Skills: {len(all_skills)}\n\n"
        if all_skills:
            msg += f"Skills: {', '.join(sorted(list(all_skills))[:15])}"
        
        send_telegram_message(chat_id, msg, parse_mode='Markdown')
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    if text.startswith('/upload'):
        upload_msg = """📤 *How to Upload Resume*

1️⃣ Send me a PDF file of the resume
2️⃣ I'll process it automatically
3️⃣ Skills are extracted using AI
4️⃣ Done! Resume is saved

*That's it!* Just send a PDF file now! 📄
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
    
    # Process as job description
    return process_job_description(chat_id, text)


def handle_document_upload(message: Dict):
    """
    Handle PDF resume upload from Telegram
    """
    chat_id = message['chat']['id']
    document = message['document']
    
    # Check if it's a PDF
    if document.get('mime_type') != 'application/pdf':
        send_telegram_message(chat_id, "⚠️ Please send a PDF file only!")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    try:
        send_telegram_message(chat_id, "📄 Processing your resume... This may take a moment.")
        
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
            send_telegram_message(chat_id, "❌ Could not extract text from PDF. Make sure it's a readable PDF!")
            return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
        print(f"Extracted text length: {len(resume_text)}")
        
        # Use Bedrock to extract skills
        send_telegram_message(chat_id, "🤖 Analyzing resume with AI to extract skills...")
        skills = extract_skills_with_bedrock(resume_text)
        
        if not skills:
            send_telegram_message(chat_id, "⚠️ Could not extract skills. Using fallback method...")
            skills = extract_skills_fallback(resume_text)
        
        # Auto-detect role from resume text
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
        
        # Send success message
        success_msg = f"""✅ *Resume Uploaded Successfully!*

📋 *Details:*
- Resume ID: `{resume_id}`
- Detected Role: {detected_role}
- Skills Found: {len(skills)}

🔧 *Extracted Skills:*
{', '.join(skills[:15])}{'...' if len(skills) > 15 else ''}

Your resume is now available for matching! 🎉
"""
        send_telegram_message(chat_id, success_msg, parse_mode='Markdown')
        
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
        
    except Exception as e:
        print(f"Error uploading document: {str(e)}")
        import traceback
        traceback.print_exc()
        send_telegram_message(chat_id, f"❌ Error processing resume: {str(e)}")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}


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
    """Use Bedrock to extract skills"""
    try:
        prompt = f"""Analyze this resume and extract ALL technical skills, tools, and technologies.

Resume:
{resume_text[:4000]}

Return ONLY a JSON array of skills in lowercase, no explanation.
Example: ["python", "aws", "docker"]

Skills:"""

        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1024,
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
        'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
        'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
        'sql', 'mongodb', 'postgresql', 'mysql', 'redis', 'dynamodb',
        'ci/cd', 'devops', 'jenkins', 'gitlab', 'github', 'git', 'linux'
    ]
    
    text_lower = text.lower()
    return list(set([skill for skill in common_skills if skill in text_lower]))


def process_job_description(chat_id: int, job_description: str):
    """Process job description and find matches"""
    send_telegram_message(chat_id, "🔍 Analyzing job description...")
    
    required_skills = extract_skills_from_jd(job_description)
    
    if not required_skills:
        send_telegram_message(chat_id, "❌ Couldn't extract skills. Try: Python, AWS, Docker, etc.")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    resumes = get_all_resumes()
    
    if not resumes:
        send_telegram_message(chat_id, "⚠️ No resumes in database. Upload one by sending a PDF!")
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    matches = []
    for resume in resumes:
        score = calculate_match_score(required_skills, resume.get('skills', []))
        matches.append({
            'resume_id': resume['resume_id'],
            'role': resume.get('role', 'N/A'),
            'score': score,
            's3_key': resume['s3_key'],
            'skills': resume.get('skills', [])
        })
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    good_matches = [m for m in matches if m['score'] >= 80]
    
    if not good_matches:
        top = matches[:3]
        msg = f"❌ No strong matches (need 80%)\n\n📋 Skills: {', '.join(required_skills)}\n\nTop:\n"
        for i, m in enumerate(top, 1):
            msg += f"{i}. {m['resume_id']} - {m['score']}%\n"
        send_telegram_message(chat_id, msg)
        return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}
    
    best = good_matches[0]
    url = generate_presigned_url(best['s3_key'])
    matched = [s for s in best['skills'] if s.lower() in [r.lower() for r in required_skills]]
    
    msg = f"✅ *Best Match!*\n\n📄 {best['resume_id']}\n👔 {best['role']}\n🎯 {best['score']}%\n\n"
    msg += f"📋 Required: {', '.join(required_skills)}\n✓ Matched: {', '.join(matched)}\n\n"
    if url:
        msg += f"📥 [Download]({url})"
    
    send_telegram_message(chat_id, msg, parse_mode='Markdown')
    return {'statusCode': 200, 'body': json.dumps({'message': 'OK'})}


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


def extract_skills_from_jd(jd: str) -> List[str]:
    """Extract skills from job description"""
    skills = [
        'python', 'java', 'javascript', 'typescript', 'go', 'rust',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'k8s', 'terraform', 'ansible',
        'react', 'angular', 'vue', 'node', 'nodejs', 'django', 'flask',
        'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'dynamodb',
        'ci/cd', 'devops', 'jenkins', 'gitlab', 'github', 'linux', 'bash'
    ]
    return [s for s in skills if s in jd.lower()]


def get_all_resumes() -> List[Dict]:
    """Get all resumes from DynamoDB"""
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting resumes: {e}")
        return []


def calculate_match_score(required: List[str], resume: List[str]) -> float:
    """Calculate match score"""
    if not required:
        return 0.0
    req_set = set(s.lower() for s in required)
    res_set = set(s.lower() for s in resume)
    matched = len(req_set.intersection(res_set))
    return round((matched / len(req_set)) * 100, 2)


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
    
    required_skills = extract_skills_from_jd(jd)
    resumes = get_all_resumes()
    
    matches = [{'resume_id': r['resume_id'], 'role': r['role'], 
                'score': calculate_match_score(required_skills, r.get('skills', [])),
                's3_key': r['s3_key']}
               for r in resumes if calculate_match_score(required_skills, r.get('skills', [])) >= 80]
    
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    if not matches:
        return {'statusCode': 404, 'body': json.dumps({'message': 'No match', 'required_skills': required_skills})}
    
    best = matches[0]
    return {'statusCode': 200, 'body': json.dumps({
        'best_match': {'resume_id': best['resume_id'], 'role': best['role'], 
                      'score': best['score'], 'download_url': generate_presigned_url(best['s3_key'])},
        'all_matches': matches
    })}