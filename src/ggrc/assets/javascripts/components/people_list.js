/*!
  Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
  Created By: andraz@reciprocitylabs.com
  Maintained By: andraz@reciprocitylabs.com
*/

(function (can) {
  can.Component.extend({
    tag: "people-list",
    template: can.view(GGRC.mustache_path + "/base_templates/people_list.mustache"),
    viewModel: {
      define: {
        editable: {
          type: "boolean"
        },
        deferred: {
          type: "boolean"
        }
      },
      editable: "@",
      deferred: "@",
      groups: {
        "verifier": [],
        "assignee": [],
        "requester": []
      }
    },
    events: {
      "{instance} updated": "update",
      "{instance} created": "update",
      "{groups} change": function () {
        if (!this.viewModel.attr("editable")) {
          return;
        }
        var instance = this.viewModel.attr("instance"),
            isAllowed = [];

        this.viewModel.attr("groups").each(function (group, type) {
          group = group.filter(function (person) {
            return person.attr("person_state") !== "deleted";
          });
          isAllowed.push(group.length);
        });
        instance.attr("people", _.every(isAllowed));
      },
      inserted: function () {
        this.scope.instance.get_assignees().then(function (assignees) {
          assignees = _.mapKeys(assignees, function (val, key) {
            return key.toLowerCase();
          });
          _.each(["verifier", "assignee", "requester"], function(type) {
            if (!assignees[type]) {
              assignees[type] = [];
            }
          });
          assignees = _.mapValues(assignees, function (users) {
            return _.map(users, function (user) {
              user.person.relationship_id = user.relationship.id;
              return user.person;
            });
          });
          this.viewModel.attr("groups", assignees);
        }.bind(this));
      },
      "getRelationship": function (person, destination, type, action) {
        if (action === "deleted") {
          return CMS.Models.Relationship.findInCacheById(person.relationship_id);
        }
        return new CMS.Models.Relationship({
          attrs: {
            "AssigneeType": can.capitalize(type)
          },
          source: {
            href: person.href,
            type: person.type,
            id: person.id
          },
          context: null,
          destination: destination
        });
      },
      "update": function () {
        var instance = this.viewModel.attr("instance"),
            destination, relationships = [];

        destination = {
          context_id: instance.context_id,
          href: instance.href,
          type: instance.type,
          id: instance.id
        };
        this.viewModel.attr("groups").each(function (group, type) {
          group.each(function (person) {
            var action = person.person_state,
                states = {
                  "added": function (model) {
                    return model.save();
                  },
                  "deleted": function (model) {

                    return model.refresh().then(function (response) {
                      return response.destroy();
                    });
                  },
                },
                model;

            if (!_.contains(_.keys(states), action)) {
              return;
            }
            person.attr("person_state", null);
            model = this.getRelationship(person, destination, type, action);
            relationships.push(states[action](model));
          }, this);
        }, this);

        this.viewModel.attr("instance").delay_resolving_save_until($.when.apply($, relationships));
      }
    }
  });

  can.Component.extend({
    tag: "people-group",
    template: can.view(GGRC.mustache_path + "/base_templates/people_group.mustache"),
    viewModel: {
      define: {
        required: {
          type: "boolean"
        },
        limit: {
          type: "number"
        }
      },
      limit: "@",
      required: "@",
      type: "@"
    },
    events: {
      ".js-trigger--person-delete click": function (el, ev) {
        var person = el.data("person");
        if (person.attr("person_state")) {
          person.attr("person_state", null);
          return this.viewModel.attr("people").splice(el.data("index"), 1);
        }
        person.attr("person_state", "deleted");
      },
      ".person-selector input autocomplete:select": function (el, ev, ui) {
        var person = _.findWhere(this.viewModel.attr("people"), {id: ui.item.id});
        if (person) {
          if (person.attr("person_state") === "deleted") {
            person.attr("person_state", null);
          }
          return;
        }
        this.viewModel.attr("people").push(_.extend(ui.item, {
          "person_state": "added"
        }));
      }
    },
    helpers: {
      show_add: function (options) {
        if (this.attr("editable")) {
          if (_.isNull(this.attr("limit")) ||
              this.attr("limit") > this.attr("people").filter(function (person) {
                return person.attr("person_state") !== "deleted";
              }).length) {
            return options.fn();
          }
        }
        return options.inverse();
      }
    }
  });
})(window.can);
