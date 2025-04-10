from pymongo import MongoClient
from datetime import datetime


class MongoDB:
    def __init__(
        self,
        uri="mongodb+srv://inpantawat22:1234@agents.ci2qy.mongodb.net/",
        db_name="db_rezoome",
    ):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.resumes = self.db["resumes"]
        self.candidates_collection = self.db["candidates"]
        self.auth_message = self.db["inbox_auth"]
        self.job_descriptions = self.db["job_descriptions"]
        self.matching_results = self.db["results"]

    def get_all_job_descriptions(self):
        jobs = self.job_descriptions.find(
            {}, {"_id": 0, "position": 1, "requirements": 1, "embedding": 1}
        )
        return {
            job["position"]: {
                "requirements": " ".join(job["requirements"]),
                "embedding": job.get("embedding"),
            }
            for job in jobs
        }

    def insert_user(self, hr_id, name, email, role):
        user = {
            "_id": hr_id,
            "name": name,
            "email": email,
            "role": role,  # "HR" | "Candidate"
            "created_at": datetime.now(),
        }
        return self.users.insert_one(user).inserted_id

    def insert_auth_message(self, message_id):
        auth_message = {
            "message_id": message_id,
            "created_at": datetime.now(),
        }
        return self.auth_message.insert_one(auth_message).inserted_id

    def has_message_id(self, message_id):
        return self.auth_message.find_one({"message_id": message_id}) is not None

    def insert_candidate(self, candidate_id, personal_info, parsed_text, embedding):
        candidate_data = {
            "candidate_id": candidate_id,
            "name": personal_info.get("name"),
            "email": personal_info.get("email"),
            "phone": personal_info.get("phone"),
            "address": personal_info.get("address"),
            "education": personal_info.get("education"),
            "skills": personal_info.get("skills"),
            "work_experience": personal_info.get("work_experience"),
            "certifications": personal_info.get("certifications"),
            "projects": personal_info.get("projects"),
            "hobbies": personal_info.get("hobbies"),
            "references": personal_info.get("references"),
            "position": personal_info.get("position"),
            "languages": personal_info.get("languages"),
            "parsed_text": parsed_text,
            "embedding": embedding,
        }
        return self.candidates_collection.insert_one(candidate_data).inserted_id

    def insert_resume(self, resume_id, file_name, file_type):
        resumes = {
            "resume_id": resume_id,
            "file_name": file_name,
            "file_type": file_type,
            "uploaded_at": datetime.now(),
        }
        return self.resumes.insert_one(resumes).inserted_id

    def insert_job_description(self, job_id, position, requirements, embedding):
        job_descriptions = {
            "job_id": job_id,
            "position": position,
            "requirements": requirements,
            "embedding": embedding,
            "created_at": datetime.now().isoformat(),  # แปลงเวลาเป็น string
        }

        print("Inserting:", job_descriptions)  # Debug ก่อน insert

        try:
            result = self.db["job_descriptions"].insert_one(job_descriptions)
            print("Inserted ID:", result.inserted_id)  # Debug หลัง insert
            return result.inserted_id
        except Exception as e:
            print("Insert Error:", e)  # Debug error
            return None

    # def insert_result(self, resume_id, job_id, matching_score, explanation):
    #     result = {
    #         "resume_id": resume_id,
    #         "job_id": job_id,
    #         "matching_score": matching_score,
    #         "explanation": explanation,
    #         "analyzed_at": datetime.now(),
    #     }
    #     return self.matching_results.insert_one(result).inserted_id

    def get_user(self, email):
        return self.users.find_one({"email": email})

    def get_resume(self, resume_id):
        return self.resumes.find_one({"_id": resume_id})

    def get_job(self, job_id):
        return self.job_descriptions.find_one({"_id": job_id})

    # def get_results(self, resume_id):
    #     return list(self.matching_results.find({"resume_id": resume_id}))


if __name__ == "__main__":
    db = MongoDB()
    print("MongoDB connection established...")
