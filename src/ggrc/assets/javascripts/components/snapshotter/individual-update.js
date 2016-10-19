/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */
(function (can, $) {
  'use strict';

  GGRC.Components('SnapshotIndividualUpdater', {
    tag: 'snapshot-individual-update',
    template: '<content/>',
    scope: {
      instance: null,
      updateIt: function (scope, el, ev) {
        GGRC.Controllers.Modals.confirm({
          instance: scope,
          modal_title: 'Snapshot update',
          modal_description: 'Are you sure you want to update this snapshot?',
          modal_confirm: 'Update Audit Scope',
          skip_refresh: true,
          button_view: GGRC.mustache_path + '/modals/prompt_buttons.mustache'
        }, function () {
          var instance = this.instance;

          instance.refresh().then(function () {
            var data = {
              operation: 'update'
            };
            instance.attr('individual-update', data);
            instance.save();
          });
        }.bind(this));
      }
    }
  });
})(window.can, window.can.$);
