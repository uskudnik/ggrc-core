/*
 * Copyright (C) 2015 Reciprocity, Inc - All Rights Reserved
 * Unauthorized use, copying, distribution, displaying, or public performance
 * of this file, via any medium, is strictly prohibited. All information
 * contained herein is proprietary and confidential and may not be shared
 * with any third party without the express written consent of Reciprocity, Inc.
 * Created By: anze@reciprocitylabs.com
 * Maintained By: anze@reciprocitylabs.com
 */


(function (can) {
  can.Model.Cacheable("CMS.Models.Threat", {
    root_object: "threat",
    root_collection: "threats",
    category: "risk",
    findAll: "GET /api/threats",
    findOne: "GET /api/threats/{id}",
    create: "POST /api/threats",
    update: "PUT /api/threats/{id}",
    destroy: "DELETE /api/threats/{id}",
    mixins: ["ownable", "contactable", "unique_title"],
    is_custom_attributable: true,
    attributes: {
      context: "CMS.Models.Context.stub",
      contact: "CMS.Models.Person.stub",
      owners: "CMS.Models.Person.stubs",
      modified_by: "CMS.Models.Person.stub",
      object_people: "CMS.Models.ObjectPerson.stubs",
      people: "CMS.Models.Person.stubs",
      object_documents: "CMS.Models.ObjectDocument.stubs",
      documents: "CMS.Models.Document.stubs",
      related_sources: "CMS.Models.Relationship.stubs",
      related_destinations: "CMS.Models.Relationship.stubs",
      object_objectives: "CMS.Models.ObjectObjective.stubs",
      objectives: "CMS.Models.Objective.stubs",
      object_controls: "CMS.Models.ObjectControl.stubs",
      controls: "CMS.Models.Control.stubs",
      object_sections: "CMS.Models.ObjectSection.stubs",
      sections: "CMS.Models.get_stubs"
    },
    tree_view_options: {
      add_item_view : GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
    },
    init: function () {
      this._super && this._super.apply(this, arguments);
      this.validatePresenceOf("title");
    }
  }, {});
})(window.can);
