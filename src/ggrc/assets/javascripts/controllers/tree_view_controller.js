/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//= require can.jquery-all

function _firstElementChild(el) {
  if (el.nodeType === Node.DOCUMENT_FRAGMENT_NODE) {
    for (i=0; i<el.childNodes.length; i++) {
      if (el.childNodes[i].nodeType !== Node.TEXT_NODE)
        return el.childNodes[i];
    }
  } else {
    return el;
  }
}


function _display_tree_subpath(el, path, attempt_counter) {
  attempt_counter || (attempt_counter = 0);

  var rest = path.split("/")
    , type = rest.shift()
    , id = rest.shift()
    , selector = "[data-object-type=" + type + "][data-object-id=" + id + "]"
    , $node
    , $next_node
    , node_controller
    , scroll_delay = 0;
    ;

  rest = rest.join("/");

  if (type || id) {
    $node = el.find(selector);

    // sometimes nodes haven't loaded yet, wait for them
    if (!$node.size() && attempt_counter < 5) {
      setTimeout(function () {
        _display_tree_subpath(el, path, attempt_counter+1);
      }, 100);
      return;
    }

    if (!rest.length) {
      var controller = $node
              .closest(".cms_controllers_tree_view_node")
              .control();

      if (controller) {
        controller.select();
        scroll_delay = 750;
      }
    } else {
      node_controller = $node.control();
      if (node_controller && node_controller.display_path) {
         return node_controller.display_path(rest);
      }
    }

    return new $.Deferred().resolve();
  }
  else {
    return new $.Deferred().resolve();
  }
}


can.Observe("can.Observe.TreeOptions", {
  defaults : {
    instance : undefined
    , parent : null
    , children_drawn : false
  }
}, {
  // init : function() {
  //   this.bind("child_options.*.list", function(ev, newVal) {
  //     this.attr("children_drawn", !newVal.length)
  //     .attr("children_drawn", !!newVal.length);
  //   });
  // }
});

