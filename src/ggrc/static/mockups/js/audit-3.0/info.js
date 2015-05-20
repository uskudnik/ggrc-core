$(document).ready(function() {

  can.Component.extend({
    tag: "audit-info",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-info").html(can.view("/static/mockups/mustache/audit-3.0/info.mustache",{}));

  can.Component.extend({
    tag: "control",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-control").html(can.view("/static/mockups/mustache/audit-3.0/control.mustache",{}));

  can.Component.extend({
    tag: "ca",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-ca").html(can.view("/static/mockups/mustache/audit-3.0/control-assessments.mustache",{}));

  can.Component.extend({
    tag: "people",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-people").html(can.view("/static/mockups/mustache/audit-3.0/people.mustache",{}));

  can.Component.extend({
    tag: "program",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-program").html(can.view("/static/mockups/mustache/audit-3.0/program.mustache",{}));

  can.Component.extend({
    tag: "requests",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-requests").html(can.view("/static/mockups/mustache/audit-3.0/requests.mustache",{}));

  can.Component.extend({
    tag: "complete",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-complete").html(can.view("/static/mockups/mustache/audit-3.0/complete.mustache",{}));

  can.Component.extend({
    tag: "issues",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issues").html(can.view("/static/mockups/mustache/audit-3.0/issues.mustache",{}));

  can.Component.extend({
    tag: "issue-info",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-info").html(can.view("/static/mockups/mustache/audit-3.0/issue-info.mustache",{}));

  can.Component.extend({
    tag: "issue-ca",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-ca").html(can.view("/static/mockups/mustache/audit-3.0/issue-ca.mustache",{}));

  can.Component.extend({
    tag: "issue-audit",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-audit").html(can.view("/static/mockups/mustache/audit-3.0/issue-audit.mustache",{}));

  can.Component.extend({
    tag: "issue-controls",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-controls").html(can.view("/static/mockups/mustache/audit-3.0/issue-controls.mustache",{}));

  can.Component.extend({
    tag: "issue-program",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-program").html(can.view("/static/mockups/mustache/audit-3.0/issue-program.mustache",{}));

  can.Component.extend({
    tag: "issue-workflow",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-workflow").html(can.view("/static/mockups/mustache/audit-3.0/issue-workflow.mustache",{}));

  can.Component.extend({
    tag: "issue-workflow-tasks",
    scope: {
    },
    template: "<content/>",
    helpers: {
    },
    events: {
    }
  });
  $(".object-wrap-issue-workflow-tasks").html(can.view("/static/mockups/mustache/audit-3.0/issue-workflow-tasks.mustache",{}));

  function innerNavTrigger() {
    var $this = $(this),
        $allList = $this.closest(".nav").children("li"),
        $list = $this.closest("li"),
        aId = $this.attr("href"),
        $element = $("div"+aId);

    $allList.removeClass('active');
    $list.addClass('active');

    $(".object-wrap").hide();
    $(".object-wrap"+aId).show();
  }

  function personRole() {
    $('#PersonRole').modal('hide');
    $('#personAuth').html('Audit member');
    $('#personAuth2').html('Audit member');
  }

  function generateCA() {
    $("#ca .content").find(".tree-structure").find(".tree-item").show();
    $("#CaAdded").hide();
    $("#ca .content").find(".tree-structure").find(".zero-state").hide();
    $("#CaModalMapping").modal("hide");
    $("#CACounter").html("4");
    $("#assessmentTitle").html("Control assessments");
    $("#controlTitle").html("In scope Controls");
  }

  function reviewWorkflow() {
    $("#issueWorkflow").modal("hide");
    $("#workflowWrap").show();
    $(".nav li").removeClass("active");
    $("#workflowTaskWrap").show().addClass("active");
    window.location.href = '#issue-workflow-tasks';
    $(".object-wrap").hide();
    $(".object-wrap-issue-workflow-tasks").show();
  }

  function startTask() {
    $("#startTask").hide();
    $("#finishTask").show();
    $("#undoTask").show();
    $("#taskStatus").removeClass("status-assigned");
    $("#taskStatus").addClass("status-inprogress");
    $("#issueStatus").addClass("status-inprogress");
    $("#taskStatusMessage")
      .removeClass("state-assigned")
      .addClass("state-inprogress")
      .html("In progress");
    $("#issueStatusMessage").html("In progress");
  }

  function finishTask() {
    $("#finishTask").hide();
    $("#approveTask").show();
    $("#declineTask").show();
    $("#taskStatus").removeClass("status-inprogress");
    $("#taskStatus").addClass("status-finished");
    $("#issueStatus").removeClass("status-inprogress");
    $("#issueStatus").addClass("status-finished");
    $("#undoTask").hide();
    $("#taskStatusMessage")
      .removeClass("state-inprogress")
      .addClass("state-finished")
      .html("Finished");
    $("#issueStatusMessage").html("Finished");
    $("#reviewTrigger").hide();
    $("#reviewChoice").show();
  }

  function approveReview() {
    $("#approveTask").hide();
    $("#declineTask").hide();
    $("#taskStatus").removeClass("status-finished");
    $("#taskStatus").addClass("status-verified");
    $("#issueStatus").removeClass("status-finished");
    $("#issueStatus").addClass("status-verified");
    $("#taskStatusMessage")
      .removeClass("state-finished")
      .addClass("state-verified")
      .html("Verified");
    $("#issueStatusMessage")
      .closest("span")
      .removeClass("gray")
      .addClass("task-done")
      .html("<em>Verified</em>");
    $("#taskDone").show();
    $("#reviewChoice").hide();
    $("#issueStatusInfo")
      .removeClass("state-draft")
      .addClass("state-verified")
      .html("Closed");
  }

  function visualSelector() {
    $(this).find("option:selected").each(function() {
      var $respective = $(this).val(),
          $particular = $(".show-in-tree").find("#" + $respective + "").closest(".show-in-tree");

      $particular.children("span").css("display", "none");
      $(".show-in-tree").find("#" + $respective + "").css("display", "block");
    });
  }

  function AddCA() {
    $("#CaModal").modal("hide");
    $("#CaAdded").show();
  }

  function newIssue() {
    $("#issueModal").modal("hide");
    $("#newIssue").show();
    $(".nav li").removeClass("active");
    $("#issuesNavItem").closest("li").addClass("active");
    window.location.href = '#issues';
    $(".object-wrap").hide();
    $(".object-wrap-issues").show();
  }

  function defaultAssessor() {
    $(this).find("option:selected").each(function() {
      var $value = $(this).val(),
          $input = $(this).closest(".choose-from-select").find(".choose-input");

      if($value === "other") {
        $input.prop("disabled", false);
      } else {
        $input.prop("disabled", true);
      }
    });
  }

  function underAssessment() {
    $(this).find("option:selected").each(function() {
      var $value = $(this).val(),
          $label = $(this).closest(".choose-object").find(".inline-check"),
          $input = $label.find('input');

      if($value === "Control") {
        $input.prop("disabled", false);
        $label.removeClass("disabled");
      } else {
        $input.prop("disabled", true);
        $label.addClass("disabled");
      }
    });
  }

  function caEditPerson() {
    var $this = $(this),
        $currentPerson = $this.closest(".show-me"),
        $featurePerson = $this.closest(".show-me").next(".hide-me"),
        $save = $featurePerson.find(".save-person");

    if($this.hasClass("activated")) {
      $this.removeClass("activated");
      $currentPerson.show();
      $featurePerson.hide();
    } else {
      $this.addClass("activated");
      $currentPerson.hide();
      $featurePerson.show();
    }

    $save.on("click", function() {
      $currentPerson.show();
      $featurePerson.hide();
    });
  }

  $(".add-trigger").find(".disable")
    .attr("data-toggle", "")
    .attr("href", "#");

  function AssessmentTemplateDefined() {
    $("#CAModalTemplate").modal("hide");
    $("#assessmentWarning").remove();
    $(".add-trigger").find(".disable")
      .attr("data-toggle", "modal")
      .attr("href", "#CAModal")
      .removeClass("disable");
  }

  $(".top-inner-nav a").on("click", innerNavTrigger);

  $("#autoGenerateCA").on("click", generateCA);

  $("#auditRoleSave").on('click', personRole);

  $("#startReviewWorkflow").on("click", reviewWorkflow);

  $("#startTask").on("click", startTask);

  $("#finishTask").on("click", finishTask);

  $("#approveReview, #approveTask").on("click", approveReview);

  $(".visual-selector").on("change", visualSelector);

  $("#CASave").on("click", AddCA);

  $("#issueSave").on("click", newIssue);

  $("#assessorDefault").on("change", defaultAssessor);

  $("#underAssessment").on("change", underAssessment);

  $(".toggle-show-hide").on("click", caEditPerson);

  $("#templateDefined").on("click", AssessmentTemplateDefined);

});
