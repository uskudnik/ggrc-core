scope = "Audit Implied"
description = """
  A user with the ProgramOwner role for a private program will also have this
  role in the audit context for any audit created for that program.
  """
permissions = {
    "read": [
        "Request",
        "ControlAssessment",
        "Issue",
        "DocumentationResponse",
        "InterviewResponse",
        "PopulationSampleResponse",
        "UserRole",
        "Audit",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Relationship",
        "Document",
        "Meeting",
        "Context",
    ],
    "create": [
        "Request",
        "ControlAssessment",
        "Issue",
        "DocumentationResponse",
        "InterviewResponse",
        "PopulationSampleResponse",
        "UserRole",
        "Audit",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Relationship",
        "Document",
        "Meeting",
        "Response"
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [
        "Request",
        "ControlAssessment",
        "Issue",
        "DocumentationResponse",
        "InterviewResponse",
        "PopulationSampleResponse",
        "UserRole",
        "Audit",
        "AuditObject",
        "Meeting",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Relationship",
        "Document",
        "Meeting"
    ],
    "delete": [
        "UserRole",
        "ControlAssessment",
        "Issue",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Relationship",
        "Document",
        "Meeting"
        "AuditObject",
        "Audit"
    ]
}
