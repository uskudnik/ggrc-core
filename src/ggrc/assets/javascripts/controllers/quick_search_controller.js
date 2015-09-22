/*!
    Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
    Created By: brad@reciprocitylabs.com
    Maintained By: brad@reciprocitylabs.com
*/

//require can.jquery-all

(function(can, $, Mousetrap) {
  function with_params(href, params) {
    if (href.charAt(href.length - 1) === '?')
      return href + params;
    else if (href.indexOf('?') > 0)
      return href + '&' + params;
    else
      return href + '?' + params;
  }

  function get_attr(el, attrnames) {
    var attrval = null
    , $el = $(el);
    can.each(can.makeArray(attrnames), function(attrname) {
      var a = $el.attr(attrname);
      if(a) {
        attrval = a;
        return false;
      }
    });
    return attrval;
  }

CMS.Controllers.Filterable("CMS.Controllers.QuickSearch", {
  defaults : {
    list_view : GGRC.mustache_path + "/dashboard/object_list.mustache"
    , spin : true
    , tab_selector : 'ul.nav-tabs:first > li > a'
    , tab_href_attr : [ "href", "data-tab-href" ]
    , tab_target_attr : [ "data-tab-target", "href" ]
    , tab_model_attr : [ "data-model", "data-object-singular" ]
    , limit : null
  }
}, {

  setup : function(el, opts) {
    this._super && this._super.apply(this, arguments);
    if(!opts.observer) {
      opts.observer = new can.Observe();
    }
  }

  , init : function(opts) {
    var that = this;
    var $tabs = this.element.find(this.options.tab_selector);
    $tabs.each(function(i, tab) {
      var $tab = $(tab)
      , href = get_attr($tab, that.options.tab_href_attr)
      , loaded = $tab.data('tab-loaded')
      , pane = get_attr($tab, that.options.tab_target_attr)
      , $pane = $(pane)
      , template = $tab.data("template") || that.options.list_view
      , model_name = get_attr($tab, that.options.tab_model_attr)
      , model = can.getObject("CMS.Models." + model_name) || can.getObject("GGRC.Models." + model_name)
      , view_data = null
      , xhrs = {};

      if(!template && typeof console !== "undefined") {
        console.warn("No template defined for quick_search in ", $pane.attr("id"));
      }

      if(model && template) {
        view_data = new can.Observe({
          list: new model.List()
          , all_items: new model.List()
          , filtered_items: new model.List()
          , observer: that.options.observer
          , model : model
        });

        $tab.data("view_data", view_data);
        $tab.data("model", model);
        $pane.trigger("loading");
        model.findAll().done(function(data) {
          view_data.attr('all_items', data);
          view_data.attr('filtered_items', data.slice(0));
          if($tab.is("li.active a")) {
            can.Observe.startBatch();
            if(that.options.limit != null) {
              view_data.attr('list').replace(data.slice(0, that.options.limit));
            } else {
              view_data.attr('list', data);
            }
            can.Observe.stopBatch();
            $pane.trigger("loaded", xhrs[$pane.attr("id")], $tab.data("list"));
          } else {
            GGRC.queue_event(function() {
              if(that.options.limit != null) {
                view_data.attr('list').replace(data.slice(0, that.options.limit));
              } else {
                view_data.attr('list', data);
              }
              $pane.trigger("loaded", xhrs[$pane.attr("id")], $tab.data("list"));
            });
          }
          $tab.find(".item-count").html(data ? data.length : 0);
        });

        model.bind("created", function(ev, instance) {
          if(instance.constructor === model) {
            view_data.list.unshift(instance.serialize());
          }
        });
      }

      if(that.options.spin) {
        // Scroll up so spinner doesn't get pushed out of visibility
        $pane.scrollTop(0);
      }

      if (view_data) {
        can.view(template, view_data, function(frag, xhr) {
          $tab.data('tab-loaded', true);
          $pane.html(frag);
          xhrs[$pane.attr("id")] = xhr;
        });
      }
    });
  }

  , "{observer} value" : function(el, ev, newval) {
    this.filter(newval);
    this.element.trigger('kill-all-popovers');
  }

  , "{observer} my_work" : function(el, ev, newval) {
    this.filter(null, newval ? { "contact_id": GGRC.current_user.id } : null);
    this.element.trigger('kill-all-popovers');
  }

  // @override
  , redo_last_filter : function(id_to_add) {
    var that = this;
    var $tabs = $(this.element).find(this.options.tab_selector);
    var old_sel = this.options.filterable_items_selector;
    var old_ids = this.last_filter_ids;

    $tabs.each(function(i, tab) {
      var $tab = $(tab)
      , model = $tab.data("model")
      , res = old_ids ? that.last_filter.getResultsFor(model) : null
      , view_data = $tab.data("view_data");

      //that.options.filterable_items_selector = $(get_attr($tab, that.options.tab_href_attr)).find("li:not(.view-more, .add-new)");
      that.last_filter_ids = res = res ? can.unique(can.map(res, function(v) { return v.id; })) : null; //null is the show-all case
      if(res) {
        view_data.filtered_items.replace(can.map(view_data.all_items, function(item) { return ~can.inArray(item.id, res) ? item : undefined; }));
      } else {
        view_data.filtered_items.replace(view_data.all_items.slice(0));
      }
      view_data.list.replace(that.options.limit ? view_data.filtered_items.slice(0, that.options.limit) : view_data.filtered_items);

      //that._super();
      // res = can.map(res, function(obj, i) {
      //   var m = new model(obj);
      //   if(!m.selfLink) {
      //     m.refresh();
      //   }
      //   return m;
      // });
      $tab.find(".item-count").html(res ? res.length : $tab.data("view_data").filtered_items.length);
    });
  }

  , ".tabbable loaded" : function(el, ev) {
    $(el).scrollTop(0);
  }

  , ".nav-tabs li click" : function(el, ev) {
    var plural = el.children("a").attr("data-object-plural");
    var singular = can.map(window.cms_singularize(plural).split("_"), can.capitalize).join(" ");
    el.closest(".widget").find(".object-type").text(singular)
      .closest("a").attr("data-object-plural", plural.split(" ").join("_").toLowerCase())
      .attr("data-object-singular", singular.replace(" ", ""));
  }
});

can.Control("CMS.Controllers.LHN", {
    defaults: {
    }
}, {
    init: function() {
      var self = this
        ;

      this.obs = new can.Observe();

      this.init_lhn();

      // Set up a scroll handler to capture the current scroll-Y position on the
      // whole LHN search panel.  scroll events do not bubble, so this cannot be
      // set as a delegate on the controller element.
      self.lhs_holder_onscroll = _.debounce(function() {
        self.options.display_prefs.setLHNState({ "panel_scroll" : this.scrollTop });
      }, 250);
      this.element.find(".lhs-holder").on("scroll", self.lhs_holder_onscroll);
    }

  , is_lhn_open: function () {
      var _is_open = this.options.display_prefs.getLHNState().is_open;

      if (typeof _is_open === "undefined") {
          return false;
      }

      return _is_open;
  }

  , "input.widgetsearch keypress": function(el, ev) {
      var value;
      if (ev.which === 13) {
        ev.preventDefault();

        value = $(ev.target).val();
        this.do_search(value);
        this.toggle_filter_active();
      }
    }

  , "submit": function (el, ev) {
      ev.preventDefault();

      var value = $(ev.target).find("input.widgetsearch").val();
      this.do_search(value);
      this.toggle_filter_active();
  }

  , toggle_filter_active: function () {
      // Set active state to search field if the input is not empty:
      var $filter = this.element.find('.widgetsearch'),
          $button = this.element.find('.widgetsearch-submit'),
          $off = this.element.find('.filter-off'),
          $search_title = this.element.find(".search-title"),
          got_filter = !!$filter.val().trim().length;

      $filter.toggleClass("active", got_filter);
      $button.toggleClass("active", got_filter);
      $off.toggleClass("active", got_filter);
      $search_title.toggleClass("active", got_filter);
  }

  , ".filter-off a click": function (el, ev) {
    ev.preventDefault();

    this.element.find('.widgetsearch').val('');
    this.do_search('');
    this.toggle_filter_active();
  }

  , "a[data-name='work_type'] click": function(el, ev) {
      var target = $(ev.target),
          checked;

      checked = target.data('value') === 'my_work';
      this.obs.attr("my_work", checked);
        //target.closest('.btn')[checked ? 'addClass' : 'removeClass']('btn-success');
      this.options.display_prefs.setLHNState("my_work", checked);
      this.set_active_tab(checked);
    }

  , toggle_lhn: function (ev) {
      ev && ev.preventDefault();
      var is_open = this.is_lhn_open();

      if (is_open) {
          this.close_lhn();
      } else {
          this.open_lhn();
      }
  }

  , close_lhn: function () {
      if (this.options.display_prefs.getLHNState().is_pinned) {
        return;
      }

      // not nested
      $(".lhn-trigger").removeClass("active");

      var _width = this.options.display_prefs.getLHNavSize(null, null).lhs,
          width = _width || this.element.find(".lhs-holder").width(),
          safety = 20;

      this.element.find(".lhs-holder")
          .removeClass("active")
          .css("left", (-width-safety)+"px");

      this.element.find(".lhn-type")
          .removeClass("active")
          .css("left", (-width-safety)+"px");

      this.element.find(".bar-v")
          .removeClass("active");

      this.element.find(".lhs-search")
          .removeClass("active");

      this.options.display_prefs.setLHNState({is_open: false});
   }

  , open_lhn: function () {
      this.set_active_tab();

      // not nested
      $(".lhn-trigger").removeClass('hide').addClass("active");

      this.element.find(".lhs-holder")
          .css("left", "")
          .addClass("active");

      this.element.find(".lhn-type")
          .css("left", "")
          .addClass("active");

      this.element.find(".bar-v")
          .addClass("active");

      this.element.find(".lhs-search")
          .addClass("active");

      this.options.display_prefs.setLHNState({is_open: true});
  }

  , set_active_tab: function (newval) {
    newval || (newval = this.obs.attr("my_work"));

    var value = ["all", "my_work"][Number(newval)];
    $("a[data-name='work_type']").removeClass("active");
    $("a[data-name='work_type'][data-value='"+value+"'").addClass("active");
  }

  , init_lhn: function() {
      CMS.Models.DisplayPrefs.getSingleton().done(function(prefs) {
        var $lhs = $("#lhs"),
            lhn_search_dfd,
            my_work_tab = false;

        this.options.display_prefs = prefs;

        if (typeof prefs.getLHNState().my_work !== "undefined") {
          my_work_tab = !!prefs.getLHNState().my_work;
        }
        this.obs.attr("my_work", my_work_tab);

        lhn_search_dfd = $lhs
          .cms_controllers_lhn_search({
            observer: this.obs,
            display_prefs: prefs
          })
          .control('lhn_search')
          .display();

        $lhs.cms_controllers_lhn_tooltips();

        // Delay LHN initializations until after LHN is rendered
        lhn_search_dfd.then(function() {
          var checked = this.obs.attr('my_work'),
              value = checked ? "my_work" : "all",
              target = this.element.find('#lhs input.my-work[value='+value+']');

          target.prop('checked', true);
          target.closest('.btn')[checked ? 'addClass' : 'removeClass']('btn-success');

          // When first loading up, wait for the list in the open section to be loaded (if there is an open section), then
          //  scroll the LHN panel down to the saved scroll-Y position.  Scrolling the
          //  open section is handled in the LHN Search controller.

          if(this.options.display_prefs.getLHNState().open_category) {
            this.element.one("list_displayed", this.initial_scroll.bind(this));
          } else {
            this.initial_scroll();
          }

          this.toggle_filter_active();

          if (this.options.display_prefs.getLHNState().is_pinned) {
            this.pin();
          }
        }.bind(this));

        this.initial_lhn_render();
      }.bind(this));
    }
  , initial_scroll: function () {
    this.element.find(".lhs-holder").scrollTop(
        this.options.display_prefs.getLHNState().panel_scroll
        || 0
    );
  }
  // this uses polling to make sure LHN is there
  // requestAnimationFrame takes browser render optimizations into account
  // it ain't pretty, but it works
  , initial_lhn_render: function (try_count) {
    if (!$(".lhs-holder").size() || !$(".lhn-trigger").size()) {
      window.requestAnimationFrame(this.initial_lhn_render.bind(this));
      return;
    }

    // this is ugly, but the trigger doesn't nest inside our top element
    $(".lhn-trigger").on("click", this.toggle_lhn.bind(this));
    Mousetrap.bind("alt+m", this.toggle_lhn.bind(this));

    this.resize_lhn();

    if (this.options.display_prefs.getLHNState().is_pinned) {
      this.open_lhn();
    }else{
      this.close_lhn();
    }
  }
  , lhn_width : function(){
    return $(".lhs-holder").width()+8;
  }
  , hide_lhn: function() {
    //UI-revamp
    //Here we should hide the button ||| also
      var $area = $(".area")
        , $lhsHolder = $(".lhs-holder")
        , $bar = $('.bar-v')
        , $lhnTrigger = $(".lhn-trigger")
        ;

      this.element.hide();
      $lhsHolder.css("width", 0);
      $area.css("margin-left", 0);
      $bar.hide();
      $lhnTrigger.hide();
      $lhnTrigger.addClass('hide')

      window.resize_areas();
    }

  , do_search: function (value) {
    var $search_title = this.element.find(".search-title");
    value = $.trim(value);
    if (this._value === value) {
      return;
    }
    $search_title.addClass("active");
    this.obs.attr("value", value);
    this.options.display_prefs.setLHNState("search_text", value);
    this._value = value;
  }

  , mousedown : false
  , dragged : false
  , resize_lhn : function(resize, no_trigger){
    resize || (resize = this.options.display_prefs && this.options.display_prefs.getLHNavSize(null, null).lhs);

    var max_width = window.innerWidth*.75,
        default_size = 240;

    if (resize < default_size) {
      resize = default_size;
    }
    resize = Math.min(resize, max_width);

    this.element.find(".lhs-holder").width(resize);

    if (resize) {
      this.options.display_prefs.setLHNavSize(null, "lhs", resize);
    }

    if (!no_trigger) {
      $(window).trigger("resize");
    }
  }
  , ".bar-v mousedown" : function(el, ev) {
    var $target = $(ev.target);
    this.mousedown = true;
    this.dragged = false;
  }
  , "{window} mousemove" : function(el, ev){
    if(!this.mousedown){
      return;
    }

    ev.preventDefault();
    this.dragged = true;

    if (!this.element.find(".bar-v").hasClass("disabled")) {
      this.resize_lhn(ev.pageX);
    }
  }
  , "{window} mouseup" : function(el, ev){
    var self = this;
    if(!this.mousedown) return;

    this.mousedown = false;
  }
  , "{window} resize" : function(el, ev) {
    this.resize_lhn(null, true); // takes care of height and min/max width
  }
  , "{window} mousedown": function (el, event) {
    var x = event.pageX,
        y = event.pageY;

    if (x === undefined || y === undefined) {
      return;
    }

    var on_lhn = [".lhn-trigger:visible", ".lhn-type:visible", ".lhs-holder:visible"]
            .reduce(function (yes, selector) {
                var $selector = $(selector),
                    bounds;

                if (!$selector.length) {
                  return;
                }

                bounds = $selector[0].getBoundingClientRect();

                return yes
                    || x >= bounds.left
                    && x <= bounds.right
                    && y >= bounds.top
                    && y <= bounds.bottom;
            }, false);

    // #extended-info - makes sure that menu doesn't close if tooltip is open and user has clicked inside
    // We should handle this form some manager, and avoid having God object
    if (!on_lhn && this.options.display_prefs && !this.options.display_prefs.getLHNState().is_pinned &&
        !$('#extended-info').hasClass('in')) {
      this.close_lhn();
    }
  }

  , destroy : function() {
    this.element.find(".lhs-holder").off("scroll", self.lhs_holder_onscroll);
    this._super && this._super.apply(this, arguments);
  }

  , ".lhn-pin click": function (element, event) {
    if (this.options.display_prefs.getLHNState().is_pinned) {
      this.unpin();
    }else{
      this.pin();
    }
  }

  , unpin: function () {
    this.element.find(".lhn-pin").removeClass("active");
    this.element.find(".bar-v").removeClass("disabled");
    this.options.display_prefs.setLHNState("is_pinned", false);
  }

  , pin: function () {
    this.element.find(".lhn-pin").addClass("active");
    this.element.find(".bar-v").addClass("disabled");
    this.options.display_prefs.setLHNState("is_pinned", true);
  }
});


can.Control("CMS.Controllers.InfiniteScroll", {
    defaults: {
    }
}, {
    init: function() {
    }

  , " DOMMouseScroll": "prevent_overscroll"
  , " mousewheel": "prevent_overscroll"
  , " scroll": "prevent_overscroll"

  , prevent_overscroll: function($el, ev) {
      // Based on Troy Alford's response on StackOverflow:
      //   http://stackoverflow.com/a/16324762
      var scrollTop = $el[0].scrollTop
        , scrollHeight = $el[0].scrollHeight
        , height = $el.height()
        , scrollTopMax = scrollHeight - height
        , delta
        , up
        , loadTriggerOffset = 50
        ;

      if (ev.type === "DOMMouseScroll")
        delta = ev.originalEvent.detail * -40;
      else
        delta = ev.originalEvent.wheelDelta;

      up = delta > 0;

      var prevent = function() {
        ev.stopPropagation();
        ev.preventDefault();
        ev.returnValue = false;
        return false;
      }

      if (ev.type === "scroll" &&
          scrollTop > scrollTopMax - loadTriggerOffset) {
        this.show_more($el);
        return prevent();
      } else if (!up && scrollTop - delta > scrollTopMax) {
        // Scrolling down, but this will take us past the bottom.
        $el.scrollTop(scrollHeight);
        this.show_more($el);
        return prevent();
      } else if (up && delta > scrollTop) {
        // Scrolling up, but this will take us past the top.
        $el.scrollTop(0);
        return prevent();
      } else if (!up && scrollTop - delta > scrollTopMax - loadTriggerOffset) {
        // Scrolling down, close to bottom, so start loading more
        this.show_more($el);
      }
    }

  , show_more: function($el) {
      this.element.trigger("scrollNext");
    }
});


can.Control("CMS.Controllers.LHN_Search", {
    defaults : {
        list_view : GGRC.mustache_path + "/base_objects/search_result.mustache"
      , actions_view : GGRC.mustache_path + "/base_objects/search_actions.mustache"
      , list_selector: 'ul.top-level > li, ul.mid-level > li'
      , list_toggle_selector: 'li > a.list-toggle'
      , model_attr_selector: null
      , model_attr: 'data-model-name'
      , model_extra_attr: 'data-model-extra'
      , count_selector: '.item-count'
      , list_mid_level_selector: 'ul.mid-level'
      , list_content_selector: 'ul.sub-level'
      , actions_content_selector: 'ul.sub-actions'
      , limit : 50
      , observer : null
      , filter_params: new can.Observe()
      , counts : new can.Observe()
    }
}, {
    display: function() {
      var self = this
        , prefs = this.options.display_prefs
        , prefs_dfd
        , template_path = GGRC.mustache_path + this.element.data('template')
        ;

      prefs_dfd = CMS.Models.DisplayPrefs.getSingleton();

      // 2-way binding is set up in the view using can-value, directly connecting the
      //  search box and the display prefs to save the search value between page loads.
      //  We also listen for this value in the controller
      //  to trigger the search.
      return can.view(template_path, prefs_dfd.then(function(prefs) { return prefs.getLHNState(); })).then(function(frag, xhr) {
        var lhn_prefs = prefs.getLHNState()
          , initial_term
          , initial_params = {}
          , saved_filters = prefs.getLHNState().filter_params
          ;

        self.element.html(frag);
        self.post_init();
        self.element.find(".sub-level")
          .cms_controllers_infinite_scroll()
          .on("scroll", _.debounce(function() {
            self.options.display_prefs.setLHNState("category_scroll", this.scrollTop);
          }, 250));

        initial_term = self.options.display_prefs.getLHNState().search_text || "";
        if (self.options.observer.my_work) {
          initial_params = { "contact_id": GGRC.current_user.id };
        }
        $.map(CMS.Models, function(model, name) {
          if (model.attributes && model.attributes.default_lhn_filters) {
            self.options.filter_params.attr(model.attributes.default_lhn_filters);
          }
        });
        self.options.filter_params.attr(saved_filters);
        self.options.loaded_lists = [];
        self.run_search(initial_term, initial_params);

        // Above, category scrolling is listened on to save the scroll position.  Below, on page load the
        //  open category is toggled open, and the search placed into the search box by display prefs is
        //  sent to the search service.

        if(lhn_prefs.open_category) {
          var selector = self.options.list_selector
                  .split(",")
                  .map(function(s) {
                      return s + " > a[data-object-singular=" + lhn_prefs.open_category + "]";
                  })
                  .join(",");

          self.toggle_list_visibility(
            self.element.find(selector)
          );
        }
      });
    }

  , post_init: function() {
      var self = this;
      this.init_object_lists();
      this.init_list_views();

      can.Model.Cacheable.bind("created", function(ev, instance) {

        if (instance instanceof can.Model.Join) {
          // Don't refresh LHN counts when joins are created
          return;
        }

        var visible_model_names =
              can.map(self.get_visible_lists(), self.proxy("get_list_model"))
          , model_name = instance.constructor.shortName
          ;

        if(visible_model_names.indexOf(model_name) > -1) {
          self.options.visible_lists[model_name].unshift(instance);
          self.options.results_lists[model_name].unshift(instance);
        }
        // Refresh the counts whenever the lists change
        self.refresh_counts();
      });
    }

  , "{list_toggle_selector} click": function (el, ev) {
      ev && ev.preventDefault();
      this.toggle_list_visibility(el);
  }

  , ensure_parent_open: function (el) {
      var $toggle = el.parents(this.options.list_mid_level_selector).parents("li").find("a.list-toggle.top"),
          $ul = $toggle.parent("li").find(this.options.list_mid_level_selector);

      if ($toggle.size() && !$toggle.hasClass("active")) {
          this.open_list($toggle, $ul, null, true);
      }
  }

  , toggle_list_visibility: function(el, dont_update_prefs) {
      var sub_selector = this.options.list_content_selector + ',' + this.options.actions_content_selector
        , mid_selector = this.options.list_mid_level_selector
        , $parent = el.parent("li")
        , selector
        ;

      if ($parent.find(mid_selector).size()) {
        selector = mid_selector;
      }else{
        selector = sub_selector;
      }

      var $ul = $parent.find(selector);

      // Needed because the `list_selector` selector matches the Recently Viewed
      // list, which will cause errors
      if ($ul.length < 1) {
        return;
      }

      if ($ul.is(":visible")) {
        this.close_list(el, $ul, dont_update_prefs);
      } else {
        this.open_list(el, $ul, selector, dont_update_prefs);
      }
    }

  , open_list: function (el, $ul, selector, dont_update_prefs) {
      // Use a cached max-height if one exists
      var holder = el.closest('.lhs-holder')
      , $content = $ul.filter([this.options.list_content_selector,
                               this.options.list_mid_level_selector].join(","))
      , $siblings = selector ? $ul.closest(".lhs").find(selector) : $(false)
      , extra_height = 0
      , top
      ;

      // Collapse other lists
      var $mids = $ul.closest(".lhs").find(this.options.list_mid_level_selector)
                    .not(el.parents(this.options.list_mid_level_selector))
                    .not(el.parent().find(this.options.list_mid_level_selector)),
          $non_children = $ul.closest(".lhs")
              .find([this.options.list_content_selector,
                     this.options.actions_content_selector].join(","))
              .filter(".in")
              .filter(function (i, el) {
                  return !$.contains($ul[0], el);
              });

      [$siblings, $mids, $non_children].map(function ($selection) {
          $selection.slideUp().removeClass("in");
      });

      // Expand this list
      $ul.slideDown().addClass("in");

      // Remove active classes from others
      // remove all except current element or children
      // this works because open_list is called twice if we ensure parent is open
      var $others = $ul.closest(".lhs").find(this.options.list_selector)
              .find("a.active")
              .not(el)
              .filter(function (i, el) {
                  return !$.contains($ul[0], el);
              });
      $others.removeClass("active");

      // Add active class to this list
      el.addClass("active");

      // Compute the extra height to add to the expandable height,
      // based on the size of the content that is sliding away.
      top = $content.offset().top;
      $siblings.filter(':visible').each(function() {
          var sibling_top = $(this).offset().top;
          if (sibling_top <= top) {
              extra_height += this.offsetHeight + (sibling_top < 0 ? -holder[0].scrollTop : 0);
          }
      });

      // Determine the expandable height
      this._holder_height = holder.outerHeight();
      if (!$ul.hasClass("mid-level")) {
        $content.filter(this.options.list_content_selector).css(
            'maxHeight',
            Math.max(160,
                     (this._holder_height - holder.position().top
                      + extra_height - top - 40))
        );
      }

      // Notify the display prefs that the category the user just opened is to be reopened on next page load.
      if (!dont_update_prefs) {
          this.options.display_prefs.setLHNState({ "open_category" : el.attr("data-object-singular") });
      }

      this.ensure_parent_open(el);
      this.on_show_list($ul);
  }

  , close_list: function (el, $ul, dont_update_prefs) {
      el.removeClass("active");
      $ul.slideUp().removeClass("in");
      // on closing a category, set the display prefs to reflect that there is no open category and no scroll
        //  for the next category opened.
      if (!dont_update_prefs) {
          this.options.display_prefs.setLHNState({ "open_category" : null, category_scroll : 0 });
      }
  }

  , " resize": function() {
      var $content = this.element.find([this.options.list_content_selector].join(",")).filter(':visible');


      if ($content.length) {
        var last_height = this._holder_height
          , holder = this.element.closest('.lhs-holder')
          ;
        this._holder_height = holder.outerHeight();


        $content.css(
            'maxHeight',
            Math.max(160,
                     (this._holder_height - last_height))
        );
      }
    }

  , on_show_list: function(el, ev) {
      var $list = $(el).closest(this.get_lists())
        , model_name = this.get_list_model($list)
        , tracker_stop = GGRC.Tracker.start("LHN_show_list", model_name)
        , that = this
        ;

      setTimeout(function() {
        that.refresh_visible_lists().done(tracker_stop);
      }, 20);
    }

  , "{observer} value" : function(el, ev, newval) {
      this.run_search(newval, this.current_params);
    }

  , "{observer} my_work" : function(el, ev, newval) {
    this.run_search(this.current_term, newval ? { "contact_id": GGRC.current_user.id } : null);
  }

  , ".sub-level scrollNext": "show_more"

  , show_more: function($el, ev) {
      if (this._show_more_pending)
        return;

      var that = this
        , $list = $el.closest(this.get_lists())
        , model_name = this.get_list_model($list)
        , visible_list = this.options.visible_lists[model_name]
        , results_list = this.options.results_lists[model_name]
        , refresh_queue
        , new_visible_list
        , tracker_stop = GGRC.Tracker.start("LHN", "show_more", model_name)
        ;

      if (visible_list.length >= results_list.length)
        return;

      this._show_more_pending = true;
      refresh_queue = new RefreshQueue();
      new_visible_list =
        //results_list.slice(0, visible_list.length + this.options.limit);
        results_list.slice(visible_list.length, visible_list.length + this.options.limit);

      can.each(new_visible_list, function(item) {
        refresh_queue.enqueue(item);
      });
      refresh_queue.trigger().then(function() {
        visible_list.push.apply(visible_list, new_visible_list);
        visible_list.attr('is_loading', false);
        //visible_list.replace(new_visible_list);
        delete that._show_more_pending;
      }).done(tracker_stop);
      visible_list.attr('is_loading', true);
    }

  , init_object_lists: function() {
      var self = this;
      if (!this.options.results_lists)
        this.options.results_lists = {};
      if (!this.options.visible_lists)
        this.options.visible_lists = {};

      can.each(this.get_lists(), function($list) {
        var model_name;
        $list = $($list);
        model_name = self.get_list_model($list);
        self.options.results_lists[model_name] = new can.Observe.List();
        self.options.visible_lists[model_name] = new can.Observe.List();
        self.options.visible_lists[model_name].attr('is_loading', true);
      });
    }

  , init_list_views: function() {
      var self = this;

      can.each(this.get_lists(), function($list) {
        var model_name;
        $list = $($list);
        model_name = self.get_list_model($list);

        var context = {
            model: CMS.Models[model_name]
          , filter_params: self.options.filter_params
          , list: self.options.visible_lists[model_name]
          , counts: self.options.counts
          , count: can.compute(function() {
              return self.options.results_lists[model_name].attr('length');
            })
        };

        can.view($list.data("template") || self.options.list_view, context, function(frag, xhr) {
          $list.find(self.options.list_content_selector).html(frag);

          // If this category we're rendering is the one that is open, wait for the
          //  list to finish rendering in the content pane, then set the scrolltop
          //  of the category to the stored value in display prefs.
          if(model_name === self.options.display_prefs.getLHNState().open_category) {
            $list.one("list_displayed", function() {
              $(this).find(self.options.list_content_selector).scrollTop(
                self.options.display_prefs.getLHNState().category_scroll || 0
              );
            });
          }
        });
        can.view($list.data("actions") || self.options.actions_view, context, function(frag, xhr) {
          $list.find(self.options.actions_content_selector).html(frag);
        });
      });
    }

  , get_list_model: function($list, count) {
      $list = $($list);
      if (this.options.model_attr_selector)
        $list = $list.find(this.options.model_attr_selector).first();
      if (count && $list.attr('data-count')) {
        return $list.attr('data-count');
      }
      return $list.attr(this.options.model_attr);
    }
  , get_extra_list_model: function($list) {
      $list = $($list);
      if (this.options.model_attr_selector)
        $list = $list.find(this.options.model_attr_selector).first();
      if(!$list.attr(this.options.model_extra_attr)) {
        return null;
      }
      var model = $list.attr(this.options.model_attr),
          extra = $list.attr(this.options.model_extra_attr).split(',');

      extra = $.map(extra, function(e){
        return e + "=" + model;
      }).join(',');
      return extra;
    }

  , display_counts: function(search_result) {
      var self = this;

      // Remove all current counts
      self.options.counts.each(function(val, key) {
          self.options.counts.removeAttr(key);
      });
      // Set the new counts
      self.options.counts.attr(search_result.counts);

      can.each(this.get_lists(), function($list) {
        var model_name, count;
        $list = $($list);
        model_name = self.get_list_model($list, true);
        if (model_name) {
          count = search_result.getCountFor(model_name);

          // Remove filter suffix (ie Workflow_All) from model_name before
          //  checking permissions
          model_name = model_name.split('_')[0];
          $list
            .find(self.options.count_selector)
            .text(count);
        }
      });
    }

  , display_lists: function(search_result, display_now) {
      var self = this
        , lists = this.get_visible_lists()
        , dfds = []
        , search_text = this.current_term
        , my_work = self.current_params && self.current_params.contact_id
        , extra_params = self.current_params && self.current_params.extra_params
        ;

      can.each(lists, function(list) {
        var dfd
          , $list = $(list)
          , model_name = self.get_list_model($list)
          , results = search_result.getResultsForType(model_name)
          , refresh_queue = new RefreshQueue()
          , initial_visible_list = null;
          ;

        self.options.results_lists[model_name].replace(results);
        initial_visible_list =
          self.options.results_lists[model_name].slice(0, self.options.limit);

        can.each(initial_visible_list, function(obj) {
          refresh_queue.enqueue(obj);
        });

        function finish_display(_) {
          can.Map.startBatch();
          self.options.visible_lists[model_name].attr('is_loading', false);
          self.options.visible_lists[model_name].replace(initial_visible_list);
          can.Map.stopBatch();
          setTimeout(function() {
            $list.trigger("list_displayed", model_name);
          }, 1);
        }
        dfd = refresh_queue.trigger().then(function(d) {
          new CMS.Models.LocalListCache({
            name : "search_" + model_name
            , objects : d
            , search_text : search_text
            , my_work : my_work
            , extra_params: extra_params
            , type : model_name
            , keys : ["title", "contact", "private", "viewLink"]
          }).save();
          return d;
        });
        if(display_now) {
          finish_display();
        } else {
          dfd = dfd.then(finish_display);
        }
        dfds.push(dfd);
      });

      return $.when.apply($, dfds);
    }

  , refresh_counts: function() {
      var self = this
        , search_id = this.search_id
        , models
        , extra_models;
      models = can.map(this.get_lists(), this.proxy("get_list_model"));
      extra_models = can.map(this.get_lists(), this.proxy("get_extra_list_model"));
      // Retrieve and display counts
      return GGRC.Models.Search.counts_for_types(
          this.current_term, models, this.current_params, extra_models
        ).then(function() {
          if (self.search_id === search_id) {
            return self.display_counts.apply(self, arguments);
          }
        });
    }

  , refresh_visible_lists: function() {
      var self = this
        , search_id = this.search_id
        , lists = this.get_visible_lists()
        , models = can.map(lists, this.proxy("get_list_model"))
        ;

      models = can.map(models, function(model_name) {
        if (self.options.loaded_lists.indexOf(model_name) == -1)
          return model_name;
      });

      if (models.length > 0) {
        // Register that the lists are loaded
        can.each(models, function(model_name) {
          self.options.loaded_lists.push(model_name);
        });

        $.when.apply(
          $
          , models.map(function(model_name) {
            return CMS.Models.LocalListCache.findAll({ "name" : "search_" + model_name});
          })
        ).then(function() {
          var types = {}, fake_search_result;
          can.each(can.makeArray(arguments), function(a) {
            var a = a[0];
            if (a
                && a.search_text == self.current_term
                && a.my_work == (self.current_params && self.current_params.contact_id)
                && a.extra_params == (self.current_params && self.current_params.extra_params)) {
              types[a.name] = a.objects;
            }
          });

          if (Object.keys(types).length > 0) {
            fake_search_result = {
              getResultsForType : function(type) {
                if(types["search_" + type]) {
                  return types["search_" + type];
                }
              }
            };
            return fake_search_result;
          }
        }).done(function(fake_search_result) {
          if (fake_search_result)
            self.display_lists(fake_search_result, true);
        });

        return GGRC.Models.Search.search_for_types(
            this.current_term, models, this.current_params
          ).then(function() {
            if (self.search_id === search_id) {
              return self.display_lists.apply(self, arguments);
            }
          });
      } else {
        return new $.Deferred().resolve();
      }
    }

  , run_search: function(term, extra_params) {
      var self = this
        , tracker_stop = GGRC.Tracker.start(
          "LHN_run_search",
          extra_params && extra_params.contact_id ? "MyWork" : "Normal")
        , filter_list = [];

        ;
      if (term !== this.current_term || extra_params !== this.current_params) {
        // Clear current result lists
        can.each(this.options.results_lists, function(list) {
          list.replace([]);
        });
        can.each(this.options.visible_lists, function(list) {
          list.replace([]);
          list.attr('is_loading', true);
        });
        this.options.loaded_lists = [];

        //  `search_id` exists solely to provide a simple unique value for
        //  each search to ensure results are shown for the correct search
        //  parameters (avoiding a race condition with quick search term
        //  changes)
        this.search_id = (this.search_id || 0) + 1;
        this.current_term = term;
        this.current_params = extra_params || {};

        // Construct extra_params based on filters:
        delete this.current_params.extra_params;
        this.options.display_prefs.setLHNState("filter_params",
          this.options.filter_params);
        this.options.filter_params.each(function(obj, type) {
          var properties_list = [];
          obj.each(function(v, k){
            properties_list.push(k + "=" + v);
          });
          if (properties_list.length) {
            filter_list.push(type + ":" + properties_list.join(','));
          }
        });
        this.current_params.extra_params = filter_list.join(';');

        // Retrieve and display results for visible lists
        return $.when(
            this.refresh_counts(),
            this.refresh_visible_lists()
          ).done(tracker_stop);
      }
    }

  , get_lists: function() {
      return $.makeArray(
          this.element.find(this.options.list_selector));
    }

  , get_visible_lists: function() {
      var self = this;
      return can.map(this.get_lists(), function($list) {
        $list = $($list);
        if ($list.find([self.options.list_content_selector,
                        self.options.list_mid_level_selector].join(",")).hasClass('in'))
          return $list;
      });
    },

  ".filters a click" : function(el, ev) {
    var term = this.options.display_prefs.getLHNState().search_text || "",
        param = {},
        key = el.data('key'),
        value = el.data('value'),
        for_model = el.parent().data('for'),
        filters = this.options.filter_params;
    if (this.options.observer.my_work) {
      param = { "contact_id": GGRC.current_user.id };
    }

    if (el.hasClass('active')) {
      filters[for_model].removeAttr(key);
      this.run_search(term, param);
      return;
    }
    if (!(for_model in filters)) {
      filters.attr(for_model, {});
    }
    filters[for_model].attr(key, value);
    this.run_search(term, param);
  }
});


can.Control("CMS.Controllers.LHN_Tooltips", {
    defaults : {
        tooltip_view: GGRC.mustache_path + "/base_objects/extended_info.mustache"
      , trigger_selector: ".show-extended"
      , fade_in_delay: 300
      , fade_out_delay: 300
    }
}, {
    init: function() {
      if (!this.options.$extended) {
        this.options.$extended = $('#extended-info');
        if (this.options.$extended.length < 1)
          this.options.$extended =
            $('<div id="extended-info" class="extended-info hide" />')
              .appendTo('body');
      }
      if (!this.options.$lhs)
        this.options.$lhs = $('#lhs');
      // Renew event listening, since we assigned $extended, $lhs
      this.on();
    }

  // Tooltip / popover handling
  , "{trigger_selector} mouseenter": "on_mouseenter"
  , "{trigger_selector} mouseleave": "on_mouseleave"
  , "{$extended} mouseleave": "on_mouseleave"
  , "{$extended} mouseenter": "on_tooltip_mouseenter"

  , on_mouseenter: function(el, ev) {
      var instance = el.closest("[data-model]").data("model")
                      || el.closest(":data(model)").data("model")
        , delay = this.options.fade_in_delay
        ;

      // There isn't tooltip data available for recently viewed objects
      if (instance instanceof GGRC.Models.RecentlyViewedObject)
        return;

      if (this.options.$extended.data('model') !== instance) {
        clearTimeout(this.fade_in_timeout);
        // If tooltip is already showing, show new content without delay
        if (this.options.$extended.hasClass('in'))
          delay = 0;
        this.fade_in_timeout = setTimeout(
            this.proxy('on_fade_in_timeout', el, instance), delay);
        clearTimeout(this.fade_out_timeout);
        this.fade_out_timeout = null;
      } else if (this.fade_out_timeout) {
        clearTimeout(this.fade_out_timeout);
        this.fade_out_timeout = null;
      }
    }

  , ensure_tooltip_visibility: function() {
      var offset = this.options.$extended.offset().top
        , height = this.options.$extended.height()
        // "- 24" compensates for the Chrome URL display when hovering a link
        // "348" should be the widht of the Chrome URL display when displaying javascript://
        , window_height = $(window).height() + $(window).scrollTop() -
            (this.options.$extended.offset().left > 348 ? 0 : 24)
        , new_offset
        ;

      if (offset + height > window_height) {
        if (height > window_height)
          new_offset = 0;
        else
          new_offset = window_height - height;
        this.options.$extended.css({ top: new_offset });
      }
    }

  , get_tooltip_view: function(el) {
      var tooltip_view = $(el)
            .closest('[data-tooltip-view]').attr('data-tooltip-view');
      if (tooltip_view && tooltip_view.length > 0) {
        if (tooltip_view === "null") {
          return null;
        }
        else {
          return GGRC.mustache_path + tooltip_view;
        }
      }
      else {
        return this.options.tooltip_view;
      }
    }

  , on_fade_in_timeout: function(el, instance) {
      var self = this
        , tooltip_view = this.get_tooltip_view(el)
        ;

      if (tooltip_view) {
        this.fade_in_timeout = null;
        can.view(tooltip_view, { instance: instance }, function(frag) {

          var tooltip_width = self.options.$extended.outerWidth()
            , offset = el.parent().offset()
            , el_left = offset ? offset.left : 0
            , offset_left = el_left - tooltip_width > 0 ?
                el_left - tooltip_width : el_left + el.parent().width();

          self.options.$extended
            .html(frag)
            .addClass('in')
            .removeClass('hide')
            .css({ top: el.offset().top, left: offset_left })
            .data('model', instance);
          self.ensure_tooltip_visibility();
        });
      }
    }

  , on_tooltip_mouseenter: function() {
      clearTimeout(this.fade_out_timeout);
      this.fade_out_timeout = null;
    }

  , on_fade_out_timeout: function() {
      clearTimeout(this.fade_in_timeout);
      this.fade_in_timeout = null;
      this.fade_out_timeout = null;
      this.options.$extended
        .removeClass('in')
        .addClass('hide')
        .data('model', null);
    }

  , on_mouseleave: function(el, ev) {
      // Cancel fade_in, if we haven't displayed yet
      clearTimeout(this.fade_in_timeout);
      this.fade_in_timeout = null;

      clearTimeout(this.fade_out_timeout);
      this.fade_out_timeout =
        setTimeout(
            this.proxy("on_fade_out_timeout"),
            this.options.fade_out_delay);
    }
  , destroy: function() {
    this._super();
    this.on_mouseleave();
  }
});
})(this.can, this.can.$, Mousetrap);
