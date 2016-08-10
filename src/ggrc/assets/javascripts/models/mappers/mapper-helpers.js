/*!
    Copyright (C) 2016 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can) {
  GGRC.MapperHelpers = {};

  GGRC.MapperHelpers.Proxy = function Proxy(
    optionModelName, joinOptionAttr, joinModelName, joinObjectAttr,
    instanceJoinAttr) {
    return new GGRC.ListLoaders.ProxyListLoader(
        joinModelName, joinObjectAttr, joinOptionAttr,
        instanceJoinAttr, optionModelName);
  };

  GGRC.MapperHelpers.Direct = function Direct(
      optionModelName, instanceJoinAttr, remoteJoinAttr) {
    return new GGRC.ListLoaders.DirectListLoader(
      optionModelName, instanceJoinAttr, remoteJoinAttr);
  };

  GGRC.MapperHelpers.Indirect = function Indirect(instModelName, joinAttr) {
    return new GGRC.ListLoaders.IndirectListLoader(instModelName, joinAttr);
  };

  GGRC.MapperHelpers.Search = function Search(queryFunction, observeTypes) {
    return new GGRC.ListLoaders.SearchListLoader(queryFunction, observeTypes);
  };

  GGRC.MapperHelpers.Multi = function Multi(sources) {
    return new GGRC.ListLoaders.MultiListLoader(sources);
  };

  GGRC.MapperHelpers.TypeFilter = function TypeFilter(source, modelName) {
    return new GGRC.ListLoaders.TypeFilteredListLoader(source, [modelName]);
  };

  GGRC.MapperHelpers.TypeConverter = function TypeConverter(source, converter) {
    return new GGRC.ListLoaders.TypeConverterListLoader(source, converter);
  };

  GGRC.MapperHelpers.AttrFilter = function AttrFilter(source, filterName,
                                                      keyword, type) {
    return new GGRC.ListLoaders.AttrFilteredListLoader(source, filterName,
      keyword, type);
  };

  GGRC.MapperHelpers.CustomFilter = function CustomFilter(source, filterFn) {
    return new GGRC.ListLoaders.CustomFilteredListLoader(source, filterFn);
  };

  GGRC.MapperHelpers.Reify = function Reify(source) {
    return new GGRC.ListLoaders.ReifyingListLoader(source);
  };

  GGRC.MapperHelpers.Cross = function Cross(localMapping, remoteMapping) {
    return new GGRC.ListLoaders.CrossListLoader(localMapping, remoteMapping);
  };

  GGRC.all_local_results = function (instance) {
    // Returns directly-linked objects
    var loaders;
    var multiLoader;
    var localLoaders = [];

    if (instance._all_local_results_binding)
      return instance._all_local_results_binding.refresh_stubs();

    loaders = GGRC.Mappings.get_mappings_for(instance.constructor.shortName);
    can.each(loaders, function (loader, name) {
      if (loader instanceof GGRC.ListLoaders.DirectListLoader ||
        loader instanceof GGRC.ListLoaders.ProxyListLoader) {
        localLoaders.push(name);
      }
    });

    multiLoader = new GGRC.ListLoaders.MultiListLoader(localLoaders);
    instance._all_local_results_binding = multiLoader.attach(instance);
    return instance._all_local_results_binding.refresh_stubs();
  };
})(window.GGRC, window.can);
