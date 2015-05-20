scope = "Audit"
description = """
  The permissions required by an auditor to access relevant resources for the
  program being audited.
  """
permissions = {
    "read": [
        "Audit",
        "Request",
        "ControlAssessment",
        "Issue",
        {
            "terms": {
                "property_name": "status",
                "value": [
                    "Submitted",
                    "Accepted",
                    "Rejected"
                ]
            },
            "type": "DocumentationResponse",
            "condition": "in"
        },
        {
            "terms": {
                "property_name": "status",
                "value": [
                    "Submitted",
                    "Accepted",
                    "Rejected"
                ]
            },
            "type": "InterviewResponse",
            "condition": "in"
        },
        {
            "terms": {
                "property_name": "status",
                "value": [
                    "Submitted",
                    "Accepted",
                    "Rejected"
                ]
            },
            "type": "PopulationSampleResponse",
            "condition": "in"
        },
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
        "Request",
        "ControlAssessment",
        "Issue",
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
        "PopulationSampleResponse"
    ],
    "delete": [
        "Request",
    ],
}
