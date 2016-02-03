/*!
    Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: ivan@reciprocitylabs.com
    Maintained By: ivan@reciprocitylabs.com
*/


(function(can, $) {
  can.Component.extend({
    tag: "reuse-objects",
    scope: {
      parentInstance: null,
      reusedObjects: new can.List(),
      create_relationship: function(destination) {
        console.log("_create_relationship", this, destination);
        var source;
        var dest;

        if (!this.scope || !destination) {
          return $.Deferred().resolve();
        }

        source = this.scope.attr("parentInstance");
        dest = CMS.Models.get_instance({
          id: destination.id,
          type: can.spaceCamelCase(destination.type).replace(/ /g, '')
        });

        return new CMS.Models.Relationship({
          source: source.stub(),
          destination: dest,
          context: source.context,
        }).save();
      },
      create_evidence_relationship: function(destination) {
        console.log("create_evidence_relationship", destination);
        var source;
        var dest;

        if (!this.scope || !destination) {
          return $.Deferred().resolve();
        }

        source = this.scope.attr("parentInstance");
        dest = CMS.Models.get_instance({
          id: destination.id,
          type: can.spaceCamelCase(destination.type).replace(/ /g, '')
        });

        //console.log("dest: ", dest);

        return new CMS.Models.ObjectDocument({
          context : source.context,
          documentable : source,
          document : dest,
        }).save();
      },
    },
    events: {
      init: function(el, ev) {

        //debugger;
      },
      "inserted": function(el, ev) {
        console.log("inserted", el, ev);
        console.log("parent instance: ", this.scope.parentInstance);
        console.log("parent instance: ", this.options.scope.parentInstance);
        //debugger;
        // kje bi naj sicer prisel tale?
        //this.scope.attr("parent_instance", GGRC.page_instance());
      },
      "[reusable=true] input[type=checkbox] change": function (el, ev) {
        var reused = this.scope.attr("reusedObjects");
        var object = el.parent();
        console.log("method: ", object.parents("[reusable=true]").attr("reuse-method"));
        //debugger;
        var key = {
          type: object.attr("data-object-type"),
          id: object.attr("data-object-id"),
          method: object.parents("[reusable=true]").attr("reuse-method")
        };
        var index = _.findIndex(reused, key);
        if (index >= 0) {
          reused.splice(index, 1);
          return;
        }
        reused.push(key);
      },
      ".js-trigger-reuse click": function(el, ev) {
        console.log("clicked reuse");

        var reused = this.scope.attr("reusedObjects");
        var related_dfds = can.map(reused, function (object) {
          console.log("this: ", this);
          console.log("o: ", object);
          var executer = this.scope[object.method].bind(this);
          console.log(executer);

          return executer(object);
        }.bind(this));
        //}.bind(this.scope.attr("parentInstance")));
        GGRC.delay_leaving_page_until($.when.apply($, related_dfds));
      },
    }
  });

  can.Component.extend({
    tag: "mapping-tree-view",
    template: can.view(GGRC.mustache_path + "/base_templates/mapping_tree_view.mustache"),
    scope: {
      reusable: "@"
    },
    events: {
      "[data-toggle=unmap] click": function (el, ev) {
        ev.stopPropagation();
        var instance = el.find(".result").data("result"),
            mappings = this.scope.parentInstance.get_mapping(this.scope.mapping),
            binding;

        binding = _.find(mappings, function (mapping) {
          return mapping.instance.id === instance.id &&
                 mapping.instance.type === instance.type;
        });
        _.each(binding.get_mappings(), function (mapping) {
          mapping.refresh().then(function () {
            mapping.destroy();
          });
        });
      }
    }
  });

  can.Component.extend({
    tag: "reusable-object",
    template: "<content></content>",
    scope: {
      is_reusable: null
    },
    events: {
      "inserted": function(el, ev) {
        if (el.parents("[reusable=true]").length === 1) {
          this.scope.attr("is_reusable", true);
        }
      }
    },
    helpers: {
      if_reusable: function(options) {
        if (this.attr("is_reusable") === true) {
          return options.fn();
        }
        return options.inverse();
      }
    }
  });
})(window.can, window.can.$);
