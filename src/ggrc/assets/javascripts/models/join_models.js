/*!
    Copyright (C) 2016 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/
(function (can, $) {
  can.Model.Cacheable('can.Model.Join', {
    join_keys: null,
    setup: function () {
      this._super.apply(this, arguments);
    },
    init: function () {
      if (this._super) {
        this._super.apply(this, arguments);
      }
      function reinit(ev, instance) {
        var refreshQueue;
        if (instance instanceof can.Model.Join) {
          instance.reinit();
          refreshQueue = new RefreshQueue();
          can.each(instance.constructor.join_keys, function (cls, key) {
            var obj;
            if (instance[key]) {
              if (instance[key].reify && instance[key].reify().refresh) {
                obj = instance[key].reify();
              } else {
                obj = cls.findInCacheById(instance[key].id);
              }
            }
            if (obj) {
              refreshQueue.enqueue(obj);
            }
          });
          refreshQueue.trigger();
        }
      }
      if (this === can.Model.Join) {
        this.bind('created', reinit);
        this.bind('destroyed', reinit);
      }
    }
  }, {
    init: function () {
      this._super.apply(this, arguments);
      can.each(this.constructor.join_keys, function (cls, key) {
        this.bind(key + '.stub_destroyed', function () {
          // Trigger `destroyed` on self, since it was destroyed on the server
          this.destroyed();
        }.bind(this));
      }.bind(this));
    },

    reinit: function () {
      this.init_join_objects();
    },

    init_join_object_with_type: function (attr) {
      console.log("init_join_object_with_type", attr);
      var objectId;
      var objectType;
      if (this[attr] instanceof can.Model) {
        return;
      }

      objectId = this[attr + '_id'] || (this[attr] || {}).id;
      objectType = this[attr + '_type'] || (this[attr] || {}).type;

      if (objectId && objectType && typeof objectType === 'string') {
        this.attr(attr, CMS.Models.get_instance(
              objectType
            , objectId
            , this[attr]
            ) || this[attr]);
      } else if (objectId) {
        this.attr(attr, CMS.Models.get_instance(this[attr]));
      }
    },

    init_join_object: function (attr, modelName) {
      var objectId = this[attr + '_id'] || (this[attr] || {}).id;

      if (objectId) {
        this.attr(
            attr,
            CMS.Models.get_instance(
              modelName, objectId, this[attr]
            ).stub() || this[attr]
        );
      }
    },

    init_join_objects: function () {
      var that = this
        ;

      can.each(this.constructor.join_keys, function (model, attr) {
        if (model === can.Model.Cacheable) {
          that.init_join_object_with_type(attr);
        } else {
          that.init_join_object(attr, model.shortName);
        }
      });
    }
  });

  can.Model.Join('CMS.Models.Snapshot', {
    root_object: 'snapshot',
    root_collection: 'snapshots',
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      parent: 'CMS.Models.Cacheable.stub',
      revision: 'CMS.Models.Revision.get_instances'
    },
    join_keys: {
      parent: can.Model.Cacheable,
      revision: can.Model.Revision
    },
    defaults: {
      parent: null,
      revision: null
    },
    findAll: 'GET /api/snapshots',
    create: 'POST /api/snapshots',
    update: 'PUT /api/snapshots/{id}',
    destroy: 'DELETE /api/snapshots/{id}'
  }, {
    reinit: function () {
    //   console.log("reinit", this);
    //   console.log("reinit.parent", this.parent);
    //   console.log("reinit.revision", this.revision);
      this.attr('parent', CMS.Models.get_instance(this.parent));
      this.attr('revision', CMS.Models.get_instance(this.revision));
    }
  });

  can.Model.Join('CMS.Models.Relationship', {
    root_object: 'relationship',
    root_collection: 'relationships',
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      source: 'CMS.Models.get_stub',
      destination: 'CMS.Models.get_stub'
    },
    join_keys: {
      source: can.Model.Cacheable,
      destination: can.Model.Cacheable
    },
    defaults: {
      source: null,
      destination: null
    },
    findAll: 'GET /api/relationships',
    create: 'POST /api/relationships',
    update: 'PUT /api/relationships/{id}',
    destroy: 'DELETE /api/relationships/{id}',
    createAssignee: function (options) {
      return new this({
        attrs: {
          AssigneeType: options.role
        },
        source: {
          href: options.source.href,
          type: options.source.type,
          id: options.source.id
        },
        context: options.context,
        destination: {
          href: options.destination.href,
          type: options.destination.type,
          id: options.destination.id
        }
      });
    },
    get_relationship: function (source, destination) {
      return _.first(_.filter(CMS.Models.Relationship.cache, function (model) {
        if (!model.source || !model.destination) {
          return false;
        }
        return model.source.type === source.type &&
                model.source.id === source.id &&
                model.destination.type === destination.type &&
                model.destination.id === destination.id ||
                model.source.type === destination.type &&
                model.source.id === destination.id &&
                model.destination.type === source.type &&
                model.destination.id === source.id;
      }));
    }
  }, {
    reinit: function () {
      this.attr('source', CMS.Models.get_instance(
        this.source_type ||
          (this.source &&
            (this.source.constructor &&
              this.source.constructor.shortName ||
              (!this.source.selfLink && this.source.type))),
          this.source_id || (this.source && this.source.id),
          this.source) || this.source);
      this.attr('destination', CMS.Models.get_instance(
        this.destination_type ||
          (this.destination &&
            (this.destination.constructor &&
              this.destination.constructor.shortName ||
              (!this.source.selfLink && this.destination.type))),
        this.destination_id || (this.destination && this.destination.id),
        this.destination) || this.destination);
    }
  });

  can.Model.Join('CMS.Models.UserRole', {
    root_object: 'user_role',
    root_collection: 'user_roles',
    findAll: 'GET /api/user_roles',
    update: 'PUT /api/user_roles/{id}',
    create: 'POST /api/user_roles',
    destroy: 'DELETE /api/user_roles/{id}',
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      person: 'CMS.Models.Person.stub',
      role: 'CMS.Models.Role.stub'
    },
    join_keys: {
      person: CMS.Models.Person,
      role: CMS.Models.Role
    }
  }, {
    save: function () {
      var role;
      if (!this.role && this.role_name) {
        role = _.find(CMS.Models.Role.cache, {name: this.role_name});
        if (role) {
          this.attr('role', role.stub());
          return this._super.apply(this, arguments);
        }
        return CMS.Models.Role.findAll({
          name__in: this.role_name
        }).then(function (roles) {
          if (roles.length < 1) {
            return new $.Deferred().reject('Role not found');
          }
          this.attr('role', roles[0].stub());
          return this._super.apply(this, arguments);
        }.bind(this));
      }
      return this._super.apply(this, arguments);
    }
  });

  can.Model.Join('CMS.Models.ObjectPerson', {
    root_object: 'object_person',
    root_collection: 'object_people',
    findAll: 'GET /api/object_people',
    create: 'POST /api/object_people',
    update: 'PUT /api/object_people/{id}',
    destroy: 'DELETE /api/object_people/{id}',
    join_keys: {
      personable: can.Model.Cacheable,
      person: CMS.Models.Person
    },
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      person: 'CMS.Models.Person.stub',
      personable: 'CMS.Models.get_stub'
    }

  }, {});

  can.Model.Join('CMS.Models.ObjectOwner', {
    root_object: 'object_owner',
    root_collection: 'object_owners',
    findOne: 'GET /api/object_owners/{id}',
    findAll: 'GET /api/object_owners',
    create: 'POST /api/object_owners',
    update: 'PUT /api/object_owners/{id}',
    destroy: 'DELETE /api/object_owners/{id}',
    join_keys: {
      ownable: can.Model.Cacheable,
      person: CMS.Models.Person
    },
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      person: 'CMS.Models.Person.stub',
      ownable: 'CMS.Models.get_stub'
    }
  }, {});

  can.Model.Join('CMS.Models.ObjectDocument', {
    root_object: 'object_document',
    root_collection: 'object_documents',
    findAll: 'GET /api/object_documents',
    create: 'POST /api/object_documents',
    destroy: 'DELETE /api/object_documents/{id}',
    join_keys: {
      documentable: can.Model.Cacheable,
      document: CMS.Models.Document
    },
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      document: 'CMS.Models.Document.stub',
      documentable: 'CMS.Models.get_stub'
    }
  }, {});

  can.Model.Join('CMS.Models.MultitypeSearchJoin', {
    join_keys: {}
  }, {});

  can.Model.Join('CMS.Models.AuditObject', {
    root_object: 'audit_object',
    root_collection: 'audit_objects',
    findAll: 'GET /api/audit_objects',
    create: 'POST /api/audit_objects',
    destroy: 'DELETE /api/audit_objects/{id}',
    join_keys: {
      auditable: can.Model.Cacheable,
      audit: CMS.Models.Audit
    },
    attributes: {
      context: 'CMS.Models.Context.stub',
      modified_by: 'CMS.Models.Person.stub',
      audit: 'CMS.Models.Audit.stub',
      auditable: 'CMS.Models.get_stub'
    }
  }, {});
})(this.can, this.can.$);
