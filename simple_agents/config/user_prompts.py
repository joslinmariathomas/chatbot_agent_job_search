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
