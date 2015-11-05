/*!
  Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
  Created By: andraz@reciprocitylabs.com
  Maintained By: andraz@reciprocitylabs.com
*/

(function(can) {
  can.Component.extend({
    tag: "people-list",
    template: can.view(GGRC.mustache_path + "/base_templates/people_list.mustache"),
    scope: {
      people: {},
    },
    events: {
      init: function() {
        this.scope.instance.get_assignees().then(function(assignees) {
          this.scope.attr("people", assignees);
        }.bind(this));
      },
    },
  });
})(window.can);
