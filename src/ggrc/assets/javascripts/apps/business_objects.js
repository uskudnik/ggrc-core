/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//= require can.jquery-all

(function (can, $) {

  if (!GGRC.widget_descriptors)
    GGRC.widget_descriptors = {};
  if (!GGRC.default_widgets)
    GGRC.default_widgets = [];


  //A widget descriptor has the minimum five properties:
  // widget_id:  the unique ID string for the widget
  // widget_name: the display title for the widget in the UI
  // widget_icon: the CSS class for the widget in the UI
  // content_controller: The controller class for the widget's content section
  // content_controller_options: options passed directly to the content controller; the
  //   precise options depend on the controller itself.  They usually require instance
  //   and/or model and some view.
  can.Construct("GGRC.WidgetDescriptor", {
    /*
      make an info widget descriptor for a GGRC object
      You must provide:
      instance - an instance that is a subclass of can.Model.Cacheable
      widget_view [optional] - a template for rendering the info.
    */
    make_info_widget: function (instance, widget_view) {
      var default_info_widget_view = GGRC.mustache_path + "/base_objects/info.mustache";
      return new this(
        instance.constructor.shortName + ":info", {
          widget_id: "info",
          widget_name: function () {
            if (instance.constructor.title_singular === 'Person')
              return 'Info';
            else
              return instance.constructor.title_singular + " Info";
          },
          widget_icon: "grcicon-info",
          content_controller: GGRC.Controllers.InfoWidget,
          content_controller_options: {
            instance: instance,
            model: instance.constructor,
            widget_view: widget_view || default_info_widget_view
          }
        });
    },
    /*
      make a tree view widget descriptor with mostly default-for-GGRC settings.
      You must provide:
      instance - an instance that is a subclass of can.Model.Cacheable
      far_model - a can.Model.Cacheable class
      mapping - a mapping object taken from the instance
      extenders [optional] - an array of objects that will extend the default widget config.
    */
    make_tree_view: function (instance, far_model, mapping, extenders) {
      var descriptor = {
        content_controller: CMS.Controllers.TreeView,
        content_controller_selector: "ul",
        widget_initial_content: '<ul class="tree-structure new-tree"></ul>',
        widget_id: far_model.table_singular,
        widget_guard: function () {
          if (far_model.title_plural === "Audits" && instance instanceof CMS.Models.Program) {
            return "context" in instance && !!(instance.context.id);
          }
          return true;
        },
        widget_name: function () {
          var $objectArea = $(".object-area");
          if ($objectArea.hasClass("dashboard-area") || instance.constructor.title_singular === "Person") {
            if (/dashboard/.test(window.location)) {
              return "My " + far_model.title_plural;
            } else {
              return far_model.title_plural;
            }
          } else if (far_model.title_plural === "Audits") {
            return "Mapped Audits";
          } else {
            return (far_model.title_plural === "References" ? "Linked " : "Mapped ") + far_model.title_plural;
          }
        },
        widget_icon: far_model.table_singular,
        object_category: far_model.category || 'default',
        model: far_model,
        content_controller_options: {
          child_options: [],
          draw_children: false,
          parent_instance: instance,
          model: far_model,
          list_loader: function () {
            return mapping.refresh_list();
          }
        }
      };

      $.extend.apply($, [true, descriptor].concat(extenders || []));

      return new this(instance.constructor.shortName + ":" + far_model.table_singular, descriptor);
    },
    newInstance: function (id, opts) {
      var ret;
      if (!opts && typeof id === "object") {
        opts = id;
        id = opts.widget_id;
      }

      if (GGRC.widget_descriptors[id]) {
        if (GGRC.widget_descriptors[id] instanceof this) {
          $.extend(GGRC.widget_descriptors[id], opts);
        } else {
          ret = this._super.apply(this);
          $.extend(ret, GGRC.widget_descriptors[id], opts);
          GGRC.widget_descriptors[id] = ret;
        }
        return GGRC.widget_descriptors[id];
      } else {
        ret = this._super.apply(this, arguments);
        $.extend(ret, opts);
        GGRC.widget_descriptors[id] = ret;
        return ret;
      }
    }
  }, {});

  /*
    WidgetList - an extensions-ready repository for widget descriptor configs.
    Create a new widget list with new GGRC.WidgetList(list_name, widget_descriptions)
      where widget_descriptions is an object with the structure:
      { <page_name> :
        { <widget_id> :
          { <widget descriptor-ready properties> },
        ...},
      ...}

    See the comments for GGRC.WidgetDescriptor for details in what is necessary to define
    a widget descriptor.
  */
  can.Construct("GGRC.WidgetList", {
    modules: {},
    /*
      get_widget_list_for: return a keyed object of widget descriptors for the specified page type.

      page_type - one of a GGRC object model's shortName, or "admin"

      The widget descriptors are built on the first call of this function; subsequently they are retrieved from the
       widget descriptor cache.
    */
    get_widget_list_for: function (page_type) {
      var widgets = {};
      can.each(this.modules, function (module) {
        can.each(module[page_type], function (descriptor, id) {
          if (!widgets[id]) {
            widgets[id] = descriptor;
          } else {
            can.extend(true, widgets[id], descriptor);
          }
        });
      });
      var descriptors = {};
      can.each(widgets, function (widget, widget_id) {
        switch (widget.content_controller) {
        case GGRC.Controllers.InfoWidget:
          descriptors[widget_id] = GGRC.WidgetDescriptor.make_info_widget(
            widget.content_controller_options && widget.content_controller_options.instance || widget.instance,
            widget.content_controller_options && widget.content_controller_options.widget_view || widget.widget_view
          );
          break;
        case GGRC.Controllers.TreeView:
          descriptors[widget_id] = GGRC.WidgetDescriptor.make_tree_view(
            widget.content_controller_options && (widget.content_controller_options.instance || widget.content_controller_options.parent_instance) || widget.instance,
            widget.content_controller_options && widget.content_controller_options.model || widget.far_model || widget.model,
            widget.content_controller_options && widget.content_controller_options.mapping || widget.mapping,
            widget
          );
          break;
        default:
          descriptors[widget_id] = new GGRC.WidgetDescriptor(page_type + ":" + widget_id, widget);
        }
      });
      can.each(descriptors, function (descriptor, id) {
        if (descriptor.suppressed) {
          delete descriptors[id];
        }
      });
      return descriptors;
    },
    /*
      returns a keyed object of widget descriptors that represents the current page.
    */
    get_current_page_widgets: function () {
      return this.get_widget_list_for(GGRC.page_instance().constructor.shortName);
    },
    get_default_widget_sort: function () {
      return this.sort;
    },
  }, {
    init: function (name, opts, sort) {
      this.constructor.modules[name] = this;
      can.extend(this, opts);
      if (sort && sort.length) {
        this.constructor.sort = sort;
      }
    },
    /*
      Here instead of using the object format described in the class comments, you may instead
      add widgets to the WidgetList by using add_widget.

      page_type - the shortName of a GGRC object class, or "admin"
      id - the desired widget's id.
      descriptor - a widget descriptor appropriate for the widget type. FIXME - the descriptor's
        widget_id value must match the value passed as "id"
    */
    add_widget: function (page_type, id, descriptor) {
      this[page_type] = this[page_type] || {};
      if (this[page_type][id]) {
        can.extend(true, this[page_type][id], descriptor);
      } else {
        this[page_type][id] = descriptor;
      }
    },
    suppress_widget: function (page_type, id) {
      this[page_type] = this[page_type] || {};
      if (this[page_type][id]) {
        can.extend(true, this[page_type][id], {
          suppressed: true
        });
      } else {
        this[page_type][id] = {
          suppressed: true
        };
      }
    }
  });

  var widget_list = new GGRC.WidgetList("ggrc_core");

  $(function () {

    var object_class = GGRC.infer_object_type(GGRC.page_object),
      object_table = object_class && object_class.table_plural,
      object = GGRC.page_instance();

    var base_widgets_by_type = {
      "Program": "Issue ControlAssessment Regulation Contract Policy Standard Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Audit": "Issue ControlAssessment Request history Person Program Control",
      "Issue": "ControlAssessment Control Audit Program Regulation Contract Policy Standard Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Issue",
      "ControlAssessment": "Issue Objective Program Regulation Contract Policy Standard Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit Request",
      "Regulation": "Program Issue ControlAssessment Section Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Policy": "Program Issue ControlAssessment Section Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Standard": "Program Issue ControlAssessment Section Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Contract": "Program Issue ControlAssessment Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Clause": "Contract Objective ControlAssessment Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Section": "Objective Control ControlAssessment System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Objective": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person",
      "Control": "Issue ControlAssessment Request Program Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Person": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Audit Request",
      "OrgGroup": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Vendor": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "System": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Process": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "DataAsset": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Product": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Project": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Facility": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit",
      "Market": "Program Issue ControlAssessment Regulation Contract Policy Standard Section Clause Objective Control System Process DataAsset Product Project Facility Market OrgGroup Vendor Person Audit"
    };
    base_widgets_by_type = _.mapValues(base_widgets_by_type,
      function (conf) {
        return conf.split(" ");
      });
    //Update GGRC.base_widgets_by_type for tree_view of each widget type
    if (!GGRC.tree_view) {
      GGRC.tree_view = {};
    }
    GGRC.tree_view.base_widgets_by_type = base_widgets_by_type;

    // TODO: Really ugly way to avoid executing IIFE - needs cleanup
    if (!GGRC.page_object) {
      return;
    }
    // Info widgets display the object information instead of listing connected
    //  objects.
    var info_widget_views = {
      'programs': GGRC.mustache_path + "/programs/info.mustache",
      'audits': GGRC.mustache_path + "/audits/info.mustache",
      'people': GGRC.mustache_path + "/people/info.mustache",
      'policies': GGRC.mustache_path + "/policies/info.mustache",
      'sections': GGRC.mustache_path + "/sections/info.mustache",
      'objectives': GGRC.mustache_path + "/objectives/info.mustache",
      'controls': GGRC.mustache_path + "/controls/info.mustache",
      'systems': GGRC.mustache_path + "/systems/info.mustache",
      'processes': GGRC.mustache_path + "/processes/info.mustache",
      'products': GGRC.mustache_path + "/products/info.mustache",
      'control_assessments': GGRC.mustache_path + "/control_assessments/info.mustache",
      'issues': GGRC.mustache_path + "/issues/info.mustache",
    };
    widget_list.add_widget(object.constructor.shortName, "info", {
      widget_id: "info",
      content_controller: GGRC.Controllers.InfoWidget,
      instance: object,
      widget_view: info_widget_views[object_table]
    });

    var model_names = Object.keys(base_widgets_by_type);
    model_names.sort();
    var possible_model_type = model_names.slice();
    possible_model_type.push("Request"); //Missing model-type by selection
    can.each(model_names, function (name) {
      GGRC.tree_view.basic_model_list.push({model_name: name, display_name: CMS.Models[name].title_singular});
      //Initialize child_model_list, and child_display_list each model_type
      var w_list  = base_widgets_by_type[name], child_model_list = [];
      w_list.sort();
      can.each(w_list, function (item) {
        if (possible_model_type.indexOf(item) !== -1) {
          child_model_list.push({model_name: item, display_name: CMS.Models[item].title_singular});
        }
      });
      GGRC.tree_view.sub_tree_for[name] = {
        model_list: child_model_list,
        display_list : CMS.Models[name].tree_view_options.child_tree_display_list || w_list
      };
    });

    function sort_sections(sections) {
      return can.makeArray(sections).sort(window.natural_comparator);
    }

    function apply_mixins(definitions) {
      var mappings = {};

      // Recursively handle mixins
      function reify_mixins(definition) {
        var final_definition = {};
        if (definition._mixins) {
          can.each(definition._mixins, function (mixin) {
            if (typeof (mixin) === "string") {
              // If string, recursive lookup
              if (!definitions[mixin])
                console.debug("Undefined mixin: " + mixin, definitions);
              else
                can.extend(final_definition, reify_mixins(definitions[mixin]));
            } else if (can.isFunction(mixin)) {
              // If function, call with current definition state
              mixin(final_definition);
            } else {
              // Otherwise, assume object and extend
              can.extend(final_definition, mixin);
            }
          });
        }
        can.extend(final_definition, definition);
        delete final_definition._mixins;
        return final_definition;
      }

      can.each(definitions, function (definition, name) {
        // Only output the mappings if it's a model, e.g., uppercase first letter
        if (name[0] === name[0].toUpperCase())
          mappings[name] = reify_mixins(definition);
      });

      return mappings;
    }

    var far_models = base_widgets_by_type[object.constructor.shortName],
      model_widget_descriptors = {},
      model_default_widgets = [],

      // here we are going to define extra descriptor options, meaning that
      //  these will be used as extra options to create widgets on top of

      extra_descriptor_options = {
        all: {
          Person: {
            widget_icon: 'grcicon-user-black'
          },
          Document: {
            widget_icon: 'grcicon-link'
          }
        },
        Contract: {
          Clause: {
            widget_name: function () {
              var $objectArea = $(".object-area");
              if ($objectArea.hasClass("dashboard-area")) {
                return "Clauses";
              } else {
                return "Mapped Clauses";
              }
            }
          }
        },
        Program: {
          Person: {
            widget_id: "person",
            widget_name: "People",
            widget_icon: "person",
            content_controller: GGRC.Controllers.TreeView
          }
        },
        Audit: {
          Person: {
            widget_id: "person",
            widget_name: "People",
            widget_icon: "person",
            content_controller: GGRC.Controllers.TreeView,
            content_controller_options: {
              mapping: "authorized_people",
              allow_mapping: false,
              allow_creating: false
            }
          },
          Request: {
            widget_id: "Request",
            widget_name: "Open Requests"
          },
          history: {
            widget_id: "history",
            widget_name: "Complete",
            widget_icon: "history"
          },
          Control: {
            widget_id: "control",
            widget_name: "In Scope Controls",
            widget_icon: "control"
          },
          program: {
            widget_id: "program",
            widget_name: "Program",
            widget_icon: "program"
          },
        },
        Control: {
          Request: {
            widget_id: "Request",
            widget_name: "Audit Requests"
          }
        },
        Person: {
          Request: {
            widget_id: "Request",
            widget_name: "Audit Requests"
          }
        }
      },
      // Prevent widget creation with <model_name>: false
      // e.g. to prevent ever creating People widget:
      //     { all : { Person: false }}
      // or to prevent creating People widget on Objective page:
      //     { Objective: { Person: false } }
      overridden_models = {
        Program: {
          //  Objective: false
          //, Control: false
          //, Regulation: false
          //, Policy: false
          //, Standard: false
          //, Contract: false
        },
        all: {
          Document: false,
          DocumentationResponse: false,
          InterviewResponse: false,
          PopulationSampleResponse: false
        }
      },
      section_child_options = {
        model: CMS.Models.Section,
        mapping: "sections",
        show_view: GGRC.mustache_path + "/sections/tree.mustache",
        footer_view: GGRC.mustache_path + "/sections/tree_footer.mustache",
        add_item_view: GGRC.mustache_path + "/sections/tree_add_item.mustache",
        draw_children: true
      },
      clause_child_options = {
        model: CMS.Models.Clause,
        mapping: "related_objects",
        show_view: GGRC.mustache_path + "/sections/tree.mustache",
        footer_view: GGRC.mustache_path + "/sections/tree_footer.mustache",
        add_item_view: GGRC.mustache_path + "/sections/tree_add_item.mustache",
        draw_children: true
      },
      related_objects_child_options = {
        model: can.Model.Cacheable,
        mapping: "related_objects",
        show_view: GGRC.mustache_path + "/base_objects/tree.mustache",
        footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
        add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
        draw_children: true
      },
      extra_content_controller_options = apply_mixins({
        objectives: {
          Objective: {
            mapping: "objectives",
            draw_children: true,
            show_view: GGRC.mustache_path + "/objectives/tree.mustache",
            footer_view: GGRC.mustache_path + "/objectives/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/objectives/tree_add_item.mustache"
          }
        },
        controls: {
          Control: {
            mapping: "controls",
            draw_children: true,
            show_view: GGRC.mustache_path + "/controls/tree.mustache",
            footer_view: GGRC.mustache_path + "/controls/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/controls/tree_add_item.mustache"
          }
        },
        business_objects: {
          DataAsset: {
            mapping: "related_data_assets",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Facility: {
            mapping: "related_facilities",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Market: {
            mapping: "related_markets",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          OrgGroup: {
            mapping: "related_org_groups",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Vendor: {
            mapping: "related_vendors",
            hild_options: [related_objects_child_options],
            draw_children: true
          },
          Process: {
            mapping: "related_processes",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Product: {
            mapping: "related_products",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Project: {
            mapping: "related_projects",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          System: {
            mapping: "related_systems",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          ControlAssessment: {
            mapping: "related_control_assessments",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Document: {
            mapping: "documents"
          },
          Person: {
            mapping: "people"
          },
          Program: {
            mapping: "programs",
            child_options: [related_objects_child_options],
            draw_children: true
          },
        },
        issues: {
          Issue: {
            mapping: "related_issues",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
            child_options: [related_objects_child_options],
            draw_children: true
          }
        },
        governance_objects: {
          Regulation: {
            mapping: "regulations",
            draw_children: true,
            child_options: [section_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache",
            footer_view: GGRC.mustache_path + "/directives/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/directives/tree_add_item.mustache"
          },
          Contract: {
            mapping: "contracts",
            draw_children: true,
            child_options: [clause_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache",
            footer_view: GGRC.mustache_path + "/directives/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/business_objects/tree_add_item.mustache"
          },
          Policy: {
            mapping: "policies",
            draw_children: true,
            child_options: [section_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache",
            footer_view: GGRC.mustache_path + "/directives/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/directives/tree_add_item.mustache"
          },
          Standard: {
            mapping: "standards",
            draw_children: true,
            child_options: [section_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache",
            footer_view: GGRC.mustache_path + "/directives/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/directives/tree_add_item.mustache"
          },
          Control: {
            mapping: "controls"
          },
          Objective: {
            mapping: "objectives"
          },
          Section: {
            mapping: "sections"
          },
          Clause: {
            mapping: "clauses"
          }
        },
        Program: {
          _mixins: [
            "governance_objects", "objectives", "controls", "business_objects", "issues"
          ],
          Audit: {
            mapping: "audits",
            allow_mapping: true,
            draw_children: true,
            show_view: GGRC.mustache_path + "/audits/tree.mustache",
            header_view: GGRC.mustache_path + "/audits/tree_header.mustache",
            footer_view: GGRC.mustache_path + "/audits/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/audits/tree_add_item.mustache"
          },
          Person: {
            show_view: GGRC.mustache_path + "/ggrc_basic_permissions/people_roles/authorizations_by_person_tree.mustache",
            footer_view: GGRC.mustache_path + "/ggrc_basic_permissions/people_roles/authorizations_by_person_tree_footer.mustache",
            parent_instance: GGRC.page_instance(),
            allow_reading: true,
            allow_mapping: true,
            allow_creating: true,
            model: CMS.Models.Person,
            mapping: "mapped_and_or_authorized_people"
          }
        },
        Audit: {
          _mixins: ["issues"],
          Request: {
            mapping: "active_requests",
            draw_children: true,
            show_view: GGRC.mustache_path + "/requests/tree.mustache",
            footer_view: GGRC.mustache_path + "/requests/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/requests/tree_add_item.mustache"
          },
          history: {
            mapping: "history",
            parent_instance: GGRC.page_instance(),
            draw_children: true,
            model: "Request",
            show_view: GGRC.mustache_path + "/requests/tree.mustache",
            footer_view: GGRC.mustache_path + "/requests/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/requests/tree_add_item.mustache",
            allow_mapping: false,
            allow_creating: false
          },
          Control: {
            mapping: "program_controls",
            parent_instance: GGRC.page_instance(),
            draw_children: true,
            model: CMS.Models.Control,
            show_view: GGRC.mustache_path + "/controls/tree.mustache",
            footer_view: GGRC.mustache_path + "/controls/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/controls/tree_add_item.mustache",
            allow_mapping: false,
            allow_creating: false
          },
          Program: {
            mapping: "_program",
            parent_instance: GGRC.page_instance(),
            draw_children: false,
            model: CMS.Models.Program,
            show_view: GGRC.mustache_path + "/programs/tree.mustache",
            allow_mapping: false,
            allow_creating: false
          },
          ControlAssessment: {
            mapping: "related_control_assessments",
            parent_instance: GGRC.page_instance(),
            allow_mapping: true,
            child_options: [related_objects_child_options],
            draw_children: true,
            model: CMS.Models.ControlAssessment,
            show_view: GGRC.mustache_path + "/base_objects/tree.mustache",
            header_view: GGRC.mustache_path + "/base_objects/tree_header.mustache",
            footer_view: GGRC.mustache_path + "/control_assessments/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/control_assessments/tree_add_item.mustache"
          }
        },
        directive: {
          _mixins: [
            "objectives", "controls", "business_objects"
          ]
        },
        Regulation: {
          _mixins: ["directive", "issues"],
          Section: section_child_options
        },
        Standard: {
          _mixins: ["directive", "issues"],
          Section: section_child_options
        },
        Policy: {
          _mixins: ["directive", "issues"],
          Section: section_child_options
        },
        Contract: {
          _mixins: ["directive", "issues"],
          Clause: clause_child_options
        },
        extended_audits: {
          Audit: {
            mapping: "related_audits_via_related_responses",
            allow_mapping: false,
            allow_creating: false,
            draw_children: true,
            show_view: GGRC.mustache_path + "/audits/tree.mustache",
            footer_view: null
          },
        },
        open_requests: {
          Request: {
            mapping: "open_requests",
            allow_mapping: false,
            allow_creating: false,
            draw_children: true,
            show_view: GGRC.mustache_path + "/requests/tree.mustache",
            footer_view: null
          }
        },
        Clause: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Section: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Objective: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Control: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "open_requests", "issues"],
        },
        ControlAssessment: {
          _mixins: ["governance_objects", "business_objects", "issues"],
          Audit: {
            mapping: "related_audits",
            draw_children: true,
            allow_creating: false,
            allow_mapping: true,
            show_view: GGRC.mustache_path + "/audits/tree.mustache",
            add_item_view: GGRC.mustache_path + "/audits/tree_add_item.mustache"
          },
          Section: {
            _mixins: ["directive"],
            mapping: "related_sections",
            child_options: [section_child_options],
            footer_view: GGRC.mustache_path + "/sections/tree_footer.mustache"
          },
          Clause: {
            _mixins: ["directive"],
            mapping: "related_clauses",
            child_options: [clause_child_options],
            footer_view: GGRC.mustache_path + "/clauses/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/clauses/tree_add_item.mustache"
          },
          Request: {
            mapping: "requests",
            draw_children: true,
            show_view: GGRC.mustache_path + "/requests/tree.mustache",
            footer_view: GGRC.mustache_path + "/requests/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/requests/tree_add_item.mustache"
          }
        },
        Issue: {
          _mixins: ["governance_objects", "business_objects"],
          Control: {
            mapping: "related_controls",
            draw_children: true,
            show_view: GGRC.mustache_path + "/controls/tree.mustache",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
          },
          Issue: {
            mapping: "related_issues",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache"
          },
          Audit: {
            mapping: "related_audits",
            draw_children: true,
            show_view: GGRC.mustache_path + "/audits/tree.mustache",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
          },
        },
        DataAsset: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Facility: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Market: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        OrgGroup: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Vendor: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Process: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Product: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Project: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        System: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Document: {
          _mixins: ["governance_objects", "business_objects", "extended_audits", "issues"]
        },
        Person: {
          _mixins: ["issues"],
          Request: {
            //mapping: "open_audit_requests",
            mapping: (/^\/objectBrowser\/?$/.test(window.location.pathname)) ?
              "all_open_audit_requests" : "open_audit_requests",
            draw_children: true,
            show_view: GGRC.mustache_path + "/requests/tree.mustache",
            footer_view: GGRC.mustache_path + "/requests/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/requests/tree_add_item.mustache"
          },
          Program: {
            mapping: "extended_related_programs_via_search",
            child_options: [related_objects_child_options],
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Regulation: {
            mapping: "extended_related_regulations_via_search",
            draw_children: true,
            child_options: [section_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache"
          },
          Contract: {
            mapping: "extended_related_contracts_via_search",
            draw_children: true,
            child_options: [clause_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache"
          },
          Standard: {
            mapping: "extended_related_standards_via_search",
            draw_children: true,
            child_options: [section_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache"
          },
          Policy: {
            mapping: "extended_related_policies_via_search",
            draw_children: true,
            child_options: [section_child_options],
            fetch_post_process: sort_sections,
            show_view: GGRC.mustache_path + "/directives/tree.mustache"
          },
          Audit: {
            mapping: "extended_related_audits_via_search",
            draw_children: true,
            show_view: GGRC.mustache_path + "/audits/tree.mustache"
          },
          Section: {
            model: CMS.Models.Section,
            mapping: "extended_related_sections_via_search",
            show_view: GGRC.mustache_path + "/sections/tree.mustache",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
            draw_children: true
          },
          Clause: {
            model: CMS.Models.Clause,
            mapping: "extended_related_clauses_via_search",
            show_view: GGRC.mustache_path + "/sections/tree.mustache",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache",
            draw_children: true
          },
          Objective: {
            mapping: "extended_related_objectives_via_search",
            draw_children: true,
            show_view: GGRC.mustache_path + "/objectives/tree.mustache",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
          },
          Control: {
            mapping: "extended_related_controls_via_search",
            draw_children: true,
            show_view: GGRC.mustache_path + "/controls/tree.mustache",
            footer_view: GGRC.mustache_path + "/base_objects/tree_footer.mustache",
            add_item_view: GGRC.mustache_path + "/base_objects/tree_add_item.mustache"
          },
          Issue: {
            mapping: "extended_related_issues_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          DataAsset: {
            mapping: "extended_related_data_assets_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Facility: {
            mapping: "extended_related_facilities_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Market: {
            mapping: "extended_related_markets_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          OrgGroup: {
            mapping: "extended_related_org_groups_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Vendor: {
            mapping: "extended_related_vendors_via_search",
            hild_options: [related_objects_child_options],
            draw_children: true
          },
          Process: {
            mapping: "extended_related_processes_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Product: {
            mapping: "extended_related_products_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Project: {
            mapping: "extended_related_projects_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          System: {
            mapping: "extended_related_systems_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          },
          Document: {
            mapping: "extended_related_documents_via_search"
          },
          ControlAssessment: {
            mapping: "extended_related_control_assessment_via_search",
            child_options: [related_objects_child_options],
            draw_children: true
          }
        }
      });

    // Disable editing on profile pages, as long as it isn't audits on the dashboard
    if (GGRC.page_instance() instanceof CMS.Models.Person) {
      var person_options = extra_content_controller_options.Person;
      can.each(person_options, function (options, model_name) {
        if (model_name !== 'Audit' || !/dashboard/.test(window.location)) {
          can.extend(options, {
            allow_creating: false,
            allow_mapping: false
          });
        }
      });
    }

    can.each(far_models, function (model_name) {
      if ((overridden_models.all && overridden_models.all.hasOwnProperty(model_name) && !overridden_models[model_name]) || (overridden_models[object.constructor.shortName] && overridden_models[object.constructor.shortName].hasOwnProperty(model_name) && !overridden_models[object.constructor.shortName][model_name]))
        return;
      var sources = [],
        far_model, descriptor = {},
        widget_id;

      far_model = CMS.Models[model_name];
      if (far_model) {
        widget_id = far_model.table_singular;
        descriptor = {
          instance: object,
          far_model: far_model,
          mapping: GGRC.Mappings.get_canonical_mapping(object.constructor.shortName, far_model.shortName)
        };
      } else {
        widget_id = model_name;
      }

      // Custom overrides
      if (extra_descriptor_options.all && extra_descriptor_options.all[model_name]) {
        $.extend(descriptor, extra_descriptor_options.all[model_name]);
      }

      if (extra_descriptor_options[object.constructor.shortName] && extra_descriptor_options[object.constructor.shortName][model_name]) {
        $.extend(descriptor, extra_descriptor_options[object.constructor.shortName][model_name]);
      }

      if (extra_content_controller_options.all && extra_content_controller_options.all[model_name]) {
        $.extend(true, descriptor, {
          content_controller_options: extra_content_controller_options.all[model_name]
        });
      }

      if (extra_content_controller_options[object.constructor.shortName] && extra_content_controller_options[object.constructor.shortName][model_name]) {
        $.extend(true, descriptor, {
          content_controller_options: extra_content_controller_options[object.constructor.shortName][model_name]
        });
      }

      widget_list.add_widget(object.constructor.shortName, widget_id, descriptor);
    });

  });

})(window.can, window.can.$);
