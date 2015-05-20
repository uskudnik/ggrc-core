scope = "System"
description = """
  This role grants a user basic object creation and editing permission.
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
        "ObjectOwner",
        "ObjectPerson",
        "ObjectSection",
        "Option",
        "OrgGroup",
        "Vendor",
        "PopulationSample",
        "Product",
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
        "Person",
        "Program",
        "Role",
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
    "create": [
        "Categorization",
        "Category",
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
        "Market",
        "Objective",
        "ObjectiveControl",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectOwner",
        "ObjectPerson",
        "ObjectSection",
        "Option",
        "OrgGroup",
        "Vendor",
        "PopulationSample",
        "Product",
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
        "Person",
    ],
    "view_object_page": [
        "__GGRC_ALL__"
    ],
    "update": [
        "Categorization",
        {
            "type": "Category",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Issue",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "ControlAssessment",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Control",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "ControlControl",
        "ControlSection",
        {
            "type": "DataAsset",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Directive",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Contract",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Policy",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Regulation",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Standard",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "DirectiveControl",
        "DirectiveSection",
        {
            "type": "Document",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Facility",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Market",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Objective",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "ObjectiveControl",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectOwner",
        "ObjectPerson",
        "ObjectSection",
        {
            "type": "Option",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "OrgGroup",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Vendor",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "PopulationSample",
        {
            "type": "Product",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "Relationship",
        "RelationshipType",
        {
            "type": "SectionBase",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Section",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Clause",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "SectionObjective",
        {
            "type": "SystemOrProcess",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "System",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Process",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "SystemControl",
        "SystemSystem",
        "Person"
    ],
    "delete": [
        "Categorization",
        {
            "type": "Category",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Control",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Issue",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "ControlAssessment",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "ControlControl",
        "ControlSection",
        {
            "type": "DataAsset",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Directive",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Contract",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Policy",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Regulation",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Standard",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "DirectiveControl",
        "DirectiveSection",
        {
            "type": "Document",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Facility",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Market",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Objective",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "ObjectiveControl",
        "ObjectControl",
        "ObjectDocument",
        "ObjectObjective",
        "ObjectOwner",
        "ObjectPerson",
        "ObjectSection",
        {
            "type": "Option",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "OrgGroup",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Vendor",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "PopulationSample",
        {
            "type": "Product",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "Relationship",
        "RelationshipType",
        {
            "type": "SectionBase",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Section",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Clause",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "SectionObjective",
        {
            "type": "SystemOrProcess",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "System",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        {
            "type": "Process",
            "terms": {
                "list_property": "owners",
                "value": "$current_user"
            },
            "condition": "contains"
        },
        "SystemControl",
        "SystemSystem"
    ]
}
