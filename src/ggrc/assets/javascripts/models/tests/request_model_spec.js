/*!
  Copyright (C) 2016 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('CMS.Models.Request', function () {
  'use strict';

  var Model;

  beforeAll(function () {
    Model = CMS.Models.Request;
  });

  describe('display_name() method', function () {
    var method;  // the method under test
    var instance;

    beforeEach(function () {
      instance = new can.Map({
        title: 'Request 18',
        id: 18
      });
      method = Model.prototype.display_name.bind(instance);
    });

    it('returns a generic name for deleted objects', function () {
      var result;
      instance.attr('title', undefined);
      result = method();
      expect(result).toEqual('"Request 18" (DELETED)');
    });
  });
});
