/*!
    Copyright (C) 2016 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  var CoreExtension = {};

  CoreExtension.name = 'core"';
  GGRC.extensions.push(CoreExtension);
  _.extend(CoreExtension, {
    object_type_decision_tree: function () {
      return {
        program: CMS.Models.Program,
        snapshot: CMS.Models.Snapshot,
        audit: CMS.Models.Audit,
        contract: CMS.Models.Contract,
        policy: CMS.Models.Policy,
        standard: CMS.Models.Standard,
        regulation: CMS.Models.Regulation,
        org_group: CMS.Models.OrgGroup,
        vendor: CMS.Models.Vendor,
        project: CMS.Models.Project,
        facility: CMS.Models.Facility,
        product: CMS.Models.Product,
        data_asset: CMS.Models.DataAsset,
        access_group: CMS.Models.AccessGroup,
        market: CMS.Models.Market,
        system_or_process: {
          _discriminator: function (data) {
            if (data.is_biz_process) {
              return CMS.Models.Process;
            }
            return CMS.Models.System;
          }
        },
        system: CMS.Models.System,
        process: CMS.Models.Process,
        control: CMS.Models.Control,
        assessment: CMS.Models.Assessment,
        assessment_template: CMS.Models.AssessmentTemplate,
        request: CMS.Models.Request,
        issue: CMS.Models.Issue,
        objective: CMS.Models.Objective,
        section: CMS.Models.Section,
        clause: CMS.Models.Clause,
        person: CMS.Models.Person,
        role: CMS.Models.Role,
        threat: CMS.Models.Threat,
        vulnerability: CMS.Models.Vulnerability,
        template: CMS.Models.Template
      };
    },
    init_widgets: function () {
      var base_widgets_by_type = GGRC.tree_view.base_widgets_by_type;
      var widget_list = new GGRC.WidgetList('ggrc_core');
      var object_class = GGRC.infer_object_type(GGRC.page_object);
      var object_table = object_class && object_class.table_plural;
      var object = GGRC.page_instance();
      var path = GGRC.mustache_path;
      var info_widget_views;
      var summaryWidgetViews;
      var model_names;
      var possible_model_type;
      var treeViewDepth = 2;
      var relatedObjectsChildOptions = [GGRC.Utils.getRelatedObjects(treeViewDepth)];

      // TODO: Really ugly way to avoid executing IIFE - needs cleanup
      if (!GGRC.page_object) {
        return;
      }
      // Info and summary widgets display the object information instead of listing
      // connected objects.
      summaryWidgetViews = {
        audits: path + '/audits/summary.mustache'
      };
      if (summaryWidgetViews[object_table]) {
        widget_list.add_widget(object.constructor.shortName, 'summary', {
          widget_id: 'summary',
          content_controller: GGRC.Controllers.SummaryWidget,
          instance: object,
          widget_view: summaryWidgetViews[object_table],
          order: 3
        });
      }
      info_widget_views = {
        programs: path + '/programs/info.mustache',
        audits: path + '/audits/info.mustache',
        people: path + '/people/info.mustache',
        policies: path + '/policies/info.mustache',
        objectives: path + '/objectives/info.mustache',
        controls: path + '/controls/info.mustache',
        systems: path + '/systems/info.mustache',
        processes: path + '/processes/info.mustache',
        products: path + '/products/info.mustache',
        assessments: path + '/assessments/info.mustache',
        assessment_templates:
          path + '/assessment_templates/info.mustache',
        requests: path + '/requests/info.mustache',
        issues: path + '/issues/info.mustache',
        snapshots: path + '/snapshots/info.mustache'
      };
      widget_list.add_widget(object.constructor.shortName, 'info', {
        widget_id: 'info',
        content_controller: GGRC.Controllers.InfoWidget,
        instance: object,
        widget_view: info_widget_views[object_table],
        order: 5
      });
      model_names = can.Map.keys(base_widgets_by_type);
      model_names.sort();
      possible_model_type = model_names.slice();
      possible_model_type.push('Request'); // Missing model-type by selection
      can.each(model_names, function (name) {
        var w_list;
        var child_model_list = [];

        GGRC.tree_view.basic_model_list.push({
          model_name: name,
          display_name: CMS.Models[name].title_singular
        });
        // Initialize child_model_list, and child_display_list each model_type
        w_list = base_widgets_by_type[name];

        can.each(w_list, function (item) {
          if (possible_model_type.indexOf(item) !== -1) {
            child_model_list.push({
              model_name: item,
              display_name: CMS.Models[item].title_singular
            });
          }
        });
        GGRC.tree_view.sub_tree_for.attr(name, {
          model_list: child_model_list,
          display_list: CMS.Models[name].tree_view_options.child_tree_display_list || w_list
        });
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
              if (typeof (mixin) === 'string') {
                // If string, recursive lookup
                if (!definitions[mixin]) {
                  console.debug('Undefined mixin: ' + mixin, definitions);
                } else {
                  can.extend(
                    final_definition,
                    reify_mixins(definitions[mixin])
                  );
                }
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
        // here we are going to define extra descriptor options, meaning that
        //  these will be used as extra options to create widgets on top of

      // NOTE: By default, widgets are sorted alphabetically (the value of
      // the order 100+), but the objects with higher importance that should
      // be  prioritized use order values below 100. An order value of 0 is
      // reserved for the "info" widget which always comes first.
      extra_descriptor_options = {
        all: {
          Standard: {
            order: 10
          },
          Regulation: {
            order: 20
          },
          Contract: {
            order: 30
          },
          Section: {
            order: 40
          },
          Objective: {
            order: 50
          },
          Control: {
            order: 60
          },
          AccessGroup: {
            order: 100
          },
          Assessment: {
            order: 110
          },
          Audit: {
            order: 120
          },
          Clause: {
            order: 130
          },
          DataAsset: {
            order: 140
          },
          Document: {
            widget_icon: 'fa fa-link',
            order: 150
          },
          Facility: {
            order: 160
          },
          Issue: {
            order: 170
          },
          Market: {
            order: 180
          },
          OrgGroup: {
            order: 190
          },
          Person: {
            widget_icon: 'fa fa-person',
            order: 200
          },
          Policy: {
            order: 210
          },
          Process: {
            order: 220
          },
          Product: {
            order: 230
          },
          Program: {
            order: 240
          },
          Project: {
            order: 250
          },
          Request: {
            order: 260
          },
          System: {
            order: 270
          },
          Vendor: {
            order: 280
          },
          Snapshot: {
            order: 290
          }
        },
        Contract: {
          Clause: {
            widget_name: function () {
              var $objectArea = $('.object-area');
              if ($objectArea.hasClass('dashboard-area')) {
                return 'Clauses';
              } else {
                return 'Mapped Clauses';
              }
            }
          }
        },
        Program: {
          Person: {
            widget_id: 'person',
            widget_name: 'People',
            widget_icon: 'person',
            content_controller: GGRC.Controllers.TreeView
          }
        },

        // An Audit has a different set of object that are more relevant to it,
        // thus these objects have a customized priority. On the other hand,
        // the object otherwise prioritized by default (e.g. Regulation) have
        // their priority lowered so that they fit nicely into the alphabetical
        // order among the non-prioritized object types.
        Audit: {
          Assessment: {
            order: 10
          },
          Request: {
            widget_id: 'Request',
            widget_name: 'Requests',
            order: 20
          },
          Issue: {
            order: 30
          },
          AssessmentTemplate: {
            order: 40
          },
          Contract: {
            order: 133  // between default Clause (130) and DataAsset (140)
          },
          Control: {
            order: 137  // between default Clause (130) and DataAsset (140)
          },
          Objective: {
            order: 182  // between default Market (180) and OrgGroup (190)
          },
          Regulation: {
            order: 257  // between default Project (250) and Request (260)
          },
          program: {
            widget_id: 'program',
            widget_name: 'Program',
            widget_icon: 'program'
          },
          Section: {
            order: 263  // between default Request (260) and System (270)
          },
          Standard: {
            order: 267  // between default Request (260) and System (270)
          },
          Person: {
            widget_id: 'person',
            widget_name: 'People',
            widget_icon: 'person',
            // NOTE: "order" not overridden
            content_controller: GGRC.Controllers.TreeView,
            content_controller_options: {
              mapping: 'authorized_people',
              allow_mapping: false,
              allow_creating: false
            }
          }
        },
        Control: {
          Request: {
            widget_id: 'Request',
            widget_name: 'Requests'
          }
        },
        Person: {
          Request: {
            widget_id: 'Request',
            widget_name: 'Requests'
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
        },
        all: {
          Document: false
        }
      },

      extra_content_controller_options = apply_mixins({
        snapshots: {
          Snapshot: {
            mapping: 'snapshots',
            child_options: relatedObjectsChildOptions,
            draw_children: false,
            show_view: path + '/snapshots/tree.mustache',
            content_controller_options: {
              allow_mapping: false,
              allow_creating: false
            }
          }
        },
        snapshot_parent: {
          Audit: {
            mapping: 'snapshot_audit',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: GGRC.mustache_path + '/audits/tree.mustache',
            footer_view:
            GGRC.mustache_path + '/base_objects/tree_footer.mustache',
            add_item_view:
            GGRC.mustache_path + '/base_objects/tree_add_item.mustache'
          }
        },
        objectives: {
          Objective: {
            mapping: 'objectives',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/objectives/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/objectives/tree_add_item.mustache'
          }
        },
        controls: {
          Control: {
            mapping: 'controls',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/controls/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/controls/tree_add_item.mustache'
          }
        },
        business_objects: {
          Audit: {
            mapping: 'related_audits',
            draw_children: true,
            child_options: relatedObjectsChildOptions,
            allow_mapping: true,
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
          AccessGroup: {
            mapping: 'related_access_groups',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          DataAsset: {
            mapping: 'related_data_assets',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Facility: {
            mapping: 'related_facilities',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Market: {
            mapping: 'related_markets',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          OrgGroup: {
            mapping: 'related_org_groups',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Vendor: {
            mapping: 'related_vendors',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Process: {
            mapping: 'related_processes',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Product: {
            mapping: 'related_products',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Project: {
            mapping: 'related_projects',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          System: {
            mapping: 'related_systems',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Assessment: {
            mapping: 'related_assessments',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            footer_view: path + '/base_objects/tree_footer.mustache'
          },
          Request: {
            mapping: 'related_requests',
            child_options: [
              _.extend({}, relatedObjectsChildOptions[0], {
                mapping: 'info_related_objects'
              })
            ],
            draw_children: true
          },
          Document: {
            mapping: 'documents',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Person: {
            mapping: 'people',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Program: {
            mapping: 'programs',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        issues: {
          Issue: {
            mapping: 'related_issues',
            footer_view: GGRC.mustache_path +
              '/base_objects/tree_footer.mustache',
            add_item_view: GGRC.mustache_path +
              '/base_objects/tree_add_item.mustache',
            child_options: relatedObjectsChildOptions.concat({
              model: CMS.Models.Person,
              mapping: 'people',
              show_view: GGRC.mustache_path +
                '/base_objects/tree.mustache',
              footer_view: GGRC.mustache_path +
                '/base_objects/tree_footer.mustache',
              draw_children: false
            }),
            draw_children: true
          }
        },
        governance_objects: {
          Regulation: {
            mapping: 'regulations',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/directives/tree_add_item.mustache'
          },
          Contract: {
            mapping: 'contracts',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache'
          },
          Policy: {
            mapping: 'policies',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/directives/tree_add_item.mustache'
          },
          Standard: {
            mapping: 'standards',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/directives/tree_add_item.mustache'
          },
          Control: {
            mapping: 'controls',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Objective: {
            mapping: 'objectives',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Section: {
            mapping: 'sections',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        Program: {
          _mixins: [
            'governance_objects', 'objectives', 'controls',
            'business_objects', 'issues'
          ],
          Audit: {
            mapping: 'audits',
            allow_mapping: true,
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/audits/tree.mustache',
            header_view: path + '/audits/tree_header.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
          Person: {
            show_view: path + '/ggrc_basic_permissions/people_roles/authorizations_by_person_tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            parent_instance: GGRC.page_instance(),
            allow_reading: true,
            allow_mapping: true,
            allow_creating: true,
            model: CMS.Models.Person,
            mapping: 'mapped_and_or_authorized_people',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        Audit: {
          _mixins: ['issues', 'governance_objects', 'business_objects'],
          Request: {
            mapping: 'active_requests',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/requests/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/requests/tree_add_item.mustache'
          },
          Program: {
            mapping: '_program',
            parent_instance: GGRC.page_instance(),
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            model: CMS.Models.Program,
            show_view: path + '/programs/tree.mustache',
            allow_mapping: false,
            allow_creating: false
          },
          Section: {
            mapping: 'sections',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Assessment: {
            mapping: 'related_assessments',
            parent_instance: GGRC.page_instance(),
            allow_mapping: true,
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            model: CMS.Models.Assessment,
            show_view: path + '/base_objects/tree.mustache',
            header_view: path + '/base_objects/tree_header.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/assessments/tree_add_item.mustache'
          },
          AssessmentTemplate: {
            mapping: 'related_assessment_templates',
            child_options: relatedObjectsChildOptions,
            draw_children: false,
            allow_mapping: false,
            show_view: GGRC.mustache_path +
              '/base_objects/tree.mustache',
            footer_view: GGRC.mustache_path +
              '/base_objects/tree_footer.mustache',
            add_item_view: GGRC.mustache_path +
              '/assessment_templates/tree_add_item.mustache'
          },
          Person: {
            widget_id: 'person',
            widget_name: 'People',
            widget_icon: 'person',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            content_controller: GGRC.Controllers.TreeView,
            content_controller_options: {
              mapping: 'authorized_people',
              allow_mapping: false,
              allow_creating: false
            }
          }
        },
        directive: {
          _mixins: [
            'objectives', 'controls', 'business_objects'
          ],
          Section: {
            mapping: 'sections',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
         },
        Regulation: {
          _mixins: ['directive', 'issues']
        },
        Standard: {
          _mixins: ['directive', 'issues']
        },
        Policy: {
          _mixins: ['directive', 'issues']
        },
        Contract: {
          _mixins: ['directive', 'issues']
        },
        Clause: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        Section: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        Objective: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        Control: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        Request: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            allow_creating: false,
            allow_mapping: false,
            show_view: path + '/audits/tree.mustache',
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
        },
        Assessment: {
          _mixins: ['governance_objects', 'business_objects', 'issues'],
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            allow_creating: false,
            allow_mapping: true,
            show_view: path + '/audits/tree.mustache',
            add_item_view: path + '/audits/tree_add_item.mustache'
          },
          Section: {
            mapping: 'sections',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Clause: {
            mapping: 'clauses',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Request: {
            mapping: 'related_requests',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/requests/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/requests/tree_add_item.mustache'
          }
        },
        Issue: {
          _mixins: ['governance_objects', 'business_objects'],
          Control: {
            mapping: 'related_controls',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/controls/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Issue: {
            mapping: 'related_issues',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Audit: {
            mapping: 'related_audits',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: GGRC.mustache_path + '/audits/tree.mustache',
            footer_view:
              GGRC.mustache_path + '/base_objects/tree_footer.mustache',
            add_item_view:
              GGRC.mustache_path + '/base_objects/tree_add_item.mustache'
          }
        },
        Snapshot: {
          _mixins: ['governance_objects', 'business_objects'],
          AccessGroup: {
            mapping: 'related_access_groups',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          }
        },
        AccessGroup: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        DataAsset: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Facility: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Market: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        OrgGroup: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Vendor: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Process: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Product: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Project: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        System: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Document: {
          _mixins: ['governance_objects', 'business_objects', 'issues', 'snapshots', 'snapshot_parent']
        },
        Person: {
          _mixins: ['issues'],
          Request: {
            mapping: (/^\/objectBrowser\/?$/.test(window.location.pathname)) ?
              'all_open_audit_requests' : 'open_audit_requests',
            draw_children: true,
            child_options: relatedObjectsChildOptions,
            show_view: GGRC.mustache_path + '/requests/tree.mustache',
            footer_view: GGRC.mustache_path + '/base_objects/tree_footer.mustache',
            add_item_view: GGRC.mustache_path + '/requests/tree_add_item.mustache'
          },
          Program: {
            mapping: 'extended_related_programs_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections
          },
          Regulation: {
            mapping: 'extended_related_regulations_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache'
          },
          Contract: {
            mapping: 'extended_related_contracts_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache'
          },
          Standard: {
            mapping: 'extended_related_standards_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache'
          },
          Policy: {
            mapping: 'extended_related_policies_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            fetch_post_process: sort_sections,
            show_view: path + '/directives/tree.mustache'
          },
          Audit: {
            mapping: 'extended_related_audits_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/audits/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache'
          },
          Section: {
            model: CMS.Models.Section,
            mapping: 'extended_related_sections_via_search',
            show_view: GGRC.mustache_path + '/sections/tree.mustache',
            footer_view:
              GGRC.mustache_path + '/base_objects/tree_footer.mustache',
            add_item_view:
              GGRC.mustache_path + '/base_objects/tree_add_item.mustache',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Clause: {
            model: CMS.Models.Clause,
            mapping: 'extended_related_clauses_via_search',
            show_view: GGRC.mustache_path + '/sections/tree.mustache',
            footer_view:
              GGRC.mustache_path + '/base_objects/tree_footer.mustache',
            add_item_view:
              GGRC.mustache_path + '/base_objects/tree_add_item.mustache',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Objective: {
            mapping: 'extended_related_objectives_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/objectives/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Control: {
            mapping: 'extended_related_controls_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            show_view: path + '/controls/tree.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache',
            add_item_view: path + '/base_objects/tree_add_item.mustache'
          },
          Issue: {
            mapping: 'extended_related_issues_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            footer_view: GGRC.mustache_path + '/base_objects/tree_footer.mustache'
          },
          AccessGroup: {
            mapping: 'extended_related_access_groups_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          DataAsset: {
            mapping: 'extended_related_data_assets_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Facility: {
            mapping: 'extended_related_facilities_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Market: {
            mapping: 'extended_related_markets_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          OrgGroup: {
            mapping: 'extended_related_org_groups_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Vendor: {
            mapping: 'extended_related_vendors_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Process: {
            mapping: 'extended_related_processes_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Product: {
            mapping: 'extended_related_products_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Project: {
            mapping: 'extended_related_projects_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          System: {
            mapping: 'extended_related_systems_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true
          },
          Document: {
            mapping: 'extended_related_documents_via_search'
          },
          Assessment: {
            mapping: 'extended_related_assessment_via_search',
            child_options: relatedObjectsChildOptions,
            draw_children: true,
            add_item_view: null,
            header_view: path + '/assessments/tree_header.mustache',
            footer_view: path + '/base_objects/tree_footer.mustache'
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
              allow_mapping: true
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
    }
  });
})(window.can, window.can.$);
