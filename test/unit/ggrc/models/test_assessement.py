# Copyright (C) 2016 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

""" Unit tests for the Assessment object """

from sqlalchemy.ext import associationproxy
from sqlalchemy.orm import attributes

from ggrc import db
from ggrc.models import Assessment
from ggrc.models import mixins
from ggrc.models import mixins_assignable
from ggrc.models import object_document
from ggrc.models import object_owner
from ggrc.models import object_person
from ggrc.models import relationship
from ggrc.models import track_object_state

from unit.ggrc.models import test_mixins_base


class TestAssessmentMixins(test_mixins_base.TestMixinsBase):
  """ Tests inclusion of correct mixins and their attributes """

  def setUp(self):
    self.model = Assessment
    self.included_mixins = [
        mixins_assignable.Assignable,
        mixins.CustomAttributable,
        db.Model,
        object_document.Documentable,
        track_object_state.HasObjectState,
        mixins.TestPlanned,
        mixins.Timeboxed,
        object_owner.Ownable,
        object_person.Personable,
        relationship.Relatable,
        mixins.Described,
        mixins.FinishedDate,
        mixins.Hyperlinked,
        mixins.Noted,
        mixins.Slugged,
        mixins.Titled,
        mixins.VerifiedDate,
        mixins.WithContact,
    ]

    self.attributes_introduced = [
        ('audit', dict),
        ('design', attributes.InstrumentedAttribute),
        ('operationally', attributes.InstrumentedAttribute),
        ('object', dict),
        ('status', attributes.InstrumentedAttribute),                    # Stateful       # noqa
        ('assignees', property),                                         # Assignable     # noqa
        ('contact_id', attributes.InstrumentedAttribute),                # WithContact    # noqa
        ('contact', attributes.InstrumentedAttribute),                   # WithContact    # noqa
        ('secondary_contact', attributes.InstrumentedAttribute),         # WithContact    # noqa
        ('custom_attribute_values', attributes.InstrumentedAttribute),   # CustomAttrib.  # noqa
        ('description', attributes.InstrumentedAttribute),               # Described      # noqa
        ('end_date', attributes.InstrumentedAttribute),                  # Timeboxed      # noqa
        ('notes', attributes.InstrumentedAttribute),                     # Noted          # noqa
        ('object_documents', attributes.InstrumentedAttribute),          # Documentable   # noqa
        ('object_people', attributes.InstrumentedAttribute),             # Personable     # noqa
        ('os_state', attributes.InstrumentedAttribute),                  # HasObjectState # noqa
        ('owners', associationproxy.AssociationProxy),                   # Ownable        # noqa
        ('reference_url', attributes.InstrumentedAttribute),             # HyperLinked    # noqa
        ('related_sources', attributes.InstrumentedAttribute),           # Relatable      # noqa
        ('related_destinations', attributes.InstrumentedAttribute),      # Relatable      # noqa
        ('slug', attributes.InstrumentedAttribute),                      # Slugged        # noqa
        ('start_date', attributes.InstrumentedAttribute),                # Timeboxed      # noqa
        ('test_plan', attributes.InstrumentedAttribute),                 # TestPlanned    # noqa
        ('title', attributes.InstrumentedAttribute),                     # Titled         # noqa
        ('url', attributes.InstrumentedAttribute),                       # HyperLinked    # noqa
    ]
