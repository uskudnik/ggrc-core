/*!
  Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
  Created By: ivan@reciprocitylabs.com
  Maintained By: ivan@reciprocitylabs.com
*/

(function(can, $) {
  var url = can.route.deparam(window.location.search.substr(1)),
      filterModel = can.Map({
        model_name: "Program",
        value: "",
        filter: {}
      }),
      panelModel = can.Map({
        selected: {},
        models: null,
        type: "Program",
        filter: "",
        relevant: can.compute(function () {
          return new can.List();
        }),
        columns: can.compute(function () {
          return _.filter(GGRC.model_attr_defs[this.attr("type")], function(el) {
            return (!el.import_only) &&
                   (el.display_name.indexOf("unmap:") === -1);
          });
        })
      }),
      panelsModel = can.Map({
        items: new can.List()
      }),
      exportModel = can.Map({
        panels: new panelsModel(),
        loading: false,
        url: "/_service/export_csv",
        type: url.model_type || "Program",
        edit_filename: false,
        only_relevant: false,
        filename: "Export Objects",
        get_filename: can.compute(function () {
          return this.attr("filename").replace(/\s+/, "_").toLowerCase() + ".csv";
        }),
        data_grid: can.compute(function () {
          return _.has(url, "data_grid");
        })
      });


  can.Component.extend({
    tag: "csv-template",
    template: "<content></content>",
    scope: {
      url: "/_service/export_csv",
      selected: [],
      importable: GGRC.Bootstrap.importable,
    },
    events: {
      "#importSelect change": function (el, ev) {
        var $items = el.find(":selected"),
            selected = this.scope.attr("selected");

        $items.each(function () {
          var $item = $(this);
          if (_.findWhere(selected, {value: $item.val()})) {
            return;
          }
          return selected.push({
            name: $item.attr("label"),
            value: $item.val()
          });
        });
      },
      ".import-button click": function (el, ev) {
        ev.preventDefault();
        var data = _.map(this.scope.attr("selected"), function (el) {
              return {
                object_name: el.value,
                fields: "all"
              };
            });
        if (!data.length) {
          return;
        }

        GGRC.Utils.export_request({
          data: data
        }).then(function (data) {
          GGRC.Utils.download("import_template.csv", data);
        }.bind(this))
        .fail(function (data) {
          $("body").trigger("ajax:flash", {"error": data.responseText.split("\n")[3]});
        }.bind(this));
      },
      ".import-list a click": function (el, ev) {
        ev.preventDefault();

        var index = el.data("index"),
            item = this.scope.attr("selected").splice(index, 1)[0];

        this.element.find("#importSelect option:selected").each(function () {
          var $item = $(this);
          if ($item.val() === item.value) {
            $item.prop("selected", false);
          }
        });
      }
    }
  });

  can.Component.extend({
    tag: "csv-export",
    template: "<content></content>",
    scope: function () {
      return {
        export: new exportModel()
      };
    },
    events: {
      ".btn-title-change click": function (el, ev) {
        ev.preventDefault();
        this.scope.attr("export.edit_filename", !this.scope.attr("export.edit_filename"));
      },
      "#export-csv-button click": function (el, ev) {
        ev.preventDefault();
        this.scope.attr("export.loading", true);
        var panels = this.scope.attr("export.panels.items"),
            data_grid = this.scope.attr("export.data_grid"),
            only_relevant = this.scope.attr("export.only_relevant"),
            query = _.map(panels, function (panel, index) {
              var relevant_filter = "",
                  predicates;
              if (data_grid && index > 0) {
                relevant_filter = "#__previous__," + (index - 1) + "#";
                if (only_relevant && index > 1) {
                  relevant_filter += " AND #__previous__,0#";
                }
              } else {
                predicates = _.map(panel.attr("relevant"), function (el) {
                  var id = el.model_name === "__previous__" ? index - 1 : el.filter.id;
                  return "#" + el.model_name + "," + id + "#";
                });
                relevant_filter = _.reduce(predicates, function (p1, p2) {
                  return p1 + " AND " + p2;
                });
              }
              return {
                object_name: panel.type,
                fields: _.compact(_.map(Object.keys(panel.selected), function (key) {
                  return panel.selected[key] === true ? key : null;
                })),
                filters: GGRC.query_parser.join_queries(
                  GGRC.query_parser.parse(relevant_filter || ""),
                  GGRC.query_parser.parse(panel.filter || "")
                )
              };
            }),
            view = data_grid ? "grid" : "blocks";

        GGRC.Utils.export_request({
          data: query,
          headers: {
            "X-export-view": view
          }
        }).then(function (data) {
          GGRC.Utils.download(this.scope.attr("export.get_filename"), data);
        }.bind(this))
        .fail(function (data) {
          $("body").trigger("ajax:flash", {"error": data.responseText.split("\n")[3]});
        }.bind(this))
        .always(function () {
          this.scope.attr("export.loading", false);
        }.bind(this));
      }
    }
  });


  can.Component.extend({
    tag: "export-group",
    template: "<content></content>",
    scope: {
      _index: 0
    },
    events: {
      "inserted": function () {
        this.addPanel({
          type: url.model_type || "Program"
        });
      },
      addPanel: function (data) {
        data = data || {};
        var index = this.scope.attr("_index") + 1;
        if (!data.type) {
          data.type = "Program";
        }

        this.scope.attr("_index", index);
        data.index = index;
        return this.scope.attr("panels.items").push(new panelModel(data));
      },
      getIndex: function (el) {
        return +el.closest("export-panel").control().scope.attr("item.index");
      },
      ".remove_filter_group click": function (el, ev) {
        ev.preventDefault();
        var elIndex = this.getIndex(el),
            index = _.pluck(this.scope.attr("panels.items"), "index").indexOf(elIndex);
        this.scope.attr("panels.items").splice(index, 1);
      },
      "#addAnotherObjectType click": function (el, ev) {
        ev.preventDefault();
        this.addPanel();
      }
    }
  });

  can.Component.extend({
    tag: "export-panel",
    template: "<content></content>",
    scope: {
      exportable: GGRC.Bootstrap.exportable,
      panel_number: "@",
      has_parent: false,
      fetch_relevant_data: function (id, type) {
        var dfd = CMS.Models[type].findOne({id: id});
        dfd.then(function (result) {
          this.attr("item.relevant").push(new filterModel({
            model_name: url.relevant_type,
            value: url.relevant_id,
            filter: result
          }));
        }.bind(this));
      }
    },
    events: {
      inserted: function () {
        var panel_number = +this.scope.attr("panel_number");

        if (!panel_number && url.relevant_id && url.relevant_type) {
          this.scope.fetch_relevant_data(url.relevant_id, url.relevant_type);
        }
        this.setSelected();
      },
      "[data-action=attribute_select_toggle] click": function (el, ev) {
        var items = GGRC.model_attr_defs[this.scope.attr("item.type")],
            split_items = {
              mappings: _.filter(items, function (el) {
                return el.type == "mapping";
              }),
              attributes: _.filter(items, function (el) {
                return el.type != "mapping";
              })
            };
        _.map(split_items[el.data("type")], function (attr) {
          this.scope.attr("item.selected." + attr.key, el.data("value"));
        }.bind(this));
      },
      "setSelected": function () {
        this.scope.attr("item.selected", _.reduce(this.scope.attr("item.columns"), function (memo, data) {
          memo[data.key] = true;
          return memo;
        }, {}));
      },
      "{scope.item} type": function () {
        this.scope.attr("item.selected", {});
        this.scope.attr("item.relevant", []);
        this.scope.attr("item.filter", "");
        this.scope.attr("item.has_parent", false);

        this.setSelected();
      }
    },
    helpers: {
      first_panel: function (options) {
        if (+this.attr("panel_number") > 0) {
          return options.fn();
        }
        return options.inverse();
      }
    }
  });

  $("#csv_export").html(can.view(GGRC.mustache_path + "/import_export/export.mustache", {}));
})(window.can, window.can.$);
