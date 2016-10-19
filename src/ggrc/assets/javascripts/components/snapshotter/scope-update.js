/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */
(function (can, $) {
  'use strict';

  GGRC.Components('SnapshotScopeUpdater', {
    tag: 'snapshot-scope-update',
    template: '<content/>',
    scope: {
      instance: null,
      upsertIt: function (scope, el, ev) {
        GGRC.Controllers.Modals.confirm({
          instance: scope,
          modal_title: 'Audit scope update',
          modal_description: 'Are you sure you want to update all snapshots?',
          modal_confirm: 'Update Audit Scope',
          skip_refresh: true,
          button_view: GGRC.mustache_path + '/modals/prompt_buttons.mustache'
        }, function () {
          var instance = this.instance;

          instance.refresh().then(function () {
            var data = {
              operation: 'upsert'
            };
            instance.attr('snapshots', data);
            instance.save();
          });
        }.bind(this));
      }
    }
  });
})(window.can, window.can.$);
