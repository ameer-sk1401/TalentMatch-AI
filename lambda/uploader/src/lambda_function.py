import json
import os
import boto3
import base64
from datetime import datetime
from typing import Dict, List
import PyPDF2
import io

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')

# Environment variables
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE_NAME')

def lambda_handler(event, context):
    """
    Handle resume upload and processing
    """
    try:
        print(f"Received event: {json.dumps(event)}")
        
        # Parse input
        body = json.loads(event.get('body', '{}'))
        
        # Get resume data (base64 encoded PDF)
        resume_data = body.get('resume_data')  # Base64 encoded PDF
        resume_name = body.get('resume_name', 'resume.pdf')
        role = body.get('role', 'General')
        
        if not resume_data:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'resume_data (base64 encoded PDF) is required'})
            }
        
        # Decode PDF
        try:
            pdf_bytes = base64.b64decode(resume_data)
        except Exception as e:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Invalid base64 data: {str(e)}'})
            }
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(pdf_bytes)
        
        if not resume_text:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Could not extract text from PDF'})
            }
        
        print(f"Extracted resume text (first 500 chars): {resume_text[:500]}")
        
        # Use Bedrock to extract skills
        skills = extract_skills_with_bedrock(resume_text)
        
        print(f"Extracted skills: {skills}")
        
        # Generate unique resume ID
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        resume_id = f"{role.lower().replace(' ', '_')}_{timestamp}"
        
        # Upload to S3
        s3_key = f"resumes/{role.lower().replace(' ', '-')}/{resume_name}"
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
                'role': role,
                'skills': skills,
                's3_key': s3_key,
                'created_at': datetime.utcnow().isoformat(),
                'filename': resume_name
            }
        )
        
        print(f"Saved metadata to DynamoDB: {resume_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Resume uploaded and processed successfully',
                'resume_id': resume_id,
                'skills_extracted': skills,
                's3_key': s3_key,
                'role': role
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes
    """
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        return ""


def extract_skills_with_bedrock(resume_text: str) -> List[str]:
    """
    Use Amazon Bedrock (Claude) to intelligently extract skills from resume
    """
    try:
        prompt = f"""Analyze this resume and extract ALL technical skills, tools, and technologies mentioned.

Resume:
{resume_text[:4000]}  # Limit to avoid token limits

Return ONLY a JSON array of skills in lowercase, with no explanation or markdown formatting.
Include:
- Programming languages (python, java, javascript, etc.)
- Cloud platforms (aws, azure, gcp)
- Tools (docker, kubernetes, terraform, jenkins, etc.)
- Databases (postgresql, mongodb, redis, etc.)
- Frameworks (react, django, spring, etc.)
- Methodologies (agile, devops, ci/cd, etc.)

Example format: ["python", "aws", "docker", "kubernetes", "terraform"]

Skills:"""

        # Call Bedrock (Claude 3 Haiku - fast and cheap)
        response = bedrock_runtime.invoke_model(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 1024,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            })
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        skills_text = response_body['content'][0]['text'].strip()
        
        print(f"Bedrock raw response: {skills_text}")
        
        # Clean up response (remove markdown formatting if present)
        skills_text = skills_text.replace('```json', '').replace('```', '').strip()
        
        # Parse JSON
        skills = json.loads(skills_text)
        
        # Ensure it's a list and deduplicate
        if isinstance(skills, list):
            return list(set([s.lower().strip() for s in skills if s]))
        
        return []
        
    except Exception as e:
        print(f"Error extracting skills with Bedrock: {str(e)}")
        # Fallback to basic keyword extraction
        return extract_skills_fallback(resume_text)


def extract_skills_fallback(resume_text: str) -> List[str]:
    """
    Fallback: Basic keyword matching if Bedrock fails
    """
    common_skills = [
        'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#',
        'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible',
        'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring',
        'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'dynamodb', 'redis',
        'jenkins', 'gitlab', 'github', 'ci/cd', 'devops', 'agile', 'scrum',
        'linux', 'bash', 'git', 'rest api', 'graphql', 'microservices'
    ]
    
    text_lower = resume_text.lower()
    found_skills = [skill for skill in common_skills if skill in text_lower]
    
    return list(set(found_skills))
