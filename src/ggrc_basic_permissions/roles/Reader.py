scope = "System"
description = """
  This role grants a user basic, read-only, access permission to a gGRC
  instance.
  """
permissions = {
    "read": [
        "Categorization",
        "Category",
        "ControlCategory",
        "ControlAssertion",
        "Control",
        "ControlAssessment",
        "Issue",
        "ControlControl",
        "ControlSection",
        "DataAsset",
        "Directive",
        "Contract",
        "Policy",
        "Regulation",
        "Standard",
        "DirectiveControl",
        "DirectiveSection",
        "Document",
        "Facility",
        "Help",
        "Market",
        "Objective",
        "ObjectiveControl",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectPerson",
        "ObjectSection",
        "Option",
        "OrgGroup",
        "Vendor",
        "PopulationSample",
        "Product",
        "ProgramControl",
        "ProgramDirective",
        "Project",
        "Relationship",
        "RelationshipType",
        "SectionBase",
        "Section",
        "Clause",
        "SectionObjective",
        "SystemOrProcess",
        "System",
        "Process",
        "SystemControl",
        "SystemSystem",
        "ObjectOwner",
        "Person",
        "Program",
        "Role",
        "UserRole",
        "Context",
        {
            "type": "BackgroundTask",
            "terms": {
                "property_name": "modified_by",
                "value": "$current_user"
            },
            "condition": "is"
        },
    ],
    "create": [],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [],
    "delete": []
}
