/*!
 Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 Created By: urban@reciprocitylabs.com
 Maintained By: urban@reciprocitylabs.com
 */
(function (can, $) {
  'use strict';

  GGRC.Components('objectCloner', {
    tag: 'object-cloner',
    template: '<content/>',
    scope: {
      instance: null,
      modalTitle: '@',
      modalDescription: '@',
      includeObjects: {},
      getIncluded: function () {
        var included = this.attr('includeObjects');
        return _.filter(can.Map.keys(included), function (val) {
          return included[val];
        });
      },
      cloneObject: function (scope, el, ev) {
        var instance = this.instance;

        instance.refresh();
        this.attr('includeObjects', {});

        GGRC.Controllers.Modals.confirm({
          instance: scope,
          modal_title: scope.attr('modalTitle'),
          modal_description: scope.attr('modalDescription'),
          content_view: GGRC.mustache_path + '/' +
            instance.class.root_collection + '/object_cloner.mustache',
          modal_confirm: 'Copy',
          skip_refresh: true
        }, function () {
          instance.attr('operation', 'clone');
          instance.attr('associatedObjects', this.getIncluded());
          $.when(instance.save()).then(function (object) {
            var url = '/' + instance.class.root_collection + '/' +
              object._operation_data.clone.audit.id;
            GGRC.navigate(url);
          });
        }.bind(this));
      }
    }
  });
})(window.can, window.can.$);
