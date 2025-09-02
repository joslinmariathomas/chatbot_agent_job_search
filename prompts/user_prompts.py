user_prompt_to_identify_query_type = """Analyze this query and extract structured information. 
        Return ONLY valid JSON in this exact format:
        {"query_type":"<query type>"} 
        user query:
        """
user_prompt_to_identify_job = """Analyze this query and extract job user is interested in. 
                Return ONLY valid JSON in this exact schema:
                "job_position":"<job_position>" 
                user query:
                """
user_prompt_to_identify_location = """Analyze this query and extract location user is interested in. 
                Return ONLY valid JSON in this exact schema:
                {"location":"<location>"} 
                user query:
                """
user_prompt_to_extract_resume_details = """
Here is a candidate CV in markdown format. 
Extract the details into the structured JSON format as defined above. 

CV:
"""

user_prompt_to_extract_job_features = """
        Analyze this job description and extract structured information. Return ONLY valid JSON in this exact format:

        {
            "required_skills": ["skill1", "skill2"],
            "preferred_skills": ["skill3", "skill4"],
            "experience_level": "3-5 years",
            "education": ["Bachelor's in Computer Science"],
            "technologies": ["Python", "SQL", "AWS"],
            "soft_skills": ["Communication", "Problem-solving"],
            "salary_range": "$80,000 - $120,000",
            "employment_type": "full-time",
        }

        Job Description:
        """


def get_user_prompt_for_summary(previous_summary: str, latest_message: str):
    user_prompt_for_summary = f"""
    Previous summary: {previous_summary}
    Latest user query or computer response: "{latest_message}"
    
    Update the summary so it reflects the current state of the conversation.
    """
    return user_prompt_for_summary
