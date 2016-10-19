/*!
    Copyright (C) 2016 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (GGRC, _) {
  var base_widgets_by_type = {
    AccessGroup: 'Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Audit: 'AccessGroup Clause Contract Control Assessment AssessmentTemplate DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor',
    Clause: 'AccessGroup Audit Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Contract: 'AccessGroup Audit Clause Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Process Product Program Project Request Section System Vendor Snapshot',
    Control: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Request Section Standard System Vendor Snapshot',
    Assessment: 'AccessGroup Audit Clause Contract Control DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Request Section Standard System Vendor',
    DataAsset: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Facility: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Issue: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor',
    Market: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Objective: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    OrgGroup: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Person: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Policy Process Product Program Project Regulation Request Request Section Standard System Vendor',
    Policy: 'AccessGroup Audit Clause Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Process Product Program Project Request Section System Vendor Snapshot',
    Process: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Product: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Program: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Project Regulation Request Section Standard System Vendor',
    Project: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor',
    Regulation: 'AccessGroup Audit Clause Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Process Product Program Project Request Section System Vendor Snapshot',
    Request: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor',
    Section: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Standard: 'AccessGroup Audit Clause Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Process Product Program Project Request Section System Vendor Snapshot',
    System: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Vendor: 'AccessGroup Audit Clause Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor Snapshot',
    Snapshot: 'AccessGroup Audit Contract Control Assessment DataAsset Facility Issue Market Objective OrgGroup Person Policy Process Product Program Project Regulation Request Section Standard System Vendor',
  };
  base_widgets_by_type = _.mapValues(base_widgets_by_type, function (conf) {
    return conf.split(' ').sort();
  });
  GGRC.tree_view = GGRC.tree_view || new can.Map();
  GGRC.tree_view.attr('base_widgets_by_type', base_widgets_by_type);
})(this.GGRC, this._);
