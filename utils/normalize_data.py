def normalize_resume_data(raw_data: dict, candidate_id: str, parsed_text: str, embedding=None) -> dict:
    def safe_list(value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def safe_dict(value):
        return value if isinstance(value, dict) else {}

    def safe_education_list(value):
        if not isinstance(value, list):
            return []
        return [{
            "degree": item.get("degree"),
            "institution": item.get("institution"),
            "year": item.get("year"),
            "major": item.get("major"),
            "gpa": item.get("gpa")
        } for item in value]

    def safe_work_experience_list(value):
        if not isinstance(value, list):
            return []
        return [{
            "position": item.get("position"),
            "company": item.get("company"),
            "duration": item.get("duration"),
            "responsibilities": item.get("responsibilities")
        } for item in value]

    def safe_certifications_list(value):
        if not isinstance(value, list):
            return []
        return [{
            "name": item.get("name"),
            "issuer": item.get("issuer"),
            "year": item.get("year")
        } for item in value]

    def safe_projects_list(value):
        if not isinstance(value, list):
            return []
        return [{
            "name": item.get("name"),
            "description": item.get("description"),
            "year": item.get("year")
        } for item in value]

    def safe_references_list(value):
        if not isinstance(value, list):
            return []
        return [{
            "name": item.get("name"),
            "relationship": item.get("relationship"),
            "contact": item.get("contact")
        } for item in value]

    # Validate input parameters
    if not candidate_id or not parsed_text:
        raise ValueError("Candidate ID and parsed text are required")

    if raw_data is None:
        raw_data = {}

    # Normalize data
    normalized_data = {
        "candidate_id": candidate_id,
        "name": raw_data.get("name"),
        "email": raw_data.get("email"),
        "phone": raw_data.get("phone"),
        "address": raw_data.get("address"),
        "position": raw_data.get("position"),
        "education": safe_education_list(raw_data.get("education")),
        "work_experience": safe_work_experience_list(raw_data.get("work_experience")),
        "skills": {
            "technical": safe_list(raw_data.get("skills", {}).get("technical")),
            "soft": safe_list(raw_data.get("skills", {}).get("soft"))
        },
        "languages": safe_dict(raw_data.get("languages")),
        "certifications": safe_certifications_list(raw_data.get("certifications")),
        "projects": safe_projects_list(raw_data.get("projects")),
        "hobbies": safe_list(raw_data.get("hobbies")),
        "references": safe_references_list(raw_data.get("references")),
        "parsed_text": parsed_text,
        "embedding": embedding
    }

    return normalized_data
