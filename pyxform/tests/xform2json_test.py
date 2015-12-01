import cStringIO
import tempfile
from unittest2 import TestCase

import utils
import pyxform.survey_from
from pyxform.builder import create_survey_from_path


class Test_DumpAndLoadXForm2Json(TestCase):

    maxDiff = None

    def setUp(self):
        self.excel_files = [
            "gps.xls",
            #"include.xls",
            "specify_other.xls",
            "loop.xls",
            "text_and_integer.xls",
            # todo: this is looking for json that is created (and
            # deleted) by another test, is should just add that json
            # to the directory.
            # "include_json.xls",
            "simple_loop.xls",
            "yes_or_no_question.xls",
            "xlsform_spec_test.xlsx",
            "group.xls",
        ]
        
        self.surveys = list()
        for filename in self.excel_files:
            path = utils.path_to_text_fixture(filename)
            try:
                self.surveys.append(create_survey_from_path(path))
            except Exception as e:
                print("Error on : " + filename)
                raise e

    def test_load_from_dump(self):
        for survey in self.surveys:
            with tempfile.NamedTemporaryFile(suffix='-pyxform.json') as temp_file:
                survey.json_dump(temp_file.name)    # What is this line for?
            filey_xml_dump= cStringIO.StringIO(survey.to_xml().encode('UTF-8'))
            survey_from_dump = pyxform.survey_from.xform(filelike_obj=filey_xml_dump)
            self.assertMultiLineEqual(
                survey.to_xml(), survey_from_dump.to_xml())
