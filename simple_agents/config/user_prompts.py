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


def get_user_prompt_for_summary(previous_summary: str, latest_message: str):
    user_prompt_for_summary = f"""
    Previous summary: {previous_summary}
    Latest user query or computer response: "{latest_message}"
    
    Update the summary so it reflects the current state of the conversation.
    """
    return user_prompt_for_summary
