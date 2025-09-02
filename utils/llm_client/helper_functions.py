import json
import re


def extract_json_from_response(response: str) -> dict:
    """Extract JSON from LLM response, handling various formats"""
    # Strip whitespace
    response = response.strip()
    json_match = bool(re.search(r"[`\n]", response))
    if json_match:
        json_match = response.replace("`", "").replace("\n", "").replace("json", "")
        try:
            response = json.loads(json_match)
            return response
        except json.decoder.JSONDecodeError:
            if not response.startswith("{") or not response.endswith("}"):
                response = "{" + response + "}"
                json_response = json.loads(response)
                return json_response

    if not response.startswith("{") or not response.endswith("}"):
        response = "{" + response + "}"
        json_response = json.loads(response)
        return json_response
    return {}
