def match_skills(job_skills: list, resume_skills: list) -> dict:
    if not job_skills:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "skill_match_score": 0
        }
    
    job_skills_set = set(str(skill).lower() for skill in job_skills if skill)
    resume_skills_set = set(str(skill).lower() for skill in resume_skills if skill)

    matched = job_skills_set.intersection(resume_skills_set)
    missing = job_skills_set - resume_skills_set

    score = int((len(matched) / len(job_skills_set)) * 100) if job_skills_set else 0

    return {
        "matched_skills": list(matched),
        "missing_skills": list(missing),
        "skill_match_score": score
    }
