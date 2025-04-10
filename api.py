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
from database import MongoDB
import uvicorn
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader

load_dotenv()

app = FastAPI(
    title="Resume Atlas API",
    description="API for Resume Atlas functionality",
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

# Initialize database and resume processor
db = MongoDB()
resume_processor = ResumeProcessor()

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

@app.get("/")
async def root():
    return {"message": "Welcome to Resume Atlas API"}

@app.post("/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
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
                # If LlamaParse fails, fall back to PyPDFLoader
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
        
        # Extract resume information
        resume_info = resume_processor.extract_resume_info(resume_text)
        
        # Clean up the temporary file
        os.unlink(temp_path)
        
        return {"resume_text": resume_text, "resume_info": resume_info}
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        raise http_exc
    except Exception as e:
        # Check if temp file exists and clean up
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/get-embedding")
async def create_embedding(
    text_data: Optional[TextRequest] = Body(None),
    text: Optional[str] = Form(None)
):
    try:
        # Get text from either form data or JSON body
        input_text = text or (text_data.text if text_data else None)
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
    input_text = text_data.text
    try:
        # Get text from either form data or JSON body
        #input_text = text or (text_data.text if text_data else None)
        if not input_text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        classification = classify_text(input_text)
        if not classification:
            raise HTTPException(status_code=400, detail="Failed to classify text")
        
        return {"classification": classification}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error classifying text: {str(e)}")

@app.post("/analyze-resume")
async def analyze_resume_endpoint(
    analysis_request: Optional[ResumeAnalysisRequest] = Body(None),
    resume_text: Optional[str] = Form(None),
    optimize: Optional[bool] = Form(False)
):
    try:
        # Get data from either form data or JSON body
        input_text = resume_text or (analysis_request.resume_text if analysis_request else None)
        should_optimize = optimize or (analysis_request.optimize if analysis_request else False)
        
        if not input_text:
            raise HTTPException(status_code=400, detail="No resume text provided")
        
        results = analyze_resume(input_text, should_optimize)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

@app.post("/call-llm")
async def call_llm(
    llm_request: Optional[LLMRequest] = Body(None),
    prompt: Optional[str] = Form(None)
):
    try:
        # Get prompt from either form data or JSON body
        input_prompt = prompt or (llm_request.prompt if llm_request else None)
        if not input_prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Since call_llama is a generator, we need to collect its output
        response_text = "".join(list(call_llama(input_prompt)))
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling LLM: {str(e)}")

@app.post("/fetch-emails")
async def fetch_emails(
    background_tasks: BackgroundTasks,
    credentials: Optional[EmailCredentials] = Body(None),
    email_address: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    imap_server: Optional[str] = Form("imap.zoho.com")
):
    try:
        # Get credentials from either form data or JSON body
        email = email_address or (credentials.email_address if credentials else None)
        pwd = password or (credentials.password if credentials else None)
        server = imap_server or (credentials.imap_server if credentials else "imap.zoho.com")
        
        if not email or not pwd:
            raise HTTPException(status_code=400, detail="Email address and password are required")
        
        # Run email fetching in background to avoid timeout
        background_tasks.add_task(
            fetch_attachments_and_classify,
            email,
            pwd,
            server
        )
        return {"message": "Email fetching started in background"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching emails: {str(e)}")

@app.get("/job-descriptions")
async def get_job_descriptions():
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
    try:
        # Get data from either form data or JSON body
        job_position = position or (job_data.position if job_data else None)
        job_requirements = requirements or (job_data.requirements if job_data else None)
        
        if not job_position or not job_requirements:
            raise HTTPException(status_code=400, detail="Position and requirements are required")
        
        # Generate a unique ID for the job
        job_id = str(uuid.uuid4())
        
        # Join requirements into a single string for embedding
        req_text = " ".join(job_requirements)
        
        # Generate embedding for the requirements
        embedding = get_embedding(req_text)
        
        # Insert job description into database
        db.insert_job_description(job_id, job_position, job_requirements, embedding)
        
        return {"message": "Job description added successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding job description: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)