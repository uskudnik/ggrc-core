/*!
 Copyright (C) 2016 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

GGRC.ListLoaders.BaseListLoader("GGRC.ListLoaders.TypeConverterListLoader", {
}, {
  init: function (source) {
    this.source_binding = source;
    this._super(source);
  },
  init_listeners: function (binding) {
    // We have no listeners since data is immutable but we need it due to
    // BaseListLoader's "method signiture"
  },
  refresh_stubs: function (binding) {
    // We already have all the data on front-end, no need for stubs.
    // Converting to stubs also causes request to object's root_collection
    // API endpoint.
    return this.refresh_instances(binding);
  },
  refresh_instances: function (binding) {
    var source_binding = binding.instance.get_binding(this.source_binding);
    return source_binding.refresh_instances().then(function (results) {
      var rev_to_snapshot_lookup = {};

      if (!_.isUndefined(binding)) {
        _.map(binding.instance.snapshoted_objects, function (stub) {
          var snapshot = CMS.Models.Snapshot.cache[stub.id];
          rev_to_snapshot_lookup[snapshot.revision_id] = stub.id;
        });
      }

      var converted_results = new can.List(_.map(results, function (result) {
        var revision = result.instance;
        var snapshot = CMS.Models.Snapshot.cache[rev_to_snapshot_lookup[result.instance.id]];
        var data = revision.content.serialize();
        var model = CMS.Models[revision.resource_type];
        var obj;
        data.type = revision.resource_type;
        data.id = revision.resource_id;
        // tree_view_controller.draw_list tests full object data with
        // selfLink, if it's not present it tries to fetch from backend.
        data.selfLink = "/api/" + model.root_collection + "/" + data.id;
        obj = new model(data);
        obj.snapshot = snapshot;
        return this.make_result(obj, [result], binding);
      }.bind(this)));
      return this.insert_results(binding, converted_results);
    }.bind(this));
  }
});
