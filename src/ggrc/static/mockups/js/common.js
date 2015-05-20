$(document).ready(function(){

  $('[rel=tooltip]').tooltip();

  $('.lhs-holder').css('height', $(window).height() - 71 );
  $('.inner-nav').css('height', $(window).height() - 126 );
  $('.object-area').css('height', $(window).height() - 172 );
  $('.object-area').css('width', $(window).width() - 248 );
  $('.object-area.wide').css('width', $(window).width() - 48 );

  $('input[name=notify-digest]').parent().on('click', function(ev){
    ev.stopPropagation();
  });

  $('body').on('click', '.info-expand a', function() {
    var $this = $(this),
        $show_hide = $this.closest('.row-fluid').next('.hidden-fields-area');

    if($this.hasClass("active")) {
      $show_hide.slideUp('fast');
      $this.removeClass("active");
    } else {
      $show_hide.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $('body').on('click', '.expand-link a', function() {
    var $this = $(this),
        $show_hide = $this.closest('.row-fluid').next('.hidden-fields-area');

    if($this.hasClass("active")) {
      $show_hide.slideUp('fast');
      $this.removeClass("active");
    } else {
      $show_hide.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $('body').on('click', 'ul.tree-structure .item-main .grcobject, ul.tree-structure .item-main .openclose', function(e) {
    openclose.call(this);
    e.stopPropagation();
  });
  $.fn.openclose = openclose;
  function openclose(command) {
    var $that = $(this)
    , use_slide = $that.length < 100

    $that.each(function(){
      var $this = $(this)
        , $main = $this.closest('.item-main')
        , $li = $main.closest('li')
        , $content = $li.children('.item-content')
        , $icon = $main.find('.openclose')
        , $parentTree = $this.closest('ul.new-tree')
        , cmd = command;

      if(typeof cmd !== "string" || cmd === "toggle") {
        cmd = $icon.hasClass("active") ? "close" : "open";
      }

      if (cmd === "close") {

        use_slide ? $content.slideUp(50) : $content.css("display", "none");
        $icon.removeClass('active');
        $li.removeClass('item-open');
        // Only remove tree open if there are no open siblings
        !$li.siblings('.item-open').length && $parentTree.removeClass('tree-open');
        $content.removeClass('content-open');
      } else if(cmd === "open") {
        use_slide ? $content.slideDown(50) : $content.css("display", "block");
        $icon.addClass('active');
        $li.addClass('item-open');
        $parentTree.addClass('tree-open');
        $content.addClass('content-open');
      }
    });

    return this;

  }

  $.fn.openclose = openclose;

  $('body').on('click', '.advanced-filter-trigger', function() {
    var $this = $(this),
        $filters = $this.closest('.inner-tree').find('.advanced-filters');

    if($this.hasClass("active")) {
      $filters.slideUp('fast');
      $this.removeClass("active");
      $this.html('<i class="grcicon-search"></i> Show Filters');
    } else {
      $filters.slideDown('fast');
      $this.addClass("active");
      $this.html('<i class="grcicon-search"></i> Hide Filters');
    }

    return false;

  });

  $('.autogenerate').change(function(){
    $('.autogenerate-result').toggleClass('active', $(this).val() == 'control');
  });

  $('body').on('click', '.accordion-group > a', function() {
    var $this = $(this),
        $subNav = $this.closest('.accordion-group').find('.sub-level'),
        $subAction = $this.closest('.accordion-group').find('.sub-actions');

    if($this.hasClass("active")) {
      $subNav.slideUp('fast');
      $subAction.slideUp('fast');
      $this.removeClass("active");
    } else {
      $subNav.slideDown('fast');
      $subAction.slideDown('fast');
      $this.addClass("active");
    }

    return false;

  });

  $('body').on('click', '.inner-accordion-group > a', function() {
    var $this = $(this),
        $subNav = $this.closest('.inner-accordion-group').find('.lhn-items-list'),
        $subAction = $this.closest('.inner-accordion-group').find('.lhn-items-list-actions');

    if($this.hasClass("active")) {
      $this.removeClass("active");
      $subNav.slideUp('fast');
      $subAction.slideUp('fast');
    } else {
      $this.addClass("active");
      $subNav.slideDown('fast');
      $subAction.slideDown('fast');
    }

    return false;

  });

  $('body').on('click', '.accordion-group-inner > .arrow', function() {
    var $this = $(this),
        $subNav = $this.closest('.accordion-group-inner').find('.sub-level');

    if($this.hasClass("active")) {
      $subNav.slideUp('fast');
      $this.removeClass("active");
    } else {
      $subNav.slideDown('fast');
      $this.addClass("active");
    }

    return false

  });

  $( ".date" ).datepicker();

  $(function() {
    var people = [
      "Vladan Mitevski",
      "Predrag Kanazir",
      "Dan Ring",
      "Silas Barta",
      "Cassius Clay"
    ];
    var program = [
      "Google Fiber",
      "LEED",
      "ISO 27001 Program",
      "CFR 21 Part 11",
      "HIPAA",
      "HR Program",
      "SOX Compliance Program",
      "Contract Compliance",
      "PCI Compliance Program",
    ]
    var object = [
      "Stability and Perpetuability"
    ]

    var object2 = [
      "CTRL - Access Control",
      "CTRL - Non Critical Security",
      "POL - User Policy",
      "POL - Universal Policy"
    ]

    var tasks = [
      "Proof Reading",
      "Validate Mappings",
      "Peer Review"
    ]
  });

  // New Assessment Created
  $('body').on('click', '#addAssessmentCreated', function() {
    $('#newAssessment').modal('hide');
    $('#assessmentCountObjectNav').html('2');
    $('#assessmentCountWidget').html('(2)');
    $('#mainAssessmentsCountNew').html('2');
    $('#addAssessment').fadeIn();
    $('#mainAssessmentNew').fadeIn();

  });

  // New Object under Assessment Created
  $('body').on('click', '#addObjectUnderAssessmentCreated', function() {
    $('#newObjectToAssessment').modal('hide');
    $('#objectUnderAssessmentCountObjectNav').html('5');
    $('#objectItemUnderAssessmentCountObjectNav').html('5');
    $('#addObjectUnderAssessment').fadeIn();
  });

  // Create New Task
  $('body').on('click', '#createNewTask', function() {
    $('#newTask').modal('hide');
    $('#newlyCreatedTaskTitle').html('Clean up');
    $('#newlyCreatedTask').fadeIn();
    $('#taskCounter').html('1');
  });

  // Create New File
  $('body').on('click', '#createNewFile', function() {
    $('#newFile').modal('hide');
    $('#newlyCreatedFile').fadeIn();
    $('#fileCounter').html('3');
  });

  $('body').on('click', '.show-long', function() {
    var $this = $(this),
        $description = $this.closest('.show-description').find('.tree-description');

    $this.hide();
    $description.removeClass('short');

    return false;
  });

  $('.workflow-accordion').on('show', function (e) {
    $(e.target).prev('.accordion-heading').find('.accordion-toggle').addClass('active');
  });

  $('.workflow-accordion').on('hide', function (e) {
    $(this).find('.accordion-toggle').not($(e.target)).removeClass('active');
  });

  $('#assessmentWorkflowChoose').on('change', function(){
    var id = $(this).val()
      , workflow = null;
    new Workflow.List({}).each(function(v){
      if(v.id == id){
        workflow = v;
      }
    });
    if(id == "new"){
      workflow = new Workflow({_new: true, title: "", tasks: [], reviews: []});
    }
    $("workflow-app").trigger("workflow_selected", workflow);
    $('#accordionContentReview').show();
    $('#accordionContentTasks').show();
    return;
    if($(this).val() == 'newWorkflow') {
      $('#regularWorkflowLabel').hide();
      $('#newWorkflowLabel').show();
      $('#newWorkflowTitle').show();
      $('.workflow-accordion .accordion-group .accordion-body').each(function(){
        $(this).addClass('in');
      });
      $('#accordionContentReview').show();
      $('#accordionContentTasks').show();
      $('#showTasksCount').html('3');
      $('#showReviewCount').html('2');
    } else if ($(this).val() == 'existingWorkflow') {
      $('.workflow-accordion .accordion-group .accordion-body').each(function(){
        $(this).addClass('in');
      });
      $('#accordionContentReview').show();
      $('#accordionContentTasks').show();
      $('#showTasksCount').html('3');
      $('#showReviewCount').html('2');
    } else {
      $('#regularWorkflowLabel').show();
      $('#newWorkflowLabel').hide();
      $('#newWorkflowTitle').hide();

      $('.workflow-accordion .accordion-group .accordion-body').each(function(){
        $(this).removeClass('in');
      });
      $('#accordionContentReview').hide();
      $('#accordionContentTasks').hide();
      $('#showTasksCount').html('0');
      $('#showReviewCount').html('0');
    }
  });

  $('body').on('click', '#addWorkflow', function() {
    $('#setupWorkflow').modal('hide');
    $('#workflowNotSet').hide();
    $('#workflowSet').show();
    $('#workflowTasksCount').html('3');
    $('#workflowReviewCount').html('2');
    $('#workflowTasks').show();
    $('#workflowReviews').show();
    $('#workflowFrequency').show();
    $('#workflowSetup').hide();
    $('#workflowEdit').show();
    $('#noWorkflow').hide();
  });

  $('body').on('mouseover', '.section-add', function() {
    var $this = $(this)
    ,   $sectionExpand = $this.closest('.section-expandable').find('.section-expander');

    $this.hide();
    $sectionExpand.show();
  });

  $('body').on('click', '#addSingleObjectTrigger', function() {
    $('#addSingleObject').show();
    $('#objectFooterUtility').hide();
  });

  $('body').on('click', '#addSingleControl', function() {
    $('#addSingleObject').hide();
    $('#addedObject').show();
    $('#objectsCounter').html('(5)');
    $('#objectsMainCounter').html('5');
    $('#objectFooterUtility').show();
    $('.section-expander').hide();
    $('.section-add').show();
    $('#noObjects').html('5 Objects selected').css('font-style','normal').css('color','#000');
    $('#startAssessment').removeClass('disabled');
  });

  $('body').on('click', '#cancelSingleControl', function() {
    $('#objectFooterUtility').show();
    $('#addSingleObject').hide();
    $('.section-expander').hide();
    $('.section-add').show();
  });

  $("#objectAll").click(function () {
    $(".object-check-single").prop('checked', $(this).prop('checked'));
    if($('#objectAll').attr('checked', true)) {
      $('#objectAdd').show();
    } else {
      $('#objectAdd').hide();
    }
  });

  $('body').on('click', '#objectAdd a', function() {
    $('#objectStep2').hide();
    $('#objectAdd').hide();
    $('#objectStep3').show();
    $('#objectsCounter').html('(4)');
    $('#objectsMainCounter').html('4');
  });

  $('body').on('click', '#addRule', function() {
    $('#newRule').show();
  });

  $('body').on('click', '#objectReview', function() {
    $('#objectStep1').hide();
    $('#objectStep2').show();
    $('#objectAdd').show();
  });

  $('body').on('click', '#addEntryTrigger', function() {
    $('#entryText').show();
    $(this).hide();
  });

  $('body').on('click', '#addEntryButton', function() {
    $('#newEntry').show();
    $('#addEntryTrigger').show();
    $('#entryText').hide();
    $('#entriesCount').html('2');
    $('#taskEntryCounterMain').html('1');
  });

  $('body').on('click', '#startObject', function() {
    $('#finishObject').show();
    $(this).hide();
  });

  $('body').on('click', '#startTask', function() {
    $(this).hide();
    $('#finishTask').show();
  });
  $('body').on('click', '#startTask2', function() {
    $(this).hide();
    $('#finishTask2').show();
  });
  $('body').on('click', '#startTask3', function() {
    $(this).hide();
    $('#finishTask3').show();
  });

  $('body').on('click', '#finishTask', function() {
    $('#verifyTask').show();
    $(this).hide();
  });

  $('body').on('click', '#finishTask2', function() {
    $(this).hide();
    $('#verifyTask2').show();
  });

  $('body').on('click', '#finishTaskSpecial', function() {
    $(this).hide();
    $('#verifyTaskSpecial').show();
  });

  $('body').on('click', '#finishTask3', function() {
    $(this).hide();
    $('#verifyTask3').show();
  });

  $('body').on('click', '#verifyTask', function() {
    $(this).closest('.tree-item').removeClass('rq-draft');
    $(this).closest('.tree-item').addClass('rq-accepted');
    $(this).hide();
    $('#taskDone').show();
  });

  $('body').on('click', '#verifyTask2', function() {
    $(this).closest('.tree-item').removeClass('rq-draft');
    $(this).closest('.tree-item').addClass('rq-accepted');
    $(this).hide();
    $('#taskDone2').show();
  });

  $('body').on('click', '#verifyTask3', function() {
    $(this).closest('.tree-item').removeClass('rq-draft');
    $(this).closest('.tree-item').addClass('rq-accepted');
    $(this).hide();
    $('#taskDone3').show();
  });

  $('body').on('click', '#peerReviewActive', function() {
    $(this).hide();
    $('#peerReview').show();
  });

  $('body').on('click', '#partyReviewActive', function() {
    $(this).hide();
    $('#partyReview').show();
  });

  $('body').on('click', '#peerReviewComplete', function() {
    $(this).hide();
    $('#reviewNoteDone').show();
    $('#addNote').hide();
  });

  $('body').on('click', '#partyReviewComplete', function() {
    $(this).hide();
    $('#reviewNoteDone2').show();
    $('#addNote2').hide();
    $('#finishObject').removeClass('disabled');
  });

  $('body').on('click', '#finishObject', function() {
    $(this).closest('.tree-item').removeClass('rq-amended-request').addClass('rq-accepted');
    $(this).hide();
    $('#objectMessage').show();
  });

  $('body').on('click', '#filterTrigger', function() {
    $('#objectStep2').hide();
    $('#objectStep1').show();
  });

  $('body').on('click', '#filterTriggerFooter', function() {
    $('#objectStep2').hide();
    $('#objectStep3').hide();
    $('#objectStep1').show();
  });

  $('body').on('click', '#addTaskGroup', function() {
    $('#TaskGroupItem').show();
    $('#TaskGroupCounter').html('1');
    $('#objectsMainCounter4').html('1');
    $('#workflowStart').removeClass('disabled');
  });

  $('body').on('click', '#cancelTaskGroup', function() {
    $('#addSingleObject').hide();
    $('#objectFooterUtility').show();
  });

  $('body').on('click', '#TaskDescription', function() {
    $('#TaskHolder').show();
    $('#TaskDescription').hide();
  });

  $('body').on('click', '#descriptionCancel', function() {
    $('#TaskHolder').hide();
    $('#TaskDescription').show();
  });

  $('body').on('click', '#descriptionSave', function() {
    $('#TaskHolder').hide();
    $('#TaskDescription').hide();
    $('#TaskUpdated').show();
  });

  $('body').on('click', '#objectAddTrigger', function() {
    $('#objectList').show();
    $('#objectWorkflowCounter').html('2');
  });

  $('body').on('click', '#taskAdd', function() {
    $('#taskList').show();
    $('#lockTrigger').show();
    $('#taskWorkflowCounter').html('3');
  });

  $("#taskLock").change(function () {
    if($(this).is(':checked')) {
      $('#taskAdd').addClass('disabled');
      $('.task-list .objective-selector a').addClass('disabled');
    } else {
      $('#taskAdd').removeClass('disabled');
      $('.task-list .objective-selector a').removeClass('disabled');
    }
  });

  $("body").on('change', '.object-check-single', function() {
    if($(this).is(':checked')) {
      $(this).closest('.tree-item').removeClass('disabled');
    } else {
      $(this).closest('.tree-item').addClass('disabled');
    }
  });

  $('body').on('click', '#titleChange', function() {
    $(this).closest('h3').hide();
    $('#taskGroupTitle').show();
  });

  $('body').on('click', '#editFieldSave', function() {
    $('#titleChange').closest('h3').show();
    $('#taskGroupTitle').hide();
  });

  $('body').on('click', '#editFieldCancel', function() {
    $('#titleChange').closest('h3').show();
    $('#taskGroupTitle').hide();
  });

  $('body').on('click', '#endWorkflowTrigger', function() {
    $('.internav .progress-object').addClass('finished');
    $('#endWorkflowTrigger').hide();
    $('.internav .inner-nav-button span.message').show();
    $('.header-message').show();
    $('.workflow-group').addClass('finished');
    $('.finished-number').show();
  });

  $('body').on('click', '#cancelEntry', function() {
    $('#entryText').hide();
    $('#addEntryTrigger').show();
  });

  $('body').on('click', '#editEntryTrigger', function() {
    $('#firstEntry').hide();
    $('#editEntry').show();
  });

  $('body').on('click', '#editEntrySave', function() {
    $('#firstEntry').show();
    $('#editEntry').hide();
  });

  $('body').on('click', '#editEntryCancel', function() {
    $('#firstEntry').show();
    $('#editEntry').hide();
  });

  $('#frequency').on('change', function(){
    if($(this).val() == 'one_time') {
      $('.frequency-wrap').hide();
      $('#one-time').show();
    } else if ($(this).val() == 'weekly') {
      $('.frequency-wrap').hide();
      $('#weekly').show();
    } else if ($(this).val() == 'monthly') {
      $('.frequency-wrap').hide();
      $('#monthly').show();
    } else if ($(this).val() == 'quarterly') {
      $('.frequency-wrap').hide();
      $('#quarterly').show();
    } else if ($(this).val() == 'annually') {
      $('.frequency-wrap').hide();
      $('#annually').show();
    } else if ($(this).val() == 'continuos') {
      $('.frequency-wrap').hide();
      $('#continuos').show();
    }
  });

  // Hide fields in modals
  $(".modal .field-hide").each(function() {
    var $this = $(this),
        $hideable = $(this).closest('[class*="span"].hideable'),
        $innerHide = $this.closest('[class*="span"]').find('.hideable'),
        $resetForm = $this.closest('.modal-body').find('.reset-form');

    $this.click(function() {
      $this.closest('.inner-hide').addClass('inner-hideable');
      $hideable.hide();
      $resetForm.fadeIn(500);

      for(var i=0; i < $this.closest('.hide-wrap.hideable').find('.inner-hideable').length; i++) {
        if(i == 1) {
          $this.closest('.inner-hide').parent('.hideable').hide();
        }
      };
      return false

    });

    $resetForm.click(function() {
      $this.closest('.inner-hide').removeClass('inner-hideable');
      $hideable.show();
      $('.inner-hide').parent('.hideable').show();
      $resetForm.fadeOut(500);
      return false
    });
  });

  // Custom Attribute select
  $('.if-upload').fadeOut(500);
  $('.attr-custom').change(function() {
    if (this.value == '3') {
      $('.if-dropdown').fadeIn(500);
      $('.if-checkbox').fadeOut(500);
      $('.if-upload').fadeOut(500);
    } else if (this.value == "4") {
      $('.if-dropdown').fadeOut(500);
      $('.if-checkbox').fadeOut(500);
      $('.if-upload').fadeOut(500);
    } else if (this.value == "5") {
      $('.if-dropdown').fadeOut(500);
      $('.if-checkbox').fadeOut(500);
      $('.if-upload').fadeIn(500);
    } else {
      $('.if-dropdown').fadeOut(500);
      $('.if-checkbox').fadeIn(500);
      $('.if-upload').fadeOut(500);
    }
  });

  // Add Custom Attribute
  $('body').on('click', '#addAttribute', function() {
    $("#NewAttribute").show();
    $("#customAttribute").modal('hide');
  });

  // Custom attribute disable edit link
  $(".disabled-link").on("click", function(ev) {
    ev.preventDefault();
  });

  $("#attribute-cat-trigger").on("click", function() {
    var $this = $(this);
        $activeList = $this.closest("li"),
        $list = $this.closest(".internav").find("li"),
        $activeWidget = $this.closest("body").find("#attribute_cat"),
        $widget = $this.closest("body").find(".widget");

    $widget.hide();
    $activeWidget.show();
    $list.removeClass("active");
    $activeList.addClass("active");
  });

  $("#object-attribute-trigger").on("click", function() {
    var $this = $(this);
        $activeList = $this.closest("li"),
        $list = $this.closest(".internav").find("li"),
        $activeWidget = $this.closest("body").find("#object_attribute_widget"),
        $widget = $this.closest("body").find(".widget");

    $widget.hide();
    $activeWidget.show();
    $list.removeClass("active");
    $activeList.addClass("active");
  });

  $("#addCategory").on("click", function() {
    var $this = $(this),
        $newCategory = $("#newCategory");

    $this.modal('hide');
    $newCategory.show();
  });

  // Custom Reporting
  $(".save-template input[type=checkbox]").each(function() {
    var $this = $(this),
        $label = $(this).closest("label");
    if($(this).prop('disabled')) {
      $label.addClass("disabled");
    }
  });

  $(".attribute-trigger").each(function() {
    $(".attribute-trigger").popover({
      html: true,
      trigger: "click",
      content: function(){
        return $(this).next('.attr-wrap').html();
      },
      placement: "bottom",
      template: '<div class="popover popover-medium popover-manual-close" role="tooltip"><div class="popover-content"></div></div>'
    });

    $(this).on('shown.bs.popover', function () {
      $(this).addClass("active");
      $(this).next(".popover-manual-close").find(".popover-close").click(function (e) {
          $(".attribute-trigger").popover("hide");
      });
    });

    $(this).on('hidden.bs.popover', function () {
      $(this).removeClass("active");
    });
  });

  // "Save report as" checkbox sync
  $(".report-save-check").change(function() {
    $(".report-save-check-bottom").prop("checked", this.checked);
  });

  $(".report-save-check-bottom").change(function() {
    $(".report-save-check").prop("checked", this.checked);
  });

  // Close all popovers with a class "popover-manual-close" if you click anywhere except inside popover
  $("html").on("mouseup", function(el) {
    if(!$(el.target).closest(".popover-manual-close").length) {
      $(".popover-manual-close").each(function(){
        $(this.previousSibling).popover('hide');
      });
    }
  });

  // Dropdown menu form stop propagation
  $(".dropdown-menu").on("click", function(el) {
      var $this = $(this);

    if($this.hasClass("dropdown-menu-form")) {
      el.stopPropagation();
    }
  });

  // Top navigation show/hide
  function topNav() {
    var options = {
          duration: 800,
          easing: 'easeOutExpo'
        },
        $this = $(this),
        $tooltip = $this.find("i"),
        $nav = $this.closest("body").find(".top-inner-nav"),
        $lhn_nav = $this.closest("body").find(".lhs-holder"),
        $lhn_type = $this.closest("body").find(".lhn-type"),
        $bar = $this.closest("body").find(".bar-v"),
        $content = $this.closest("body").find(".object-area"),
        $fake_merge = $content.add($bar);
    if($this.hasClass("active")) {
      $this.removeClass("active");
      $tooltip.attr("data-original-title", "Show menu");
      $nav.animate({top: "19"}, options);
      $fake_merge.animate({top: "49"}, options);
      $lhn_nav.animate({top: "99"}, options);
      $lhn_type.animate({top: "65"}, options);
    } else {
      $this.addClass("active");
      $tooltip.attr("data-original-title", "Hide menu");
      $nav.animate({top: "48"}, options);
      $fake_merge.animate({top: "78"}, options);
      $lhn_nav.animate({top: "128"}, options);
      $lhn_type.animate({top: "94"}, options);
    }
  }

  // LHN show/hide
  function lhnAnimate() {
    var options = {
          duration: 100,
          easing: 'easeOutExpo'
        },
        $this = $(this),
        $lhn = $this.closest("body").find(".lhs-holder"),
        lhn_width = $lhn.width() - 20,
        $lhn_bar = $this.closest("body").find(".bar-v"),
        $lhnType = $this.closest("body").find(".lhn-type"),
        $lhs_search = $this.closest("body").find(".lhs-search");
    if($this.hasClass("active")) {
      $this.removeClass("active");
      $lhn.removeClass("active").animate({left: "-240"}, options).css("width", "240px");
      $lhnType.removeClass("active").animate({left: "-240"}, options).css("width", "240px");
      $lhs_search.removeClass("active").css("width", "196px");
      $lhs_search.find(".widgetsearch").css("width", "130px");
    } else {
      $this.addClass("active");
      $lhn.addClass("active").animate({left: "0"}, options);
      $lhnType.addClass("active").animate({left: "0"}, options);
      $lhs_search.addClass("active");
    }
  }

  $(".nav-trigger").on("click", topNav);
  $(".lhn-trigger").on("click", lhnAnimate);

  /*
  TO-DO: when clicking everywhere else except inside lhn if lhn is active it should be closed.
  $(document).on('click', function(event) {
    if (!$(event.target).closest(".lhs-holder.active").length) {
      $(".lhs-holder").removeClass("active").animate({left: "-240"}, 800, 'easeOutExpo').css("width", "240px");
    }
  });
  */

  // top nav dropdown position
  function dropdownPosition() {
    var $this = $(this),
        $dropdown = $this.closest(".hidden-widgets-list").find(".dropdown-menu"),
        $menu_item = $dropdown.find(".inner-nav-item").find("a"),
        dropdown_height = $dropdown.outerHeight(),
        offset = $this.offset(),
        top_pos = offset.top + 36,
        left_pos = offset.left,
        win = $(window),
        win_height = win.height(),
        footer_height = $(".footer").outerHeight(),
        remain_height = win_height - footer_height,
        win_width = win.width();

    if(win_width - left_pos < 322) {
      $dropdown.addClass("right-pos");
    } else {
      $dropdown.removeClass("right-pos");
    }
    if(remain_height - top_pos < dropdown_height) {
      $dropdown.addClass("mid-pos");
    } else {
      $dropdown.removeClass("mid-pos");
    }
    if($menu_item.length === 1) {
      $dropdown.addClass("one-item");
    } else {
      $dropdown.removeClass("one-item");
    }

  }
  $(".dropdown-toggle").on("click", dropdownPosition);

  // Main title slide to right
  function slideRight() {
    var options = {
          duration: 1500,
          easing: 'easeOutExpo'
        },
        $this = $(this),
        $to_slide = $this.closest("h1").find(".title-slide"),
        $to_show = $this.closest("h1").find(".title-prev"),
        win = $(window),
        win_width = win.width(),
        slide_amount = win_width;

    $to_slide.animate({ "left": "+=" + slide_amount }, options);
  }

  $(".title-trigger").on("click", slideRight);

  $(".select").on("click", function(el) {
    var $this = $(this),
        $this_item = $this.closest(".tree-item"),
        $all_items = $(".tree-item");

    if($this_item.hasClass("active")) {
      $all_items.removeClass("active");
    } else {
      $all_items.removeClass("active");
      $this_item.addClass("active");
    }
  });

  // Workflow 2nd tier show/hide task-group, tasks and objects
  $("#taskGroupPinSelect").on("click", function(e) {
    $("#taskGroupPin").show();
    $("#taskPin").hide();
    $("#objectPin").hide();
  });

  $("#taskPinSelect").on("click", function(e) {
    $("#taskGroupPin").hide();
    $("#taskPin").show();
    $("#objectPin").hide();
  });

  $("#objectPinSelect").on("click", function(e) {
    $("#taskGroupPin").hide();
    $("#taskPin").hide();
    $("#objectPin").show();
  });

  // Audit 2nd tier show/hide requests, responses and objects
  $("#auditRequestSelect").on("click", function(e) {
    $("#auditRequestPin").show();
    $("#auditResponsePin").hide();
    $("#auditObjectPin").hide();
    $("#auditEvidencePin").hide();
    $("#auditMeetingPin").hide();
  });

  $("#auditResponseSelect").on("click", function(e) {
    $("#auditRequestPin").hide();
    $("#auditResponsePin").show();
    $("#auditObjectPin").hide();
    $("#auditEvidencePin").hide();
    $("#auditMeetingPin").hide();
  });

  $("#auditObjectSelect").on("click", function(e) {
    $("#auditRequestPin").hide();
    $("#auditResponsePin").hide();
    $("#auditObjectPin").show();
    $("#auditEvidencePin").hide();
    $("#auditMeetingPin").hide();
  });

  $("#auditEvidenceSelect").on("click", function(e) {
    $("#auditRequestPin").hide();
    $("#auditResponsePin").hide();
    $("#auditObjectPin").hide();
    $("#auditEvidencePin").show();
    $("#auditMeetingPin").hide();
  });

  $("#auditMeetingSelect").on("click", function(e) {
    $("#auditRequestPin").hide();
    $("#auditResponsePin").hide();
    $("#auditObjectPin").hide();
    $("#auditEvidencePin").hide();
    $("#auditMeetingPin").show();
  });

  // show/hide add auditor in audit info widget
  $("#auditorFiledWrapTrigger").on("click", function() {
    var $this = $(this),
        $field_wrap = $this.closest(".wrap-row").find("#auditorFiledWrap");

    if($this.hasClass("active")) {
      $this.removeClass("active").show();
      $field_wrap.slideUp();
    } else {
      $this.addClass("active").hide();
      $field_wrap.slideDown();
    }
  });

});

// Widget search active state
function searchFilter() {
  var $this = $(this),
      $field = $this.closest(".lhs-search").find(".widgetsearch"),
      $filter_icon = $this.closest(".lhs-search").find(".filter-off");
  
  $field.addClass("active");
  $filter_icon.addClass("active");
}

function searchActive() {
  var $this = $(this),
      $button = $this.closest(".lhs-search").find(".widgetsearch-submit"),
      $search_field = $this.closest(".lhs-search").find(".widgetsearch"),
      $filter_icon = $this.closest(".lhs-search").find(".filter-off");

  if($this.val().trim() !== "") {
    $button.addClass("active");
    $button.bind("click", searchFilter);
  } else {
    $button.removeClass("active");
    $search_field.removeClass("active");
    $filter_icon.removeClass("active");
  }
}

$(".widgetsearch").on("keyup", searchActive);

// Pin content height options
function pinContent() {
  var options = {
        duration: 800,
        easing: 'easeOutExpo'
      },
      $pin = $(".pin-content"),
      $pin_height = $pin.height(),
      $info = $(".pin-content").find(".info"),
      $widget = $(".widget"),
      $widget_no_pin = $(".widget-no-pin"),
      $window = $(window),
      $win_height = $window.height(),
      $win_height_part = $win_height / 3,
      $pin_max = $win_height_part * 2,
      $pin_default = $win_height_part,
      $pin_min = 30;

  $info.css("height", $pin_default);
  $widget.css("margin-bottom", $win_height_part + 80);
  $widget_no_pin.css("margin-bottom", "0");

  $(".pin-action .max").on("click", function() {
    $info.animate({height: $pin_max}, options);
  });
  $(".pin-action .default").on("click", function() {
    $info.animate({height: $pin_default}, options);
    $widget.css("margin-bottom", $win_height_part + 80);
  });
  $(".pin-action .min").on("click", function() {
    $info.animate({height: $pin_min}, options);
    $widget.css("margin-bottom", 115);
  });
}

jQuery(pinContent);
jQuery(window).on("resize", pinContent);

// LHN pin
$(".lhn-pin").on("click", function() {
  var $this = $(this),
      $lhn_button = $(".lhn-trigger"),
      $lhn_bar = $(".bar-v");
  
  if ($this.hasClass("active")) {
    $this.removeClass("active");
    $lhn_button.removeClass("disabled");
    $lhn_button.attr("disabled", false);
    $lhn_bar.removeClass("disabled");
    $lhn_bar.attr("disabled", false);
  } else {
    $this.addClass("active");
    $lhn_button.addClass("disabled");
    $lhn_button.attr("disabled", true);
    $lhn_bar.addClass("disabled");
    $lhn_bar.attr("disabled", true);
  }
});

// Make sure the windows are resized properly

jQuery(resize_areas);
jQuery(window).on("resize", resize_areas);

// The function is borrowed from dashboard.js
function resize_areas() {
  var $window, $lhs, $lhsHolder, $area, $header, $footer, $innerNav,
      $objectArea, $bar, winHeight, winWidth, objectWidth, headerWidth,
      lhsWidth, footerMargin, internavHeight;

  $window = $(window);
  $lhs = $(".lhs");
  $lhsHolder = $(".lhs-holder");
  $lhsHolderActive = $(".lhs-holder.active");
  $footer = $(".footer");
  $header = $(".header-content");
  $innerNav = $(".inner-nav");
  $objectArea = $(".object-area");
  $objectAreaActive = $(".object-area.active");
  $topNav = $(".top-inner-nav");
  $area = $(".area");
  $bar = $(".bar-v");
  $lhsSearch = $(".lhs-search");
  $lhsSearchActive = $(".lhs-search.active");
  $lhnType = $(".lhn-type");

  winHeight = $window.height();
  winWidth = $window.width();
  header_height = $(".header").height();
  header_content_height = $(".header-content").height();
  top_nav_height = $(".top-inner-nav").height();
  footer_height = $(".footer").outerHeight();
  lhsHeight = winHeight - header_height - header_content_height - top_nav_height - footer_height - 60;
  footerMargin = lhsHeight;
  internavHeight = winHeight - 156;
  lhsWidth = $lhsHolder.width();
  lhsSearchWidth = $lhsSearch.width() - 30;
  lhsSearchWidthActive = $lhsSearchActive.width() - 30;
  barWidth = $bar.is(":visible") ? $bar.outerWidth() : 0;
  internavWidth = $innerNav.width() || 0; // || 0 for pages without inner-nav
  objectWidthActive = winWidth - lhsWidth - barWidth;
  objectWidth = winWidth;
  //headerWidth = winWidth - lhsWidth - barWidth - 20;
  headerWidth = winWidth - 40;
  lhnType_width = lhsWidth;

  $lhsHolder.css("height",lhsHeight).css("width", lhsWidth);
  $lhsHolderActive.css("left", "0");
  $bar.css("height",lhsHeight);
  $footer.css("margin-top",footerMargin);
  $innerNav.css("height",internavHeight);
  $header.css("width",headerWidth);
  $topNav.css("width",objectWidth);
  $(".widgetsearch").css("width", lhsSearchWidth - 36);
  $lhsSearchActive.css("width", lhsWidth - 40);
  $objectArea
    .css("margin-left","0")
    .css("height",internavHeight)
    .css("width",objectWidth);
  $objectAreaActive
    .css("margin-left", lhsWidth + 8)
    .css("width",objectWidthActive);
  $area.css("margin-left", "0");
  $lhnType.css("width", lhnType_width);
}
