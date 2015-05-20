$(document).ready(function() {

  can.Component.extend({
    tag: "reporting",
    scope: {
      report_gen: false,
      //attr_selected: false,
      tabs: [
        {title: "ISO Systems"},
        {title: "Overdue tasks"},
      ],
      table_title: [
        {tbl_title_1: "Program Title", tbl_title_2: "Program Owner", tbl_title_3: "Control Title", tbl_title_4: "Control Owner", tbl_title_5: "Control Contact", tbl_title_6: "Control URL", tbl_title_7: "Control Code", tbl_title_8: "Control State", tbl_title_9: "System Title", tbl_title_10: "System Owner", tbl_title_11: "System Contact", tbl_title_12: "System URL", tbl_title_13: "System Code", tbl_title_14: "System Effective date", tbl_title_15: "System Stop date", tbl_title_16: "System State"}
      ],
      table_data: [
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 1", tbl_data_4: "John Doe", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT000", tbl_data_8: "Draft", tbl_data_9: "SYS1.1", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "S001", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Final"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 1", tbl_data_4: "John Doe", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT000", tbl_data_8: "Draft", tbl_data_9: "SYS1.2", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "S002", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Maintenance"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 1", tbl_data_4: "John Doe", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT000", tbl_data_8: "Effective", tbl_data_9: "SYS1.3", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "S003", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Final"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 2", tbl_data_4: "Lisa Mona", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT002", tbl_data_8: "Effective", tbl_data_9: "SYS2.1", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "S004", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Final"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 3", tbl_data_4: "Karim Abdul", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT045", tbl_data_8: "Ineffective", tbl_data_9: "SYS3.1", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "SX", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Final"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 3", tbl_data_4: "Karim Abdul", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT045", tbl_data_8: "Ineffective", tbl_data_9: "SYS3.2", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "SXa", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Draft"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 4", tbl_data_4: "Manny Manning", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT-AK-47a", tbl_data_8: "Effective", tbl_data_9: "SYS4.1", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "SX11", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Draft"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 4", tbl_data_4: "Manny Manning", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT-AK-47a", tbl_data_8: "Effective", tbl_data_9: "SYS4.2", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "SX12", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Final"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 4", tbl_data_4: "Manny Manning", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT-AK-47a", tbl_data_8: "Effective", tbl_data_9: "SYS4.3", tbl_data_10: "Jane Doe", tbl_data_11: "Richard Feynman", tbl_data_12: "http://google.com/system/manhattan-project", tbl_data_13: "SX13", tbl_data_14: "01/24/2014", tbl_data_15: "12/24/2015", tbl_data_16: "Final"},
        {tbl_data_1: "Program 1", tbl_data_2: "Predrag", tbl_data_3: "CTRL 5", tbl_data_4: "Carl Grove", tbl_data_5: "Julius Robert Oppenheimer", tbl_data_6: "http://google.com/control/manhattan-project", tbl_data_7: "CT-PR", tbl_data_8: "Effective", tbl_data_9: "", tbl_data_10: "", tbl_data_11: "", tbl_data_12: "", tbl_data_13: "", tbl_data_14: "", tbl_data_15: "", tbl_data_15: ""}
      ],
      filterRules: [
      ],
      relevantFilter: [
      ]
    },
    template: "<content/>",
    helpers: {
    },
    events: {
      "#custom_report_name keyup": function(el, ev) {
        var $item = this.element.find('li.active'),
            index = $item.index(),
            tabs = this.scope.tabs,
            new_tabs = 0;

        tabs[index].attr('title', el.val());
        this.element.find("#newReport .closed").show();

        // Calculate tabs numbers
        tabs.forEach(function(tab) {
          if (tab.new_report) {
            new_tabs++;
          }
        });

        // Revert "New Report n" if custom_report_name is empty
        if (tabs[index].attr('title').trim() === "") {
          tabs[index].attr('title', "New Report " + new_tabs);
        }
      },
      ".report-trigger click": function(el, ev) {
        this.element.find(".zero-state").fadeOut(500);
        this.element.find(".generated-report").delay(500).fadeIn(500);

        this.scope.attr('report_gen', true);
      },
      "#newReportAdd click": function(el, ev) {
        var tabs = this.scope.tabs,
            new_tabs = 1,
            $ul = el.closest('ul');
        tabs.forEach(function(tab) {
          if (tab.new_report) {
            new_tabs++;
          }
        });
        tabs.push({title: "New Report " + new_tabs, new_report: true});
        $ul.find('li').not('.hidden-widgets-list').last().addClass("active");
      },
      "#addFilterRule click": function(el, ev) {
        var newRule = this.scope.filterRules,
            new_rules = 0;
        newRule.forEach(function(rule) {
          if (rule.new_rule) {
            new_rules++;
          }
        });
        newRule.push({label: "Relevant to:", new_rule: true});
      },
      "#addRelevantFilterRule click": function(el, ev) {
        var relevantGroup = this.scope.relevantFilter,
            new_relevant = 0;
        relevantGroup.forEach(function(relevant) {
          if (relevant.new_relevant_group) {
            new_relevant++;
          }
        });
        relevantGroup.push({new_relevant_group: true});
      },
      ".remove_filter click": function(el) {
        var $item = el.closest(".single-line-filter"),
            index = $item.index(),
            rule = this.scope.filterRules;
        rule.splice(index - 1, 1);
      },
      ".remove_filter_group click": function(el) {
        var $item = el.closest(".single-line-filter"),
            index = $item.index(),
            rules = this.scope.relevantFilter;
        rules.splice(index - 1, 1);
      }
    }
  });

  $(".reporting-import").html(can.view("/static/mockups/mustache/reporting.mustache",{}));
});
