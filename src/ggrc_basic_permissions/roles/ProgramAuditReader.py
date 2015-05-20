scope = "AuditImplied"
description = """
  A user with the ProgramReader role for a private program will also have this
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
        "UserRole",
        "Context",
    ],
    "create": [
        "DocumentationResponse",
        "InterviewResponse",
        "Response",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Relationship",
        "Document"
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [
        {
            "terms": {
                "property_name": "assignee",
                "value": "$current_user"
            },
            "type": "Request",
            "condition": "is"
        },
        {
            "terms": {
                "property_name": "contact",
                "value": "$current_user"
            },
            "type": "DocumentationResponse",
            "condition": "is"
        },
        {
            "terms": {
                "property_name": "contact",
                "value": "$current_user"
            },
            "type": "InterviewResponse",
            "condition": "is"
        },
    ],
    "delete": [
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Relationship"
    ]
}