can.Control("CMS.Controllers.TreeLoader", {
  defaults : {}
}, {
  init_spinner: function() {
    console.log("treeLoader.init_spinner");
    var spinner,
        $spinner,
        $spinner_li,
        $footer;

    if (this.element) {
      // Only show the spinner if this is the last subtree
      // FIXME: This spinner will disappear when this list is completely
      //   loaded, even if other lists are still pending.
      if (this.element.next().length > 0)
        return;

      $footer = this.element.children('.tree-item-add').first();
      spinner = new Spinner({
          "radius": 4
        , "length": 4
        , "width": 2
        }).spin();
      $spinner = $(spinner.el);
      $spinner_li = $('<li class="tree-item-add tree-item tree-spinner" />');
      $spinner_li.append($spinner);
      $spinner.css({
          display: 'inline-block'
        , paddingLeft: '20px'
        , left: '10px'
        , top: '-4px'
      });
      // Admin dashboard
      if ($footer.length == 0 && this.element.children('.tree-structure').length > 0) {
        this.element.children('.tree-structure').append($spinner_li);
      }
      // My Work
      else if($footer.length == 0){
        this.element.append($spinner_li);
      }
      else {
        $footer.before($spinner_li);
      }
    }
  }
  , prepare: function() {
    var that = this;

    if (this._prepare_deferred)
      return this._prepare_deferred;

    this._prepare_deferred = new $.Deferred();
    this._prepare_deferred.resolve();

    this._attached_deferred.then(function() {
      if (that.element) {
        that.element.trigger("updateCount", 0);
        that.init_count();
      }
    });

    return this._prepare_deferred;
  }

  , show_info_pin: function() {
    if (this.element && !this.element.data('no-pin')) {
      var children = this.element.children(),
          controller = children && children.find('.select:visible')
              .first()
              .closest(".cms_controllers_tree_view_node")
              .control();

      if (controller) {
        controller.select();
      }
    }
  }

  , _will_navigate: function () {
    return !!window.location.hash.match(/#.+(\/.+)+/);
  }

  , display: function() {
      //console.log("tree_view.display()");
      var that = this
        , tracker_stop = GGRC.Tracker.start(
            "TreeView", "display", this.options.model.shortName)
        ;

      if (this._display_deferred) {
        if (!this._will_navigate()) {
          this.show_info_pin();
        }
        return this._display_deferred;
      }

      this._display_deferred = $.when(this._attached_deferred, this.prepare());

      this._display_deferred = this._display_deferred.then(this._ifNotRemoved(function() {
        return $.when(that.fetch_list(), that.init_view())
          .then(that._ifNotRemoved(that.proxy("draw_list")));
      })).done(tracker_stop);

      this._display_deferred.then(function(e){
        if (!this._will_navigate()) {
          this.show_info_pin();
        }
      }.bind(this));

      return this._display_deferred;
    }
  , draw_list : function(list) {
    console.log("tree_view_controller.draw_list", list);

    if (this._draw_list_deferred)
      return this._draw_list_deferred;
    this._draw_list_deferred = new $.Deferred();
    if (this.element && !this.element.closest('body').length)
      return;

    var that = this
      , refresh_queue = new RefreshQueue();

    if(list) {
      list = list.length == null ? new can.Observe.List([list]) : list;
    } else {
      list = this.options.list;
    }

    if(!this.element)
      return;  //controller has been destroyed

    if(!this.options.original_list) {
      this.options.attr("original_list", list);
    }
    this.options.attr("list", []);
    this.on();

    var temp_list = [];
    can.each(list, function(v, i) {
      var item = that.prepare_child_options(v);
      temp_list.push(item);
      if(!item.instance.selfLink) {
        refresh_queue.enqueue(v.instance);
      }
    });

    temp_list = can.map(temp_list, function(o) { if (o.instance.selfLink) return o; });
    this._draw_list_deferred = this.enqueue_items(temp_list);
    return this._draw_list_deferred;
  }
  , _loading_started: function() {
      if (!this._loading_deferred) {
        this._loading_deferred = new $.Deferred();
        this.init_spinner();
        this.element.trigger("loading");
      }
    }

  , _loading_finished: function() {
      var loading_deferred;
      if (this._loading_deferred) {
        this.element.trigger("loaded");
        this.element.find(".tree-spinner").remove();
        loading_deferred = this._loading_deferred;
        this._loading_deferred = null;
        loading_deferred.resolve();
      }

      // change inner tree title span4 into span8 class
      $(".inner-tree > .tree-structure > .tree-item > .item-main").find(".row-fluid").find("[class*=span]:last").attr("class", "span8");

    }

  , enqueue_items: function(items) {
      console.log("tree_loader.enqueue_items");
      var that = this;

      if (!items || items.length == 0) {
        return new $.Deferred().resolve();
      }

      if (!this._pending_items) {
        this._pending_items = [];
        this._loading_started();
      }

      $.when.apply($, can.map(items, function(item) {
        var instance = item.instance || item;
        if (instance.custom_attribute_values) {
          return instance.refresh_all('custom_attribute_values');
        }
      })).then(function(){
        that.insert_items(items);
        that._loading_finished();
      });
      return this._loading_deferred;
    }

  , insert_items: function(items) {
      console.log("tree_loader.insert_items", items);
      var that = this
        , prepped_items = []
        ;

      can.each(items, function(item) {
        var prepped = that.prepare_child_options(item);
        if (prepped.instance.selfLink) {
          prepped_items.push(prepped);
        }
      });

      if (prepped_items.length > 0) {
        this.options.list.push.apply(this.options.list, prepped_items);
        this.add_child_lists(prepped_items);
      }
    }
});

CMS.Controllers.TreeLoader("CMS.Controllers.TreeView", {
  //static properties
  defaults : {
    model : null
    , header_view : GGRC.mustache_path + "/base_objects/tree_header.mustache"
    , show_view : null
    , show_header : false
    , footer_view : null
    , add_item_view : null
    , parent : null
    , list : null
    , single_object : false
    , find_params : {}
    , sort_property : null
    , sort_direction: null
    , sort_by: null
    , sort_function : null
    , sortable : true
    , filter : null
    , start_expanded : false //true
    , draw_children : true
    , find_function : null
    , options_property : "tree_view_options"
    , allow_reading : true
    , allow_mapping : true
    , allow_creating : true
    , child_options : [] //this is how we can make nested configs. if you want to use an existing
    //example child option :
    // { property : "controls", model : CMS.Models.Control, }
    // { parent_find_param : "system_id" ... }
  },
  do_not_propagate : [
    'header_view', 'footer_view', 'add_item_view', 'list', 'original_list', 'single_object', 'find_function',
    'find_all_deferred'
  ]
}, {
  //prototype properties
  setup : function(el, opts) {
    var that = this;
    typeof this._super === "function" && this._super.apply(this, [el]);
    if(opts instanceof can.Observe) {

      this.options = opts;
      if (typeof(this.options.model) === "string")
        this.options.attr("model", CMS.Models[this.options.model]);
      if(this.options.model) {
        can.each(this.options.model[opts.options_property || this.constructor.defaults.options_property], function(v, k) {
          that.options.hasOwnProperty(k) || that.options.attr(k, v);
        });
      }
      can.each(this.constructor.defaults, function(v, k) {
        that.options.hasOwnProperty(k) || that.options.attr(k, v);
      });
    } else {
      if (typeof(opts.model) === "string")
        opts.model = CMS.Models[opts.model];
      this.options = new can.Observe(this.constructor.defaults).attr(opts.model ? opts.model[opts.options_property || this.constructor.defaults.options_property] : {}).attr(opts);
    }
  },
  deselect: function () {
    var active = this.element.find('.cms_controllers_tree_view_node.active');
    active.removeClass('active');
    this.update_hash_fragment(active.length);
  },
  update_hash_fragment: function (status) {
    if (!status) {
      return;
    }
    var hash = window.location.hash.split('/');
    hash.pop();
    window.location.hash = hash.join('/');
  },

  // Total display with is set to be span12.
  // Default: title : span4
  //          middle selectable : span4, by default 2 attributes are selected
  //          action : span4
  // When user selects 3 middle selectable attribute, title width is reduced to span3
  // and when user selects 4 attributes, the action column is also reduced to span3
  setup_column_width: function () {
    var display_options,
        display_width = 12,
        attr_count = this.options.display_attr_list.length,
        widths = {
          defaults: [4, 4, 4],
          0: [7, 1, 4],
          3: [3, 5, 4],
          4: [3, 6, 3],
        },
        selected_widths = widths[attr_count] || widths.defaults;

    display_options = {
      title_width: selected_widths[0],
      selectable_width: selected_widths[1],
      action_width: selected_widths[2],
      selectable_attr_width: display_width / Math.max(attr_count, 1)
    }
    this.options.attr('display_options', display_options);
  },

  //Displays attribute list for tree-header, Select attribute list drop down
  //Gets default and custom attribute list for each model, and sets upthe display-list
  init_display_options: function (opts) {
    var i, saved_attr_list, display_width = 12, //total width of display = span12
        select_attr_list = [], display_attr_list = [],
        model = opts.model, model_name = model.model_singular,
        model_definition = model().class.root_object,
        mandatory_attr_names, display_attr_names;

    //get standard attrs for each model
    can.each(model.tree_view_options.attr_list || can.Model.Cacheable.attr_list, function (item) {
        if (!item.attr_sort_field) {
          item.attr_sort_field = item.attr_name;
        }
        select_attr_list.push(item);
    });
    //Get mandatory_attr_names
    mandatory_attr_names = model.tree_view_options.mandatory_attr_names ?
      model.tree_view_options.mandatory_attr_names :
        can.Model.Cacheable.tree_view_options.mandatory_attr_names;

    //get custom attrs
    can.each(GGRC.custom_attr_defs, function (def, i) {
      if (def.definition_type === model_definition && def.attribute_type !== 'Rich Text') {
        var obj = {};
        obj.attr_title = obj.attr_name = def.title;
        obj.display_status = false;
        obj.attr_type = 'custom';
        obj.attr_sort_field = 'custom:'+obj.attr_name;
        select_attr_list.push(obj);
      }
    });

    //Get the display attr_list from local storage
    saved_attr_list = this.display_prefs.getTreeViewHeaders(model_name);

    if (!saved_attr_list.length) {
      //Initialize the display status, Get display_attr_names for model
      display_attr_names = model.tree_view_options.display_attr_names ?
        model.tree_view_options.display_attr_names :
          can.Model.Cacheable.tree_view_options.display_attr_names;

      for (i = 0; i < select_attr_list.length; i++) {
        var obj = select_attr_list[i];

        obj.display_status = display_attr_names.indexOf(obj.attr_name) !== -1;
        obj.mandatory = mandatory_attr_names.indexOf(obj.attr_name) !== -1;
      }
    } else {
      //Mandatory attr should be always displayed in tree view
      can.each(mandatory_attr_names, function (attr_name) {
        saved_attr_list.push(attr_name);
      });

      for (i = 0; i < select_attr_list.length; i++) {
        var obj = select_attr_list[i];
        obj.display_status = saved_attr_list.indexOf(obj.attr_name) !== -1;
        obj.mandatory = mandatory_attr_names.indexOf(obj.attr_name) !== -1;
      }
    }

    //Create display list
    can.each(select_attr_list, function (item) {
      if (!item.mandatory && item.display_status) {
          display_attr_list.push(item);
      }
    });

    this.options.attr('select_attr_list', select_attr_list);
    this.options.attr('display_attr_list', display_attr_list);
    this.setup_column_width();

  },

  init : function(el, opts) {
    CMS.Models.DisplayPrefs.getSingleton().then(function (display_prefs) {
      this.display_prefs = display_prefs;
      this.options.filter_is_hidden = this.display_prefs.getFilterHidden();

      this.element.uniqueId();

      if ('parent_instance' in opts && 'status' in opts.parent_instance){
        var setAllowMapping = function(){
          var is_accepted = opts.parent_instance.attr('status') === 'Accepted'
            , admin = Permission.is_allowed("__GGRC_ADMIN__")
            ;
          this.options.attr("allow_mapping_or_creating", (admin || !is_accepted) &&
                            (this.options.allow_mapping || this.options.allow_creating));
        }.bind(this);
        setAllowMapping();
        opts.parent_instance.bind('change', setAllowMapping);
      }
      else{
        this.options.attr("allow_mapping_or_creating",
          this.options.allow_mapping || this.options.allow_creating);
      }

      if(!this.options.scroll_element) {
        this.options.attr("scroll_element", $(".object-area"));
      }

      // Override nested child options for allow_* properties
      var allowed = {};
      this.options.each(function(item, prop) {
        if (prop.indexOf('allow') === 0 && item === false) {
          allowed[prop] = item;
        }
      });
      this.options.attr('child_options', this.options.child_options.slice(0));
      can.each(this.options.child_options, function(options, i) {
        this.options.child_options.attr(i, new can.Observe(can.extend(options.attr(), allowed)));
      }.bind(this));

      this.options.attr('filter_is_hidden', display_prefs.getFilterHidden());

      this._attached_deferred = new $.Deferred();
      if (this.element && this.element.closest('body').length) {
        this._attached_deferred.resolve();
      }
      this.init_display_options(opts);
    }.bind(this));

  }

  , " inserted": function() {
      console.log("inserted");
      this._attached_deferred.resolve();
    }
  , init_view : function() {
      console.log("tree_view.TreeView.init_view");
      var dfds = [];

      if(this.options.header_view && this.options.show_header) {
        dfds.push(
          can.view(this.options.header_view, $.when(this.options)).then(
            this._ifNotRemoved(function(frag) {
              console.log("rendering tree view");
              this.element.before(frag);
              // TODO: This is a workaround so we can toggle filter. We should refactor this ASAP.
              can.bind.call(
                  this.element.parent().find('.filter-trigger > a'), 
                  'click', 
                  function () {
                    if (this.display_prefs.getFilterHidden()) {
                      this.show_filter();
                    } else {
                      this.hide_filter();
                    }
                  }.bind(this)
              );

              can.bind.call(this.element.parent().find('.widget-col-title[data-field]'),
                            'click',
                            this.sort.bind(this)
                           );
              can.bind.call(this.element.parent().find('.set-tree-attrs'), 
                            'click',
                            this.set_tree_attrs.bind(this)
                           );
            }.bind(this))));
      }

      // Init the spinner if items need to be loaded:
      dfds.push(this.init_count().then(function(count) {
        if (!this.element) {
          return;
        }
        if (count()) {
          this._loading_started();
        } else {
          this.element.trigger("loaded");
        }
      }.bind(this)));

      if (this.options.footer_view) {
        dfds.push(
          can.view(this.options.footer_view, this.options,
            this._ifNotRemoved(function(frag) {
              this.element.append(frag);
            }.bind(this))
          ));
      }
      return $.when.apply($.when, dfds);
    }

  , init_count : function() {
      var self = this
        ;

      if (this.get_count_deferred)
        return this.get_count_deferred;

      if (this.options.parent_instance && this.options.mapping) {
        this.get_count_deferred =
          this.options.parent_instance.get_list_counter(this.options.mapping);
      } else if (this.options.list_loader) {
        this.get_count_deferred =
          this.options.list_loader(this.options.parent_instance)
            .then(function(list) {
              return can.compute(function() {
                return list.attr("length");
              });
            });
      }
      if (this.get_count_deferred) {
        this.get_count_deferred.then(this._ifNotRemoved(function(count) {
          self.element && self.element.trigger("updateCount", count());
          count.bind("change", self._ifNotRemoved(function() {
            self.element.trigger("updateCount", count());
          }));
        }));
      } else {
        // FIXME: Does this ever happen?
        this.get_count_deferred = new $.Deferred();
        this.get_count_deferred.resolve(function() { return 0; });
      }
      return this.get_count_deferred;
    }

  , fetch_list : function() {
    //console.log("tree_view.fetch_list");
    var find_function;
    if (this.find_all_deferred) {
      //  Skip, because already done, e.g., display() already called
      return this.find_all_deferred;
    } /*else if (can.isFunction(this.options.find_params)) {
      this.options.list = this.options.find_params();
      this.draw_list();
    } */else {
      if(can.isEmptyObject(this.options.find_params.serialize())) {
        this.options.find_params.attr(
          "id", this.options.parent_instance ? this.options.parent_instance.id : undefined);
      }

      if (this.options.mapping) {
        this.find_all_deferred =
          this.options.parent_instance.get_list_loader(this.options.mapping);
      } else if (this.options.list_loader) {
        this.find_all_deferred =
          this.options.list_loader(this.options.parent_instance);
      } else {
        console.debug("Unexpected code path", this);
        /*
        if (this.options.find_function)
          find_function = this.options.find_function;
        else
          find_function = this.options.single_object ? "findOne" : "findAll";
        this.find_all_deferred =
          this.options.model[find_function](this.options.find_params.serialize());
        if (this.options.fetch_post_process)
          this.find_all_deferred =
            this.find_all_deferred.then(this.options.fetch_post_process);
        */
      }

      return this.find_all_deferred;
    }
  }

  , display_path: function(path) {
      return this.display().then(this._ifNotRemoved(function() {
        return _display_tree_subpath(this.element, path);
      }.bind(this)));
    }

  , prepare_child_options: function(v) {
    //console.log("tree_view.prepare_child_options", v);
    //  v may be any of:
    //    <model_instance>
    //    { instance: <model instance>, mappings: [...] }
    //    <TreeOptions>
    var tmp, that = this;
    if(!(v instanceof can.Observe.TreeOptions)) {
      tmp = v;
      v = new can.Observe.TreeOptions();
      v.attr("instance", tmp);
      this.options.each(function(val, k) {
        ~can.inArray(k, that.constructor.do_not_propagate) || v.attr(k, val);
      });
    }
    if (!(v.instance instanceof can.Model)) {
      if (v.instance.instance instanceof can.Model) {
        v.attr("result", v.instance);
        v.attr("mappings", v.instance.mappings_compute());
        v.attr("instance", v.instance.instance);
      } else {
        v.attr("instance", this.options.model.model(v.instance));
      }
    }
    v.attr("child_count", can.compute(function() {
      var total_children = 0;
      if (v.attr("child_options")) {
        can.each(v.attr("child_options"), function(child_options) {
          var list = child_options.attr("list");
          if (list)
            total_children = total_children + list.attr('length');
        });
      }
      return total_children;
    }));
    //console.log("tree_view.prepare_child_options", v);
    return v;
  }

  , "{scroll_element} scroll": function (el, ev) {
    console.log("scroll event");

  }
  , "{scroll_element} optimizedScroll": function (el, ev) {
    console.log("optimizedScroll");
  }
  , "{original_list} add" : function(list, ev, newVals, index) {
    //console.log("tree_view.{original_list} add");
    var that = this
      , real_add = []
      ;

    can.each(newVals, function(newVal) {
      var _newVal = newVal.instance ? newVal.instance : newVal;
      if (that.oldList && ~can.inArray(_newVal, that.oldList)) {
        that.oldList.splice(can.inArray(_newVal, that.oldList), 1);
      }
      else {
        that.element && real_add.push(newVal);
      }
    });
    this.enqueue_items(real_add);
  }

  , "{original_list} remove" : function (list, ev, oldVals, index) {
    var remove_marker = {}; // Empty object used as unique marker

    //  FIXME: This assumes we're replacing the entire list, and corrects for
    //    instances being removed and immediately re-added.  This should be
    //    changed to support exact mirroring of the order of
    //    `this.options.list`.
    if (!this.oldList) {
      this.oldList = [];
    }
    this.oldList.push.apply(
        this.oldList,
        can.map(oldVals, function (v) { return v.instance ? v.instance : v; }));

    // `remove_marker` is to ensure that removals are not attempted until 20ms
    //   after the *last* removal (e.g. for a series of removals)
    this._remove_marker = remove_marker;
    setTimeout(this._ifNotRemoved(function() {
      if (this._remove_marker === remove_marker) {
        can.each(this.oldList, function(v) {
          this.element.trigger("removeChild", v);
        }.bind(this));
        this.oldList = null;
        this._remove_marker = null;

        // TODO: This is a workaround. We need to update communication between
        //       info-pin and tree views through Observer
        if (!this.element.closest(".cms_controllers_info_pin").length) {
          $(".cms_controllers_info_pin").control().unsetInstance();
        }
        this.show_info_pin();
      }
    }.bind(this)), 200);
  }

  , ".tree-structure subtree_loaded" : function(el, ev) {
    ev.stopPropagation();
    var instance_id = el.closest(".tree-item").data("object-id");
    var parent = can.reduce(this.options.list, function(a, b) {
      switch(true) {
        case !!a : return a;
        case b.instance.id === instance_id: return b;
        default: return null;
      }
    }, null);
    if(parent && !parent.children_drawn) {
      parent.attr("children_drawn", true);
    }
  }

  // add child options to every item (TreeViewOptions instance) in the drawing list at this level of the tree.
  , add_child_lists : function(list) {
    var that = this
      , current_list = can.makeArray(list)
      , list_window = []
      , all_draw_items_dfds = []
      , final_dfd
      ;

    //Recursively define tree views anywhere we have subtree configs.
    function queue_window(list_window) {
      all_draw_items_dfds.push(that.draw_items(list_window));
    }

    can.each(current_list, function(item) {
      list_window.push(item);
      if (list_window.length >= 20) {
        queue_window(list_window);
        list_window = [];
      }
    });
    if (list_window.length > 0)
      queue_window(list_window);
    final_dfd = $.when.apply($, all_draw_items_dfds);
    final_dfd.done(this._ifNotRemoved(function() {
      this.element.parent().find(".sticky").Stickyfill();
    }.bind(this)));
    return final_dfd;
  }

  , draw_items : function(options_list) {
      console.log('tree_view_controller.draw_items');
      var that = this
        , $footer = this.element.children('.tree-item-add').first()
        , $items = $()
        , $existing = this.element.children('li.cms_controllers_tree_view_node')
        , draw_items_dfds = []
        , sort_prop = this.options.sort_property
        , sort_function = this.options.sort_function
        , filter = this.options.filter
        ;
      options_list = can.makeArray(options_list);
      can.map(options_list, function(options) {
        if (!filter || filter.evaluate(options.instance.get_filter_vals())) {
          var $li = $("<li />").cms_controllers_tree_view_node(options);
          draw_items_dfds.push($li.control()._draw_node_deferred);
          $items.push($li[0]);
        }
      });

    console.log("items: ", $items);
    console.log("footer: ", $footer);
    console.log("this.elements: ", this.element);


    if (sort_prop || sort_function) {
        $items.each(function(i, item) {
            var j, $item = $(item), compare;
            for(j = $existing.length - 1; j >= 0; j--) {
              var old_item = $existing.eq(j).control().options.instance,
                  new_item = $item.control().options.instance;
              if (sort_function){
                compare = sort_function(old_item, new_item);
              }
              else {
                compare = GGRC.Math.string_less_than(
                    old_item[sort_prop],
                    new_item[sort_prop]
                );
              }
              if (compare) {
                $item.insertAfter($existing.eq(j));
                $existing.splice(j + 1, 0, item);
                return;
              }
            }
            if($existing.length) {
              $item.insertBefore($existing.eq(0));
            } else if($footer.length) {
              $item.insertBefore($footer);
            } else {
              $item.appendTo(this.element);
            }
            $existing.splice(0, 0, item);
        });
        if (this.options.sortable) {
          $(this.element).sortable({element: 'li.tree-item', handle: '.drag'});
        }
      } else {
        if($footer.length) {
          $items.insertBefore($footer);
        } else {
          $items.appendTo(this.element);
        }
      }
      return $.when.apply($, draw_items_dfds);
    }

  , " sortupdate" : function(el, ev, ui) {
    var that = this,
      $item = $(ui.item),
      $before = $item.prev("li.cms_controllers_tree_view_node"),
      $after = $item.next("li.cms_controllers_tree_view_node"),
      before_index = $before.length
                     ? $before.control().options.instance[this.options.sort_property]
                     : "0",
      after_index = $after.length
                    ? $after.control().options.instance[this.options.sort_property]
                    : Number.MAX_SAFE_INTEGER.toString(10);

    ev.stopPropagation();

    if(!this.options.sort_property) {
      return;
    }

    $item.control().options.instance.refresh().then(function(inst) {
      inst.attr(
        that.options.sort_property,
        GGRC.Math.string_half(GGRC.Math.string_add(before_index, after_index))
      ).save();
    });
  }

  , " removeChild" : function(el, ev, data) {
    var that = this
      , instance
      ;

    if (data.instance && data.instance instanceof this.options.model)
      instance = data.instance;
    else
      instance = data;

    //  FIXME: This should be done using indices, when the order of elements
    //    is guaranteed to mirror the order of `this.options.list`.

    //  Replace the list with the list sans the removed instance
    that.options.list.replace(
      can.map(this.options.list, function(options, i) {
        if (options.instance !== instance)
          return options;
      }));

    //  Remove items by data attributes
    that.element.children([
        "[data-object-id=" + instance.id + "]"
      , "[data-object-type=" + instance.constructor.table_singular + "]"
      ].join("")
    ).remove();
    ev.stopPropagation();
  }

  , " updateCount": function(el, ev) {
      // Suppress events from sub-trees
      if (!($(ev.target).closest('.' + this.constructor._fullName).is(this.element)))
        ev.stopPropagation();
    }

/*  , "{list} add": function() {
      this.element.trigger('updateCount', this.options.list.length);
    }

  , "{list} remove": function() {
      this.element.trigger('updateCount', this.options.list.length);
    }
*/
  , ".edit-object modal:success" : function(el, ev, data) {
    var model = el.closest("[data-model]").data("model");
    model.attr(data[model.constructor.root_object] || data);
    ev.stopPropagation();
  },
  reload_list: function() {
    //console.log("tree_view.reload_list")
    if (this.options.list === undefined){
      return;
    }
    this._draw_list_deferred = false;
    this.find_all_deferred = false;
    this.get_count_deferred = false;
    this.options.list.replace([]);
    this.element.children('.cms_controllers_tree_view_node').remove();
    this.fetch_list().then(this.proxy("draw_list"));
    this.init_count();
  },
  "[custom-event] click" : function(el, ev) {
    console.log("tree_view.[custom-event] click");
    var event_name = el.attr("custom-event");
    if(this.options.events && typeof this.options.events[event_name] === "function") {
      this.options.events[event_name].apply(this, arguments);
    }
  }
  , hide_filter: function () {
      var $filter = this.element.parent().find(".filter-holder"),
          height = $filter.height(),
          margin = $filter.css("margin-bottom").replace("px", "");

      $filter
          .data("height", height)
          .data("margin-bottom", margin)
          .height(0)
          .css("margin-bottom", 0);

      this.element.parent().find(".filter-trigger > a")
          .removeClass("active")
          .find("i")
          .attr("data-original-title", "Show filter");

      this.element.parent().find(".sticky.tree-header").addClass("no-filter");
      Stickyfill.rebuild();


      this.display_prefs.setFilterHidden(true);
      this.display_prefs.save();
    }

  , show_filter: function () {
      var $filter = this.element.parent().find(".filter-holder");

      $filter
          .height($filter.data("height"))
          .css("margin-bottom", $filter.data("margin-bottom"));

      this.element.parent().find(".filter-trigger > a")
          .addClass("active")
          .find("i")
          .attr("data-original-title", "Hide filter");

      this.element.parent().find(".sticky.tree-header").removeClass("no-filter");
      Stickyfill.rebuild();

      this.display_prefs.setFilterHidden(false);
      this.display_prefs.save();
    }

  /* Update the tree attributes as selected by the user CORE-1546
  */
  , set_tree_attrs : function () {
    //update the display attrbute list and re-draw
    //1: find checked items
    //2. update
    var display_width = 12, attr_to_save = [],
        $check = this.element.parent().find('.attr-checkbox'),
        $selected = $check.filter(':checked'),
        selected_items=[];

    $selected.each( function(index) {
      selected_items.push(this.value);
    });

    can.each(this.options.select_attr_list, function (item) {
      item.display_status = selected_items.indexOf(item.attr_name) !== -1;
    });

    this.options.attr('select_attr_list', this.options.select_attr_list);
    this.options.display_attr_list = [];

    can.each(this.options.select_attr_list, function (item) {
      if (!item.mandatory && item.display_status) {
        this.options.display_attr_list.push(item);
      }
    }, this);
    this.options.attr('display_attr_list', this.options.display_attr_list);
    this.setup_column_width();

    this.reload_list();
    //set user preferences for next time
    can.each(this.options.display_attr_list, function (item) {
      attr_to_save.push(item.attr_name);
    });
    this.display_prefs.setTreeViewHeaders(this.options.model.model_singular, attr_to_save);
    this.display_prefs.save();

    can.bind.call(this.element.parent().find('.widget-col-title[data-field]'),
                  'click',
                  this.sort.bind(this)
                 );

  }
  , sort: function (event) {
      var $el = $(event.currentTarget),
          key = $el.data("field");

      if (key !== this.options.sort_by) {
          this.options.sort_direction = null;
      }

      var order = this.options.sort_direction === "asc"
              ? "desc"
              : "asc";

      this.options.sort_function = function (val1, val2) {
        var a = val1.get_deep_property(key),
            b = val2.get_deep_property(key);

        if (a !== b){
          return (a < b) ^ (order !== 'asc');
        }
        return false;
      };

      this.options.sort_direction = order;
      this.options.sort_by = key;

      $el.closest(".tree-header")
          .find(".widget-col-title")
          .removeClass("asc")
          .removeClass("desc");

      $el.addClass(order);

      this.reload_list();
    }
});

can.Control("CMS.Controllers.TreeViewNode", {
  defaults : {
    model : null
    , parent : null
    , instance : null
    , options_property : "tree_view_options"
    , show_view : null
    , expanded : false
    , draw_children : true
    , child_options : []
  }
}, {
  setup : function(el, opts) {
    var that = this;
    typeof this._super === "function" && this._super.apply(this, [el]);
    if(opts instanceof can.Observe) {

      this.options = opts;
      if (typeof(this.options.model) === "string")
        this.options.attr("model", CMS.Models[this.options.model]);
      // if(this.options.model) {
      //   can.each(this.options.model[opts.options_property || this.constructor.defaults.options_property], function(v, k) {
      //     that.options.hasOwnProperty(k) || that.options.attr(k, v);
      //   });
      // }
      can.each(this.constructor.defaults, function(v, k) {
        that.options.hasOwnProperty(k) || that.options.attr(k, v);
      });
    } else {
      if (typeof(opts.model) === "string")
        opts.model = CMS.Models[opts.model];
      this.options = new can.Observe.TreeOptions(this.constructor.defaults)
      .attr(opts.model ? opts.model[opts.options_property || this.constructor.defaults.options_property] : {})
      .attr(opts);
    }
  }
  , init : function(el, opts) {
    console.log("tree view node init", this);
    var that = this;
    if(that.options.instance && !that.options.show_view) {
      that.options.show_view =
        that.options.instance.constructor[that.options.options_property].show_view
        || that.options.model[that.options.options_property].show_view
        || GGRC.mustache_path + "/base_objects/tree.mustache";
    }
    console.log("pre");
    //setTimeout(this._ifNotRemoved(this.proxy("draw_node")), 20);
    //setTimeout(this._ifNotRemoved(this.proxy("draw_placeholder")), 20);
    //setTimeout(this._ifNotRemoved(this.proxy("draw_placeholder")), 0);
    this._draw_node_deferred = new $.Deferred();
    //this.proxy("draw_placeholder");
    this.draw_placeholder();
    console.log("post")

  }

  , draw_node: function() {
    console.log("tree_view.draw_node", this);
    this.add_child_lists_to_child();
    //setTimeout(function() {
      var that = this;
      can.view(that.options.show_view, that.options, this._ifNotRemoved(function(frag) {
        that.replace_element(frag);
        that._draw_node_deferred.resolve();
      }));
    //}, 20);
  }
  , draw_placeholder: function() {
      console.log("tree_view_node.draw_placeholder");
      var that = this;
      console.log("TreeViewNode.draw_placeholder", that);
      can.view(GGRC.mustache_path + "/base_objects/tree_placeholder.mustache", that.options, this._ifNotRemoved(function(frag) {
        that.replace_element(frag);
        that._draw_node_deferred.resolve();
      }));
  }
  , should_draw_children : function(){
    var draw_children = this.options.draw_children;
    if(can.isFunction(draw_children))
      return draw_children.apply(this.options);
    return draw_children;
  }
  // add all child options to one TreeViewOptions object
  , add_child_lists_to_child : function() {
    //console.log("tree_view.add_child_lists_to_child");
    var that = this
      , original_child_options = this.options.child_options
      , new_child_options = [];

    this.options.attr("child_options", new can.Observe.List());

    if (original_child_options.length == null) {
      original_child_options = [original_child_options];
    }

    if(this.should_draw_children()) {
      can.each(original_child_options, function(data, i) {
        var options = new can.Observe();
        data.each(function(v, k) {
          options.attr(k, v);
        });
        this.add_child_list(this.options, options);
        options.attr({
            "options_property": this.options.options_property
          , "single_object": false
          , "parent": this
          , "parent_instance": this.options.instance
        });
        new_child_options.push(options);
      }.bind(this));

      this.options.attr("child_options", new_child_options);
    }
  }

  // data is an entry from child options.  if child options is an array, run once for each.
  , add_child_list : function(item, data) {
    //console.log("tree_view.add_child_list", item, data);
    //var $subtree = $("<ul class='tree-structure'>").appendTo(el);
    //var model = $(el).closest("[data-model]").data("model");
    data.attr({ start_expanded : false });
    var find_params;
    if(can.isFunction(item.instance[data.property])) {
      // Special case for handling mappings which are functions until
      // first requested, then set their name via .attr('...')
      find_params = function() {
        return item.instance[data.property]();
      };
      data.attr("find_params", find_params);
    } else if(data.property) {
      find_params = item.instance[data.property];
      if(find_params && find_params.isComputed) {
        data.attr("original_list", find_params);
        find_params = find_params();
      } else if(find_params && find_params.length) {
        data.attr("original_list", find_params);
        find_params = find_params.slice(0);
      }
      data.attr("list", find_params);
    } else {
      find_params = data.attr("find_params");
      if(find_params) {
        find_params = find_params.serialize();
      } else {
        find_params = {};
      }
      if(data.parent_find_param){
        find_params[data.parent_find_param] = item.instance.id;
      } else {
        find_params["parent.id"] = item.instance.id;
      }
      data.attr("find_params", new can.Observe(find_params));
    }
    // $subtree.cms_controllers_tree_view(opts);
  }

  , replace_element : function(el) {
    console.log("tree_view.replace_element");
    var old_el = this.element
      , $el
      , old_data
      , i
      , firstchild
      ;

    if (!this.element)
      return;

    $el = $(el);
    old_data = $.extend({}, old_el.data());

    firstchild = $(_firstElementChild(el));

    old_data.controls = old_data.controls.slice(0);
    old_el.data("controls", []);
    this.off();
    old_el.replaceWith(el);
    this.element = firstchild.addClass(this.constructor._fullName).data(old_data);
    this.on();
  }

  , display: function() {
      return this.trigger_expand();
    }

  , display_path: function(path) {
      return this.display().then(this._ifNotRemoved(function() {
        return _display_tree_subpath(this.element, path);
      }.bind(this)));
    }

  , display_subtrees: function() {
      var child_tree_dfds = []
        , that = this
        ;

      this.element.find('.' + CMS.Controllers.TreeView._fullName).each(function(_, el) {
        var $el = $(el)
          , child_tree_control
          ;

        //  Ensure this targets only direct child trees, not sub-tree trees
        if ($el.closest('.' + that.constructor._fullName).is(that.element)) {
          child_tree_control = $el.control();
          if (child_tree_control)
            child_tree_dfds.push(child_tree_control.display());
        }
      });

      return $.when.apply($, child_tree_dfds);
    }

  , expand: function() {
      if (this._expand_deferred) {
        //  If we've already expanded, then short-circuit the call.  However,
        //  we still need to toggle `expanded`, but if it's the first time
        //  expanding, `this.add_child_lists_to_child` *must* be called first.
        this.options.attr("expanded", true);
        return this._expand_deferred;
      }

      var that = this
        , $openclose = this.element.find(".openclose").first();

      this.options.attr("expanded", true);

      this._expand_deferred = new $.Deferred();
      setTimeout(this._ifNotRemoved(function() {
        that.display_subtrees().then(that._ifNotRemoved(function() {
          that.element.trigger("subtree_loaded");
          that.element.trigger("loaded");
          that._expand_deferred.resolve();
        }));
      }), 5);
      return this._expand_deferred;
    }
  , ".openclose:not(.active) click" : function(el, ev) {
    // Ignore unless it's a direct child
    if (el.closest('.' + this.constructor._fullName).is(this.element))
      this.expand();
  }
  , ".select:not(.disabled) click": function(el, ev) {
    var tree = el.closest('.cms_controllers_tree_view_node'),
        node = tree.control();

    node.select();
  }
  , select: function () {
    var $tree = this.element;

    $tree.closest('section').find('.cms_controllers_tree_view_node').removeClass('active');
    $tree.addClass('active');

    this.update_hash_fragment();
    $('.pin-content').control().setInstance(this.options.instance, $tree);
  }

  , "input,select click" : function(el, ev) {
    // Don't toggle accordion when clicking on input/select fields
    ev.stopPropagation();
  }

  , trigger_expand: function() {
      var $expand_el = this.element.find(".openclose").first();
      if (!$expand_el.hasClass("active"))
        $expand_el.trigger("click");
      return this.expand();
    }

  , hash_fragment: function () {
    var parent_fragment = "";

    if (this.options.parent) {
      parent_fragment = this.options.parent.hash_fragment();
    }

    return [parent_fragment,
            this.options.instance.hash_fragment()].join("/");
  }

  , update_hash_fragment: function () {
    var hash = window.location.hash.split("/")[0];

    window.location.hash = [hash,
                            this.hash_fragment()].join('');
  }
});

(function (can, $) {
    can.Component.extend ({
    tag: 'tree-header-selector',
    // <content> in a component template will be replaced with whatever is contained
    //  within the component tag.  Since the views for the original uses of these components
    //  were already created with content, we just used <content> instead of making
    //  new view template files.
    template: '<content/>',
    scope: {
      instance: null
    },
    events: {
      init: function () {
        this.scope.attr('controller', this);
      },

      disable_attrs: function (el, ev) {
        var MAX_ATTR = 5,
            $check = this.element.find('.attr-checkbox'),
            $mandatory = $check.filter('.mandatory'),
            $selected = $check.filter(':checked'),
            $not_selected = $check.not(':checked');

        if ($selected.length === MAX_ATTR) {
          $not_selected.prop('disabled', true).
            closest('li').addClass('disabled');
        } else {
          $check.prop('disabled', false)
            .closest('li').removeClass('disabled');
          //Make sure mandatory items are always disabled
          $mandatory.prop('disabled', true)
            .closest('li').addClass('disabled');
        }
      },

      'input.attr-checkbox click' : function (el, ev) {
        this.disable_attrs(el, ev);
        ev.stopPropagation();
      },

      '.dropdown-menu-form click' : function (el, ev) {
        ev.stopPropagation();
      },

      '.tview-dropdown-toggle click' : function (el, ev) {
        this.disable_attrs(el, ev);
      },

      '.set-tree-attrs,.close-dropdown click' : function(el, ev) {
        this.element.find('.dropdown-menu').closest('li').removeClass('open');
      }
    }
  });
})(this.can, this.can.$);
