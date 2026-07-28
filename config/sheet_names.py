"""Worksheet names and required schemas for RecruitOS configuration."""

SKILLS = "Skills"
EDUCATION = "Education"
CERTIFICATIONS = "Certifications"
COMPANIES = "Companies"
LOCATIONS = "Locations"
DOMAINS = "Domains"
LANGUAGES = "Languages"
ROLES = "Roles"
INDUSTRIES = "Industries"
SCORING = "Scoring"
RECOMMENDATION = "Recommendation"
CONFIGURATION = "Configuration"

ALL_SHEETS = [
    SKILLS,
    EDUCATION,
    CERTIFICATIONS,
    COMPANIES,
    LOCATIONS,
    DOMAINS,
    LANGUAGES,
    ROLES,
    INDUSTRIES,
    SCORING,
    RECOMMENDATION,
    CONFIGURATION,
]

# Structural schema only. Business values remain in the workbook.
REQUIRED_COLUMNS = {
    SKILLS: ("Skill", "Category", "Synonyms", "Active"),
    EDUCATION: ("Education", "Alias", "Priority", "Active"),
    CERTIFICATIONS: ("Certification", "Alias", "Category", "Active"),
    COMPANIES: ("Company", "Alias", "Industry", "Active"),
    LOCATIONS: ("Country", "State", "City", "Active"),
    DOMAINS: ("Domain", "Description", "Active"),
    LANGUAGES: ("Language", "Category", "Active"),
    ROLES: ("Role", "Department", "Active"),
    INDUSTRIES: ("Industry", "Description", "Active"),
    SCORING: ("Component", "Weight", "Active", "Remarks"),
    RECOMMENDATION: ("Minimum Score", "Maximum Score", "Recommendation"),
    CONFIGURATION: ("Key", "Value"),
}
