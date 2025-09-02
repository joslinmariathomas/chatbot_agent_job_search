from utils.resume_extractor.resume_parser import CVParser


def test_resume_parser():
    cv_parser = CVParser()
    with open("resume.pdf", "rb") as file:
        cv_parser.parse_resume(resume_pdf=file)
    assert cv_parser.parsed_uploaded_resume == True

    resume_features_extracted = cv_parser.extract_requirements(cv_parser.resume_in_text)
    assert resume_features_extracted is not None
