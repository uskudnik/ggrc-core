/*!
    Copyright (C) 2016 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, can) {
  var Proxy = GGRC.MapperHelpers.Proxy;
  var Direct = GGRC.MapperHelpers.Direct;
  var Indirect = GGRC.MapperHelpers.Indirect;
  var Search = GGRC.MapperHelpers.Search;
  var Multi = GGRC.MapperHelpers.Multi;
  var TypeFilter = GGRC.MapperHelpers.TypeFilter;
  var TypeConverter = GGRC.MapperHelpers.TypeConverter;
  var AttrFilter = GGRC.MapperHelpers.AttrFilter;
  var CustomFilter = GGRC.MapperHelpers.CustomFilter;
  var Cross = GGRC.MapperHelpers.Cross;
  /*
    class GGRC.Mappings
    represents everything known about how GGRC objects connect to each other.

    a Mappings instance contains the set of known mappings for a module, such as "ggrc_core"
    or "ggrc_gdrive_integration".  The set of all Mappings instances is used throughout the
    system to build widgets, map and unmap objects, etc.

    To configure a new Mappings instance, use the following format :
    { <mixin name or source object type> : {
        _mixins : [ <mixin name>, ... ],
        _canonical : { <option type> : <name of mapping in parent object>, ... }
        <mapping name> : GGRC.Mappings.Proxy(...) | GGRC.Mappings.Direct(...) | GGRC.Mappings.Indirect(...)
                        | GGRC.Mappings.Multi(...) | GGRC.Mappings.TypeFilter(...) | GGRC.Mappings.Cross(...)
                        | GGRC.Mappings.CustomFilter(...),
        ...
      }
    }
  */
  can.Construct('GGRC.Mappings', {
    // Convenience properties for building mappings types.
    Proxy: Proxy,
    Direct: Direct,
    Indirect: Indirect,
    Search: Search,
    Multi: Multi,
    TypeFilter: TypeFilter,
    TypeConverter: TypeConverter,
    AttrFilter: AttrFilter,
    CustomFilter: CustomFilter,
    Cross: Cross,
    modules: {},

    /*
      return all mappings from all modules for an object type.
      object - a string representing the object type's shortName

      return: a keyed object of all mappings (instances of GGRC.ListLoaders.BaseListLoader) by mapping name
      Example: GGRC.Mappings.get_mappings_for('Program')
    */
    get_mappings_for: function (object) {
      var mappings = {};
      can.each(this.modules, function (mod, name) {
        if (mod[object]) {
          can.each(mod[object], function (mapping, mappingName) {
            if (mappingName === '_canonical')
              return;
            mappings[mappingName] = mapping;
          });
        }
      });
      return mappings;
    },
    /*
      return the canonical mapping (suitable for joining) between two objects.
      object - the string type (shortName) of the "from" object's class
      option - the string type (shortName) of the "to" object's class

      return: an instance of GGRC.ListLoaders.BaseListLoader (mappings are implemented as ListLoaders)
    */
    get_canonical_mapping: function (object, option) {
      var mapping = null;
      can.each(this.modules, function (mod, name) {
        if (mod._canonical_mappings && mod._canonical_mappings[object] &&
          mod._canonical_mappings[object][option]) {
          mapping =
            CMS.Models[object]
              .get_mapper(mod._canonical_mappings[object][option]);
          return false;
        }
      });
      return mapping;
    },
    /*
      return the defined name of the canonical mapping between two objects.
      object - the string type (shortName) of the "from" object's class
      option - the string type (shortName) of the "to" object's class

      return: an instance of GGRC.ListLoaders.BaseListLoader (mappings are implemented as ListLoaders)
    */
    get_canonical_mapping_name: function (object, option) {
      var mappingName = null;
      can.each(this.modules, function (mod, name) {
        if (mod._canonical_mappings && mod._canonical_mappings[object] &&
          mod._canonical_mappings[object][option]) {
          mappingName = mod._canonical_mappings[object][option];
          return false;
        }
      });
      return mappingName;
    },
    /*
      return all canonical mappings (suitable for joining) from all modules for an object type.
      object - a string representing the object type's shortName

      return: a keyed object of all mappings (instances of GGRC.ListLoaders.BaseListLoader) by option type
    */
    get_canonical_mappings_for: function (object) {
      var mappings = {};
      can.each(this.modules, function (mod, name) {
        if (mod._canonical_mappings && mod._canonical_mappings[object]) {
          can.each(mod._canonical_mappings[object],
            function (mappingName, option) {
              mappings[option] = CMS.Models[object].get_mapper(mappingName);
            });
        }
      });
      return mappings;
    },
    /*
      return the join model for the canonical mapping between two objects if and only if the canonical mapping is a Proxy.
      model_name_a - the string type (shortName) of the "from" object's class
      model_name_b - the string type (shortName) of the "to" object's class

      return: a string of the shortName of the join model (subclass of can.Model.Join) or null
    */
    join_model_name_for: function (modelNameA, modelNameB) {
      var joinDescriptor = this.get_canonical_mapping(modelNameA, modelNameB);
      var result;
      if (joinDescriptor instanceof GGRC.ListLoaders.ProxyListLoader) {
        result = joinDescriptor.model_name;
      } else {
        result = null;
      }
      return result;
    },
    /*
      make a new instance of the join model for the canonical mapping between two objects
       if and only if the canonical mapping is a Proxy.
      object - the string type (shortName) of the "from" object's class
      option - the string type (shortName) of the "to" object's class
      join_attrs - any other attributes to add to the new instance

      return: an instance of the join model (subclass of can.Model.Join) or null
    */
    make_join_object: function (object, option, joinAttrs) {
      var joinModel;
      var joinMapping = this.get_canonical_mapping(object.constructor.shortName,
        option.constructor.shortName);
      var objectAttrs = {
        id: object.id,
        type: object.constructor.shortName
      };
      var optionAttrs = {
        id: option.id,
        type: option.constructor.shortName
      };
      var result;

      if (joinMapping && joinMapping.model_name) {
        joinModel = CMS.Models[joinMapping.model_name];
        joinAttrs = $.extend({}, joinAttrs || {});
        joinAttrs[joinMapping.option_attr] = optionAttrs;
        joinAttrs[joinMapping.object_attr] = objectAttrs;

        result = new joinModel(joinAttrs);
      } else {
        result = null;
      }
      return result;
    }
  }, {
    /*
      On init:
      kick off the application of mixins to the mappings and resolve canonical mappings
    */
    init: function (name, opts) {
      var createdMappings;
      var that = this;
      this.constructor.modules[name] = this;
      this._canonical_mappings = {};
      if (this.groups) {
        can.each(this.groups, function (group, name) {
          if (typeof group === 'function') {
            that.groups[name] = $.proxy(group, that.groups);
          }
        });
      }
      createdMappings = this.create_mappings(opts);
      can.each(createdMappings, function (mappings, objectType) {
        if (mappings._canonical) {
          if (!that._canonical_mappings[objectType]) {
            that._canonical_mappings[objectType] = {};
          }
          can.each(mappings._canonical || [],
            function (optionTypes, mappingName) {
              if (!can.isArray(optionTypes)) {
                optionTypes = [optionTypes];
              }
              can.each(optionTypes, function (optionType) {
                that._canonical_mappings[objectType][optionType] = mappingName;
              });
            });
        }
      });
      $.extend(this, createdMappings);
    },
    // Recursively handle mixins -- this function should not be called directly.
    reify_mixins: function (definition, definitions) {
      var that = this;
      var finalDefinition = {};
      if (definition._mixins) {
        can.each(definition._mixins, function (mixin) {
          if (typeof (mixin) === 'string') {
            // If string, recursive lookup
            if (!definitions[mixin]) {
              console.debug('Undefined mixin: ' + mixin, definitions);
            } else {
              can.extend(true, finalDefinition,
                that.reify_mixins(definitions[mixin], definitions));
            }
          } else if (can.isFunction(mixin)) {
            // If function, call with current definition state
            mixin(finalDefinition);
          } else {
            // Otherwise, assume object and extend
            if (finalDefinition._canonical && mixin._canonical) {
              mixin = can.extend({}, mixin);

              can.each(mixin._canonical, function (types, mapping) {
                if (finalDefinition._canonical[mapping]) {
                  if (!can.isArray(finalDefinition._canonical[mapping])) {
                    finalDefinition._canonical[mapping] =
                      [finalDefinition._canonical[mapping]];
                  }
                  finalDefinition._canonical[mapping] =
                    can.unique(finalDefinition._canonical[mapping]
                      .concat(types));
                } else {
                  finalDefinition._canonical[mapping] = types;
                }
              });
              finalDefinition._canonical = can.extend({}, mixin._canonical,
                finalDefinition._canonical);
              delete mixin._canonical;
            }
            can.extend(finalDefinition, mixin);
          }
        });
      }
      can.extend(true, finalDefinition, definition);
      delete finalDefinition._mixins;
      return finalDefinition;
    },

    // create mappings for definitions -- this function should not be called directly/
    create_mappings: function (definitions) {
      var mappings = {};

      can.each(definitions, function (definition, name) {
        // Only output the mappings if it's a model, e.g., uppercase first letter
        if (name[0] === name[0].toUpperCase())
          mappings[name] = this.reify_mixins(definition, definitions);
      }, this);
      return mappings;
    }
  });
})(window.GGRC, window.can);
