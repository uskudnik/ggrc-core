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
      parent_instance: "@",
      dinstance: "@",
      _create_relationship: function(source, destination) {
        if (!destination) {
          return $.Deferred().resolve();
        }

        return new CMS.Models.Relationship({
          source: source.stub(),
          destination: destination,
          context: source.context,
        }).save();
      },
    },
    events: {
      init: function(el, ev) {
        //debugger;
      },
      "inserted": function(el, ev) {
        console.log("init", el, ev);
        // kje bi naj sicer prisel tale?
        this.scope.attr("parent_instance", GGRC.page_instance());
      },
      ".js-trigger-reuse click": function(el, ev) {
        console.log("blablabla reuse");
        var umbrella = el.parents("reuse-objects");
        var checked = umbrella.find(
          "[reusable] li input[type=checkbox]:checked");
        var related_dfds = can.map(checked, function (c) {
          var elem = $(c);
          var type = elem.attr("data-object-type");
          var id = elem.attr("data-object-id");
          //  //console.log("gonna link it with: ", type, id);
          console.log("this: ", this);
          console.log("this stub: ", this.stub());
          console.log("this context stub: ", this.context.stub());
          //return type+id;
          var dest = CMS.Models.get_instance({
            id: id,
            type: can.spaceCamelCase(type).replace(/ /g, '')
          });
          console.log("dest: ", dest);

          return new CMS.Models.Relationship({
                source: this.stub(),
                destination: dest.stub(),
                context: this.context.stub()
              }
            ).save();
        }.bind(this.scope.attr("parent_instance")));
        GGRC.delay_leaving_page_until($.when.apply($, related_dfds));
        console.log("PI: ", this.scope.attr("parent_instance"));
        console.log("checked: ", related_dfds);
      },
    }
  });

  can.Component.extend({
    tag: "mapping-tree-view",
    template: can.view(GGRC.mustache_path + "/base_templates/mapping_tree_view.mustache"),
    scope: {
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
    tag: "mapped-object",
    events: {
      "inserted": function(el, ev) {
        if (el.parents("reuse-objects")) {
          el.find("li").append('<input type="checkbox" name="reuseable_objects" data-object-type='+el.attr("data-object-type")+' data-object-id='+el.attr("data-object-id")+' />');
        }
      }
    }
  });
})(window.can, window.can.$);
