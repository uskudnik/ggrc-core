/*
 * Copyright (C) 2016 Google Inc.
 * Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, $) {
  can.Control('GGRC.Controllers.PbcWorkflows', {}, {
    '{CMS.Models.AssessmentTemplate} updated': function (model, ev, instance) {
      var attrDfd;
      var definitions = instance.custom_attribute_definitions;

      if (!(instance instanceof CMS.Models.AssessmentTemplate)) {
        return;
      }

      attrDfd = $.map(definitions, function (attr, i) {
        var CADefinition = CMS.Models.CustomAttributeDefinition;
        var params = can.extend({
          definition_id: instance.id,
          definition_type: "assessment_template",
          context: instance.context
        }, attr.serialize());
        if (attr.id && attr._pending_delete) {
          return attr.reify().refresh().then(function (attr) {
            attr.destroy();
          });
        } else if (attr.id) {
          return CADefinition.findOne({
            id: attr.id
          }).then(function (definition) {
            definition.attr(params);
            return definition.save();
          });
        }
        return new CADefinition(params).save().then(function (definition) {
          instance.custom_attribute_definitions[i] = definition;
        });
      });
      instance.delay_resolving_save_until($.when(attrDfd));
    },
    '{CMS.Models.AssessmentTemplate} created': function (model, ev, instance) {
      return;
      if (!(instance instanceof CMS.Models.AssessmentTemplate)) {
        return;
      }

      this._after_pending_joins(instance, function () {
        var auditDfd;
        var attrDfd;
        var definitions = instance.custom_attribute_definitions;

        auditDfd = this._create_relationship(instance,
            instance.audit, instance.audit.context);
        attrDfd = $.map(definitions, function (attr, i) {
          if (attr._pending_delete) {
            return;
          }
          return new CMS.Models.CustomAttributeDefinition(can.extend({
            definition_id: instance.id,
            definition_type: "assessment_template",
            context: instance.context
          }, attr.serialize())).save().then(function (attributeDefinition) {
            instance.custom_attribute_definitions[i] = attributeDefinition;
          });
        });
        instance.delay_resolving_save_until($.when(auditDfd, attrDfd));
      }.bind(this));
    },
    '{CMS.Models.Issue} created': function (model, ev, instance) {
      var auditDfd;
      var controlDfd;
      var programDfd;
      var assessmentDfd;

      if (!(instance instanceof CMS.Models.Issue)) {
        return;
      }

      this._after_pending_joins(instance, function () {
        auditDfd = this._create_relationship(instance, instance.audit);
        controlDfd = this._create_relationship(instance, instance.control);
        programDfd = this._create_relationship(instance, instance.program);
        assessmentDfd = this._create_relationship(
          instance, instance.assessment);
        instance.delay_resolving_save_until($.when(auditDfd, controlDfd,
            programDfd, assessmentDfd));
      }.bind(this));
    },
    '{CMS.Models.Section} created': function (model, ev, instance) {
      var directiveDfd;

      if (!(instance instanceof CMS.Models.Section)) {
        return;
      }

      this._after_pending_joins(instance, function () {
        directiveDfd = this._create_relationship(instance, instance.directive);
        instance.delay_resolving_save_until($.when(directiveDfd));
      }.bind(this));
    },
    '{CMS.Models.UserRole} created': function (model, ev, instance) {
      var dfd;
      if (!(instance instanceof CMS.Models.UserRole)) {
        return;
      }
      if (instance.role_name !== 'Auditor') {
        return;
      }
      // Find the program context
      dfd = instance.refresh_all('context', 'related_object', 'program',
          'context');
      dfd.then(function (programContext) {
        // Find existing auditor roles for program context
        return $.when(
            programContext,
            CMS.Models.UserRole.findAll({context_id: programContext.id,
                person_id: instance.person.id}),
            CMS.Models.Role.findAll({name: 'ProgramReader'}));
      }).then(function (programContext, auditorProgramRoles, readerRoles) {
        // Check if there are any existing roles for the user and program context
        if (auditorProgramRoles.length) {
          return null;
        }
        // If no program role exists for the user, we create a reader role
        return new CMS.Models.UserRole({
          person: instance.person,
          role: readerRoles[0].stub(),
          context: programContext
        }).save();
      });
      instance.delay_resolving_save_until(dfd);
    },
    _after_pending_joins: function (instance, callback) {
      var dfd = instance.attr('_pending_joins_dfd');
      if (!dfd) {
        dfd = new $.Deferred().resolve();
      }
      dfd.then(callback);
    },
    _create_relationship: function (source, destination, context) {
      if (!destination || !destination.id) {
        return $.Deferred().resolve();
      }
      if (!context) {
        context = source.context;
      }
      return new CMS.Models.Relationship({
        source: source.stub(),
        destination: destination,
        context: context
      }).save();
    }
  });

  $(function () {
    $(document.body).ggrc_controllers_pbc_workflows();
  });
})(this.can, this.can.$);
