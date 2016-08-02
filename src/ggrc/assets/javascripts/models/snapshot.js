/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */
;(function (can) {
  can.Model.Cacheable('CMS.Models.Snapshot', {
    root_object: 'snapshot',
    root_collection: 'snapshots',
    findOne: 'GET /api/snapshots/{id}',
    findAll: 'GET /api/snapshots',
    update: 'PUT /api/snapshots/{id}',
    destroy: 'DELETE /api/snapshots/{id}',
    create: 'POST /api/snapshots',
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      revision: 'CMS.Models.Revision.stub',
      parent: 'CMS.Models.Cacheable.stub'
    },
    init: function () {
      console.log("class init", this.type, this.id);

      this._super && this._super.apply(this, arguments);
    }
  }, {
    init: function () {
      console.log("instance init!", this.type, this.id);

      if (this._super) {
        this._super.apply(this, arguments);
      }
    },
    object_model: can.compute(function () {
      console.log("object_model executed");
      return CMS.Models[this.attr('object_type')];
    })
  });
})(this.can);
