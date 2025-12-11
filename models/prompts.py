"""
Prompt templates for resume generation with JSON output and seniority tiers.
Optimized for ATS (Applicant Tracking System) parsing.
"""

import json

# JSON schema for structured resume output - ATS-friendly structure
RESUME_SCHEMA = {
    "summary": "2-3 sentence professional summary with keywords",
    "skills": ["skill1", "skill2", "..."],
    "experience": [
        {
            "title": "Standard Job Title (no abbreviations)",
            "company": "Fictional Company Name",
            "location": "City, State",
            "start_date": "Month YYYY",
            "end_date": "Month YYYY or Present",
            "bullets": ["Action verb + task + result/metric", "..."]
        }
    ],
    "education": [
        {
            "degree": "Full Degree Name (e.g., Bachelor of Science in Computer Science)",
            "institution": "University Name",
            "year": "YYYY",
            "gpa": "3.X (optional, only if > 3.5)"
        }
    ],
    "certifications": ["Full Certification Name (Issuing Organization)"]
}

# Compact schema string for prompts
SCHEMA_STR = json.dumps(RESUME_SCHEMA, separators=(',', ':'))


def get_seniority_tier(years: int) -> str:
    """Determine seniority tier based on years of experience."""
    if years <= 4:
        return "junior"
    elif years <= 10:
        return "mid"
    return "senior"


# System prompt - ATS optimization rules
SYSTEM_PROMPT = """Generate fictional resume JSON optimized for ATS parsing.

ATS Rules:
- Use standard job titles (Software Engineer not SWE, Project Manager not PM)
- Dates as "Month YYYY" format (January 2023, not Jan 2023 or 01/2023)
- Start bullets with strong action verbs (Led, Developed, Implemented, Managed, Designed)
- Include quantified achievements (%, $, numbers) in bullets
- Skills as individual items, no compound skills
- Full degree names (Bachelor of Science, not BS or B.S.)
- Include industry keywords naturally in summary and bullets

Content Rules:
- All data fictional - no real people/companies
- Company names: use patterns like "Vertex Technologies", "Apex Solutions", "Summit Group"
- Dates must be logical: no overlaps, recent job ends "Present" or within 6 months
- Output valid JSON only"""


# Tier-specific prompts - ATS-optimized
TIER_PROMPTS = {
    "junior": """{role} in {industry}, {seniority}yrs exp.
1-2 jobs, education focus, 2-3 bullets each.
Include: relevant coursework/projects, internships count as jobs.
Skills: 8-12 relevant technical and soft skills.
Schema:{schema}""",

    "mid": """{role} in {industry}, {seniority}yrs exp.
3-4 jobs, balanced achievements, 3-4 bullets each.
Include: promotions, team leadership, project ownership.
Skills: 12-15 skills mixing technical expertise and domain knowledge.
Schema:{schema}""",

    "senior": """{role} in {industry}, {seniority}yrs exp.
4-5 jobs, leadership focus, 4-5 bullets each.
Include: team size managed, budget responsibility, strategic initiatives.
Skills: 15-20 skills including leadership, strategy, and technical expertise.
Schema:{schema}"""
}


def build_prompt(industry: str, role: str, seniority: int) -> tuple[str, str]:
    """
    Build system and user prompts for resume generation.

    Returns:
        tuple: (system_prompt, user_prompt)
    """
    tier = get_seniority_tier(seniority)

    user_prompt = TIER_PROMPTS[tier].format(
        role=role,
        industry=industry,
        seniority=seniority,
        schema=SCHEMA_STR
    )

    return SYSTEM_PROMPT, user_prompt
