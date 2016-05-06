/*!
 Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 Created By: urban@reciprocitylabs.com
 Maintained By: urban@reciprocitylabs.com
 */
(function (can, $) {
  GGRC.Components('cloner', {
    tag: 'cloner',
    template: '<content/>',
    scope: {
      instance: null,
      modal_title: '@',
      modal_description: '@',
      includeObjects: [],
      cloner: function (scope, el, ev) {
        var instance = scope.instance;
        var $target = $('<div class=\'modal hide\'></div>');

        instance.refresh();

        $target
          .modal({backdrop: 'static'})
          .ggrc_controllers_modals({
            new_object_form: false,
            button_view:
              GGRC.mustache_path + '/modals/confirm_buttons.mustache',
            modal_title: scope.attr('modal_title'),
            modal_description: scope.attr('modal_description'),
            modal_confirm: 'Copy',
            content_view: GGRC.mustache_path +
              '/' + instance.class.root_collection + '/cloner.mustache',
            // includeObjects gets translated to includeobjects
            includeObjects: scope.includeObjects
          })
          .on('click', 'a.btn[data-toggle=confirm]', {scope: scope},
            function (event) {
              var scope = event.data.scope;
              var instance = scope.instance;

              $target.modal('hide').remove();

              instance.attr('operation', 'clone');
              instance.attr('associatedObjects', scope.includeObjects);

              $.when(instance.save()).then(function (object) {
                var url = '/' + instance.class.root_collection + '/' +
                  object._operation_data.clone.audit.id;
                GGRC.navigate(url);
              });
            });
      }
    }
  });

  GGRC.Components('clone-child', {
    tag: 'clone-child',
    template: '<content/>',
    scope: {
      instance: null,
      type: '@',
      toggleClone: function (scope, el, ev) {
        var type = scope.attr('type');
        // includeObjects from cloner component
        var includeObjects = scope.includeobjects;
        var i;
        if (_.contains(includeObjects, type)) {
          i = _.findIndex(includeObjects, type);
          scope.includeobjects.splice(i, 1);
        } else {
          scope.includeobjects.push(type);
        }
      }
    }
  });
})(window.can, window.can.$);
