# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from ggrc import db
from ggrc.models import Assessment
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc import generator
from integration.ggrc.models.factories import AssessmentFactory

# 325839
class TestAssessment(TestCase):

  def test_auto_slug_generation(self):
    AssessmentFactory(title="Some title")
    db.session.commit()
    ca = Assessment.query.first()
    self.assertEqual("ASSESSMENT-{}".format(ca.id), ca.slug)

class TestAssessmentAutoStatusChange(TestCase):
  def setUp(self):
    super(TestAssessmentAutoStatusChange, self).setUp()
    self.api = Api()
    self.generator = generator.Generator()
    self.object_generator = generator.ObjectGenerator()

  def create_simple_assessment(self):
    user_roles = self.object_generator.generate_user_roles()
    _, program = self.object_generator.generate_program(user_roles['admin'])
    _, audit = self.object_generator.generate_audit(program,
                                                    user_roles['admin'])

    random_object = self.object_generator.generate_random_objects(count=1)[0]
    assessors = [
      (user_roles['admin'], "Creator"),
      (user_roles['admin'], "Assessor")
    ]
    assessment, relationships = self.object_generator.generate_assessment(
      program,
      # Parent instance Audit is not bound to a Session; lazy load operation of attribute 'program' cannot proceed
      audit,
      user_roles['admin'],
      random_object,
      assessors
    )

    assessment_response, assessment = assessment

    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "Open")

    assessment_json = assessment_response.json
    del assessment_json["assessment"]["status"]

    return assessment, assessment_json, relationships, program, audit, user_roles

  def test_first_class_attribute_edit(self):
    assessment, assessment_json, _, _, _, _ = self.create_simple_assessment()

    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "Open")

    assessment_json["assessment"]["title"] = "edited title"

    self.api.put(assessment, assessment_json)
    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "In Progress")
    self.assertEqual(assessment.title, "edited title")


    assessment_json["assessment"]["status"] = "Final"
    self.api.put(assessment, assessment_json)

    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "Final  ")


  def test_adding_persons(self):
    assessment, assessment_json, relationships, _, _, user_roles = self.create_simple_assessment()
    # print "user_roles: ", user_roles
    # print "\n"*2
    # print "-"*80
    # print "relationships: "
    # for res, rel in relationships:
    #   print res, rel.source_id, rel.source_type, rel.destination_id, rel.destination_type


    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "Open")

    assessment_json["assessment"]["title"] = "edited title"
    self.api.put(assessment, assessment_json)
    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "In Progress")
    self.assertEqual(assessment.title, "edited title")

    assessment_json["assessment"]["status"] = "Final"
    self.api.put(assessment, assessment_json)

    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "Final")

    print "\n"*10
    print "CHANGING ASSIGNEE FIELDS"

    response = self.object_generator.generate_relationship(
      assessment, user_roles['creator'], "AssigneeType", "Verifier")

    assessment = self.generator.get_object(Assessment, assessment.id)
    self.assertEqual(assessment.status, "In Progress")

    # raise Exception("bla")
