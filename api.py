# =============================================================================
# Imports and Configurations
# =============================================================================
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import tempfile
import uuid
import json
import os
from modules.parse_pdf import ResumeProcessor
from modules.email_fetcher import fetch_attachments_and_classify
from modules.job_description import analyze_resume, call_llama
from modules.classify_text import classify_text
from modules.embed import get_embedding
from utils.database import MongoDB
import uvicorn
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader

# Load environment variables
load_dotenv()

# =============================================================================
# FastAPI App Configuration
# =============================================================================
app = FastAPI(
    title="Resume Atlas API",
    description="API for Rezoome-APP",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = MongoDB()
resume_processor = ResumeProcessor()

# =============================================================================
# Pydantic Models for Request/Response
# =============================================================================
class EmailCredentials(BaseModel):
    email_address: str
    password: str
    imap_server: Optional[str] = "imap.zoho.com"

class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    optimize: Optional[bool] = False

class TextRequest(BaseModel):
    text: str

class LLMRequest(BaseModel):
    prompt: str

class JobDescriptionRequest(BaseModel):
    position: str
    requirements: List[str]

class ResumeInfoResponse(BaseModel):
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    position: Optional[str]
    education: Optional[str]
    work_experience: Optional[str]
    skills: Optional[List[str]]
    languages: Optional[List[str]]
    certifications: Optional[List[str]]
    projects: Optional[List[str]]
    hobbies: Optional[List[str]]
    references: Optional[List[str]]

class CandidateResponse(BaseModel):
    candidate_id: str
    name: Optional[str] = None 
    email: Optional[str] = None
    phone: Optional[str] = None
    position: Optional[str] = None
    education: Optional[List[Dict[str, Any]]] = None
    work_experience: Optional[List[Dict[str, Any]]] = None
    skills: Optional[Dict[str, List[str]]] = None
    languages: Optional[Dict[str, str]] = None
    certifications: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None

class EmailRequest(BaseModel):
    to: str
    subject: str
    body: str

class StatusResponse(BaseModel):
    status: str
    version: str
    uptime: float

# =============================================================================
# Basic Routes
# =============================================================================
@app.get("/")
async def root():
    """Welcome endpoint"""
    return {"message": "Welcome to Resume Atlas API"}

@app.get("/status")
async def get_status():
    """Get API status and version information"""
    import time
    return StatusResponse(
        status="running",
        version="1.0.0",
        uptime=time.time()
    )

# =============================================================================
# Resume Processing Routes
# =============================================================================
@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """Parse a PDF file and extract text content"""
    try:
        # Save the uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # First try using load_pdf which uses LlamaParse
            resume_text = resume_processor.load_pdf(temp_path)
            if not resume_text or resume_text.strip() == "":
                # Fallback to PyPDFLoader if LlamaParse fails
                try:
                    print("LlamaParse failed, trying PyPDFLoader fallback...")
                    loader = PyPDFLoader(temp_path)
                    documents = loader.load()
                    resume_text = "\n".join([doc.page_content for doc in documents])
                    if not resume_text or resume_text.strip() == "":
                        raise HTTPException(status_code=400, detail="Failed to extract text from PDF file")
                except Exception as pdf_error:
                    print(f"PyPDFLoader fallback failed: {pdf_error}")
                    raise HTTPException(status_code=400, detail="Failed to parse PDF file using all available methods")
        except Exception as parse_error:
            print(f"Error in parsing PDF: {parse_error}")
            # Try the fallback method if the primary method fails
            try:
                print("Trying PyPDFLoader fallback after exception...")
                loader = PyPDFLoader(temp_path)
                documents = loader.load()
                resume_text = "\n".join([doc.page_content for doc in documents])
                if not resume_text or resume_text.strip() == "":
                    raise HTTPException(status_code=400, detail="Failed to extract text from PDF file")
            except Exception as pdf_error:
                print(f"PyPDFLoader fallback failed: {pdf_error}")
                raise HTTPException(status_code=400, detail=f"Failed to parse PDF file: {str(parse_error)}")
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return {"resume_text": resume_text}
    except HTTPException as http_exc:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise http_exc
    except Exception as e:
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/extract-resume-info")
async def extract_resume_info(
    text_data: Optional[TextRequest] = Body(None),
    text_form: Optional[str] = Form(None)
):
    """Extract structured information from resume text."""
    try:
        input_text = text_form or (text_data.text if text_data else None)
        if not input_text:
            raise HTTPException(status_code=400, detail="No text provided")

        try:
            resume_info = resume_processor.extract_resume_info(input_text)
            if not resume_info:
                raise HTTPException(status_code=400, detail="Failed to extract resume information")
            return {"resume_info": resume_info}
        except Exception as extract_error:
            print(f"Error extracting resume info: {extract_error}")
            raise HTTPException(
                status_code=400,
                detail="Failed to extract resume information. Make sure the input text is from a resume/CV document."
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume text: {str(e)}")

@app.post("/analyze-resume")
async def analyze_resume_endpoint(
    analysis_request: ResumeAnalysisRequest = Body(...)):
    try:
        input_text = analysis_request.resume_text.strip()
        should_optimize = analysis_request.optimize

        if not input_text:
            raise HTTPException(status_code=400, detail="Resume text cannot be empty")

        results = analyze_resume(input_text, should_optimize)
        return {"results": results}
    
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

# =============================================================================
# Text Processing Routes
# =============================================================================
@app.post("/get-embedding")
async def create_embedding(
    text_data: Optional[TextRequest] = Body(None)
):
    """Generate text embedding vector from JSON"""
    try:
        input_text = text_data.text if text_data else None
        if not input_text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        embedding = get_embedding(input_text)
        if not embedding:
            raise HTTPException(status_code=400, detail="Failed to generate embedding")
        
        return {"embedding": embedding}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

@app.post("/classify-text")
async def classify_text_endpoint(text_data: TextRequest):
    """Classify text into predefined categories"""
    try:
        input_text = text_data.text
        if not input_text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        classification = classify_text(input_text)
        if not classification:
            raise HTTPException(status_code=400, detail="Failed to classify text")
        
        return {"classification": classification}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying text: {str(e)}")

@app.post("/call-llm")
async def call_llm(
    llm_request: LLMRequest 
):
    """Call LLM model with a prompt"""
    try:
        input_prompt = llm_request.prompt
        if not input_prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        response_text = "".join(list(call_llama(input_prompt)))
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")


# =============================================================================
# Email Management Routes
# =============================================================================
@app.post("/fetch-emails")
async def fetch_emails(
    background_tasks: BackgroundTasks,
    credentials: Optional[EmailCredentials] = Body(None),
    email_address: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    imap_server: Optional[str] = Form("imap.zoho.com")
):
    """Fetch and process emails from IMAP server"""
    try:
        email = email_address or (credentials.email_address if credentials else None)
        pwd = password or (credentials.password if credentials else None)
        server = imap_server or (credentials.imap_server if credentials else "imap.zoho.com")
        
        if not email or not pwd:
            raise HTTPException(status_code=400, detail="Email address and password are required")
        
        background_tasks.add_task(
            fetch_attachments_and_classify,
            email,
            pwd,
            server
        )
        return {"message": "Email fetching started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@app.post("/email/send")
async def send_email(email_request: EmailRequest):
    """Send email to a candidate"""
    from modules.email_sender import send_email, get_email_settings
    try:
        settings = get_email_settings()
        email_credentials = {
            'email': os.getenv('EMAIL_USER'),
            'password': os.getenv('EMAIL_PASSWORD'),
            'smtp_server': settings['smtp_server'],
            'smtp_port': settings['smtp_port']
        }
        
        result = send_email(
            recipient_email=email_request.to,
            subject=email_request.subject,
            body=email_request.body,
            sender_email=email_credentials['email'],
            sender_password=email_credentials['password'],
            smtp_server=email_credentials['smtp_server'],
            smtp_port=email_credentials['smtp_port']
        )
        
        if result[0]:
            return {"message": "Email sent successfully"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to send email: {result[1]}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")

# =============================================================================
# Job Management Routes
# =============================================================================
@app.get("/job-descriptions")
async def get_job_descriptions():
    """Get all job descriptions"""
    try:
        job_descriptions = db.get_all_job_descriptions()
        return {"job_descriptions": job_descriptions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching job descriptions: {str(e)}")

@app.post("/job-description")
async def add_job_description(
    job_data: Optional[JobDescriptionRequest] = Body(None),
    position: Optional[str] = Form(None),
    requirements: Optional[List[str]] = Form(None)
):
    """Add a new job description"""
    try:
        job_position = position or (job_data.position if job_data else None)
        job_requirements = requirements or (job_data.requirements if job_data else None)
        
        if not job_position or not job_requirements:
            raise HTTPException(status_code=400, detail="Position and requirements are required")
        
        job_id = str(uuid.uuid4())
        req_text = " ".join(job_requirements)
        embedding = get_embedding(req_text)
        
        db.insert_job_description(job_id, job_position, job_requirements, embedding)
        
        return {"message": "Job description added successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding job description: {str(e)}")

# =============================================================================
# Candidate Management Routes
# =============================================================================
@app.get("/candidates", response_model=List[CandidateResponse])
async def get_candidates():
    """Get all candidates"""
    try:
        candidates = list(db.candidates_collection.find())
        return candidates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidates: {str(e)}")

@app.get("/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    """Get candidate by ID"""
    try:
        candidate = db.candidates_collection.find_one({"candidate_id": candidate_id})
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        return candidate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching candidate: {str(e)}")

@app.get("/matches/{candidate_id}")
async def get_matches(candidate_id: str):
    """Get job matches for a candidate"""
    try:
        matches = db.matching_results_collection.find_one({"candidate_id": candidate_id})
        if not matches:
            raise HTTPException(status_code=404, detail="No matches found for candidate")

        # แปลง ObjectId เป็น string ก่อนส่งกลับ
        matches["_id"] = str(matches["_id"])
        return matches

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching matches: {str(e)}")

# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)