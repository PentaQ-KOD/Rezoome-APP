# Rezoome - APP

This API provides endpoints to interact with the Resume Atlas system, allowing you to parse PDFs, analyze resumes, classify text, generate embeddings, and more.

## Features

- Parse and extract structured information from PDF resumes
- Generate embeddings for text using local Ollama model
- Classify text documents
- Analyze resumes against job descriptions for matching
- Fetch and process emails with resume attachments
- Store and retrieve job descriptions
- Supports both JSON and form data inputs for flexibility

## Getting Started

### Prerequisites

- Python 3.8+
- MongoDB
- Ollama running locally with the 'bge-m3' model

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resume-atlas.git
cd resume-atlas
```

2. Install dependencies:
```bash
pip install -r api-requirements.txt
```

3. Make sure your MongoDB instance is running and accessible.

4. Start the API server:
```bash
python run_api.py
```

The API will be available at `http://localhost:8000`.

### API Documentation

After starting the server, you can access the API documentation at `http://localhost:8000/docs`.

## API Endpoints

All endpoints support both form data and JSON request bodies, so you can use what's most convenient for your client application.

### `/parse-pdf`

Parse a PDF file and extract structured information.

**Method**: POST  
**Parameters**:
- `file`: PDF file upload

**Response**:
```json
{
  "resume_text": "Full text of the resume",
  "resume_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "123-456-7890",
    "address": "123 Main St, City, Country",
    "position": "Software Engineer",
    "education": "Bachelor of Science in Computer Science",
    "work_experience": "...",
    "skills": ["Python", "JavaScript", "Machine Learning"],
    "languages": ["English", "Spanish"],
    "certifications": ["AWS Certified Developer"],
    "projects": ["..."],
    "hobbies": ["..."],
    "references": ["..."]
  }
}
```

### `/get-embedding`

Generate an embedding vector for a given text.

**Method**: POST  
**Parameters** (Form or JSON):
- `text`: Text to embed

**Example JSON**:
```json
{
  "text": "This is the text to embed"
}
```

**Response**:
```json
{
  "embedding": [0.1, 0.2, 0.3, ...]
}
```

### `/classify-text`

Classify text into one of several predefined categories.

**Method**: POST  
**Parameters** (Form or JSON):
- `text`: Text to classify

**Example JSON**:
```json
{
  "text": "This is the text to classify"
}
```

**Response**:
```json
{
  "classification": "Resume/CV"
}
```

### `/analyze-resume`

Analyze a resume against available job descriptions to determine compatibility.

**Method**: POST  
**Parameters** (Form or JSON):
- `resume_text`: Resume text to analyze
- `optimize`: (Optional) Whether to use LLM to optimize the analysis (default: false)

**Example JSON**:
```json
{
  "resume_text": "Resume text content...",
  "optimize": true
}
```

**Response**:
```json
{
  "results": {
    "Software Engineer": "85.2%",
    "Data Scientist": "72.6%"
  }
}
```

### `/call-llm`

Send a prompt to the LLM and get a response.

**Method**: POST  
**Parameters** (Form or JSON):
- `prompt`: Prompt to send to the LLM

**Example JSON**:
```json
{
  "prompt": "What are the key skills for a data scientist?"
}
```

**Response**:
```json
{
  "response": "LLM response text"
}
```

### `/fetch-emails`

Fetch emails and process resume attachments (runs in background).

**Method**: POST  
**Parameters** (Form or JSON):
- `email_address`: Email address to fetch from
- `password`: Email password
- `imap_server`: (Optional) IMAP server (default: "imap.zoho.com")

**Example JSON**:
```json
{
  "email_address": "your@email.com",
  "password": "your_password",
  "imap_server": "imap.zoho.com"
}
```

**Response**:
```json
{
  "message": "Email fetching started in background"
}
```

### `/job-descriptions`

Get all job descriptions.

**Method**: GET  

**Response**:
```json
{
  "job_descriptions": {
    "Software Engineer": {
      "requirements": "Experience with Python, JavaScript, and cloud technologies",
      "embedding": [0.1, 0.2, 0.3, ...]
    },
    "Data Scientist": {
      "requirements": "Experience with machine learning, data analysis, and Python",
      "embedding": [0.4, 0.5, 0.6, ...]
    }
  }
}
```

### `/job-description`

Add a new job description.

**Method**: POST  
**Parameters** (Form or JSON):
- `position`: Job position title
- `requirements`: List of job requirements

**Example JSON**:
```json
{
  "position": "Data Analyst",
  "requirements": ["Python", "SQL", "Data visualization", "Statistical analysis"]
}
```

**Response**:
```json
{
  "message": "Job description added successfully",
  "job_id": "1234-5678-9101"
}
```

## Testing

A test script is included to verify the API functionality. You can run it with:

```bash
python test_api.py
```

## License

This project is licensed under the MIT License. 
