/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can) {
  GGRC.ListLoaders.StubFilteredListLoader(
    'GGRC.ListLoaders.TypeFilteredListLoader', {}, {
      init: function (source, modelNames) {
        var filterFn = function (result) {
          var i;
          var modelName;
          for (i = 0; i < modelNames.length; i++) {
            modelName = modelNames[i];
            if (typeof modelName !== 'string') {
              modelName = modelName.shortName;
            }
            if (result.instance.constructor &&
                result.instance.constructor.shortName === modelName) {
              return true;
            }
            if (result.instance.constructor.shortName === "Stub" &&
                result.instance.type === modelName) {
              return true;
            }
          }
          return false;
        };

        this._super(source, filterFn);
      }
    });
})(window.GGRC, window.can);
