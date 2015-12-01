'''
Export 'Survey' objects to CSV-or-XLS-formatted XLSForms. Aliased and available 
as methods on 'Survey' objects.

.. module:: survey_to_xlsform
    :Date: 2014/09/24

.. codeauthor: Esmail Fadae <esmail.fadae@kobotoolbox.org>
'''


from __future__ import absolute_import

import base64
import re
import os
import cStringIO
import csv
#import json    # Used by 'to_ssjson()'

import xlwt

import pyxform.question
import pyxform.aliases
from . import constants
from .errors import PyXFormError


GROUP_EXPORT_WARNING= 'Exporting groups to XLSForms is currently an experimental feature.'
SKIP_LOGIC_EXPORT_WARNING= 'Exporting skip logic in XLSForms is not currently supported.'
CALCULATION_EXPORT_WARNING= 'Exporting calculations to XLSForms is currently an experimental feature.'


class XlsFormExporter():
    
    CASCADING_SELECT_WARNING= u'Cascading-select (choice filter) questions not currently supported. Question choices for any such questions have not been imported.'
    CASCADING_SELECT_SAD_CHOICE_NAME= u'question_choices_not_imported'
    CASCADING_SELECT_SAD_CHOICE_LABEL= u'Apologies, your choices for this (cascading-select) question could not be automatically imported.'
    
    def __init__(self, survey, warnings=None):
        '''
        Prepare a representation of the survey ready to be easily exported as a 
        XLS or CSV XLSForm.

        :param pyxform.survey.Survey survey: The survey to be exported.
        :param list warnings: Optional list into which any warnings generated during export will be appended.
        '''
        
        # TODO: Support repeats, 'or_other', hints, constraints, ...
        
        # TODO: Ideally would want a data structure that preserves order while providing O(1) lookups. Ordered set? (http://stackoverflow.com/q/1653970)
        # Pre-populate with mandatory columns where possible (i.e. not label(s)).
        self.survey_sheet_columns= [constants.NAME, constants.TYPE]
        self.choices_sheet_columns= [constants.LIST_NAME, constants.NAME]
        self.settings_sheet_columns= list()

        self.survey_sheet_rows= [self.survey_sheet_columns]
        self.choices_sheet_rows= [self.choices_sheet_columns]
        self.settings_sheet_rows= [self.settings_sheet_columns]
        
        # Keep track of any warnings generated.
        if warnings != None:    # Directly test for 'None' since empty iterables are also "falsy".
            self.warnings= warnings
        else:
            self.warnings= list()
        
        self.record_settings(survey)
        
        self.record_question_container(survey)
        
        # Store the non-empty sheets.
        self.sheet_dict= dict()
        if len(self.survey_sheet_rows) > 1:
            self.sheet_dict[constants.SURVEY]= self.survey_sheet_rows
        if len(self.choices_sheet_rows) > 1:
            self.sheet_dict[constants.CHOICES]= self.choices_sheet_rows
        if len(self.settings_sheet_rows) > 1:
            self.sheet_dict[constants.SETTINGS]= self.settings_sheet_rows


    def record_question_container(self, question_container):
        for child_element in question_container['children']:
            if isinstance(child_element, pyxform.question.Question):
                self.record_question_data(child_element)
            elif isinstance(child_element, pyxform.section.GroupedSection):
                self.record_grouped_section(child_element)
            else:
                raise PyXFormError('Unexpected survey child type "{}".'.format(type(child_element)))


    def record_question_data(self, question):
        '''
        Record the given question and any associated data such as the options 
        for multiple-choice questions.
        
        :param pyxform.question.Question question:
        '''

        # Create a list with an initially empty entry for each column in the sheet.
        survey_row= [''] * len(self.survey_sheet_columns)

        # Record the entry for the mandatory 'name' column.
        question_name= question[constants.NAME]
        survey_row[self.survey_sheet_columns.index(constants.NAME)]= question_name

        # Record the entry for the mandatory 'type' column.
        xlsform_question_type= pyxform.aliases.get_xlsform_question_type(question[constants.TYPE])
        if not isinstance(question, pyxform.question.MultipleChoiceQuestion):
            survey_row[self.survey_sheet_columns.index(constants.TYPE)]= xlsform_question_type
        else:
            # Special handling for select-type questions.

            # Check that the reported 'type' matches the object type.
            if xlsform_question_type not in \
              [constants.SELECT_ONE_XLSFORM, constants.SELECT_ALL_THAT_APPLY_XLSFORM]:
                raise PyXFormError('Unexpected multiple-choice question type "{}"'.format(question['type']))

            # TODO: Would be nice to reuse the 'list name' when encountering reused sets of choices.
            # Generate a 'list name' comprised of the question name followed by 8 random bytes cast to string.
            list_name= question_name + '_' + base64.urlsafe_b64encode(os.urandom(8))

            # Strip out any non-alphanumeric characters so KoBoForm can import. \
            #   Decreasing the space of possible strings, while an egregious \
            #   affront, should be safe.
            list_name= re.compile('[\W_]+').sub('_', list_name)

            survey_row[self.survey_sheet_columns.index(constants.TYPE)]= xlsform_question_type + ' ' + list_name

            # TODO: Handle cascading-select questions (http://opendatakit.github.io/odk-xform-spec/#secondary-instances).
            # If the question appears to be a cascading-select, report in the
            #   output that the question choices could not be gathered.
            if question.is_cascading_select():
                # Deferring documentation to 'record_question_choice()'...
                cascading_select_sad_choices_row= [''] * len(self.choices_sheet_columns)
                dict_to_insert= {constants.LIST_NAME: list_name, constants.NAME: self.CASCADING_SELECT_SAD_CHOICE_NAME}
                self.insert_dict_into_row(dict_to_insert, cascading_select_sad_choices_row, self.choices_sheet_columns)
                
                # FIXME: Unsafe assumption that the "choices" sheet should have a "label" column.
                if constants.LABEL in self.choices_sheet_columns:
                    cascading_select_sad_choices_row[self.choices_sheet_columns.index(constants.LABEL)]= self.CASCADING_SELECT_SAD_CHOICE_LABEL
                else:
                    self.choices_sheet_columns.append(constants.LABEL)
                    cascading_select_sad_choices_row.append(self.CASCADING_SELECT_SAD_CHOICE_LABEL)
                self.choices_sheet_rows.append(cascading_select_sad_choices_row)
                
                if self.CASCADING_SELECT_WARNING not in self.warnings:
                    self.warnings.append(self.CASCADING_SELECT_WARNING)

            else:
                # Extract and record the choices.
                for question_choice in question[constants.CHILDREN]:
                    self.record_question_choice(question_choice, list_name)

        # Record entries for the mandatory 'label' and/or 'label::X' columns.
        question_label_dict= self.get_survey_element_label(question)
        if (not question_label_dict) and (xlsform_question_type not in constants.XLSFORM_METADATA_TYPES):
            raise PyXFormError('Non-metadata questions must have at least one label.')
        self.insert_dict_into_row(question_label_dict, survey_row, self.survey_sheet_columns)

        # TODO: Support constraints/skip logic.
        if (constants.BIND in question) and (constants.RELEVANT_XFORM in question[constants.BIND]):
            if SKIP_LOGIC_EXPORT_WARNING not in self.warnings:
                self.warnings.append(SKIP_LOGIC_EXPORT_WARNING)

        if xlsform_question_type == constants.CALCULATE_XFORM:
            if CALCULATION_EXPORT_WARNING not in self.warnings:
                self.warnings.append(SKIP_LOGIC_EXPORT_WARNING)
            dict_to_insert= {constants.CALCULATE_XLSFORM: question[constants.BIND][constants.CALCULATE_XFORM]}
            self.insert_dict_into_row(dict_to_insert, survey_row, self.survey_sheet_columns)

        if (constants.BIND in question) and (constants.REQUIRED_XFORM in question[constants.BIND]):
            dict_to_insert= {constants.REQUIRED_XFORM: question[constants.BIND][constants.REQUIRED_XFORM]}
            self.insert_dict_into_row(dict_to_insert, survey_row, self.survey_sheet_columns)

        # Add the row into the 'survey' sheet.
        self.survey_sheet_rows.append(survey_row)


    @staticmethod
    def insert_dict_into_row(dict_to_insert, row, columns):

        for column_name, cell_value in dict_to_insert.iteritems():
            if column_name in columns:
                row[columns.index(column_name)]= cell_value
            else:
                # A previously unencountered column.
                columns.append(column_name)
                row.append(cell_value)


    def record_question_choice(self, question_choice, list_name):
        '''
        Record the information for an individual choice from a multiple-choice question.
        
        :param pyxform.question.Option question_choice: The choice being imported.
        :param str list_name: A unique identifier for the set of choices this choice belongs to.
        '''
        
        # Create a list with an initially empty entry for each column in the sheet.
        choices_row= [''] * len(self.choices_sheet_columns)
        
        # Record the entry for the mandatory 'list name' column.
        choices_row[self.choices_sheet_columns.index(constants.LIST_NAME)]= list_name
        # Record the entry for the mandatory 'name' column.
        choices_row[self.choices_sheet_columns.index(constants.NAME)]= question_choice[constants.NAME]
        
        # Record entries for the mandatory 'label' and/or 'label::X' columns.
        choice_label_dict= self.get_survey_element_label(question_choice)
        if not choice_label_dict:
            raise PyXFormError('Choices for multiple-choice questions must have at least one label.')
        self.insert_dict_into_row(choice_label_dict, choices_row, self.choices_sheet_columns)
                
        # Add the row into the 'choices' sheet.
        self.choices_sheet_rows.append(choices_row)
        

    def record_grouped_section(self, grouped_section):
        '''
        Record the data associated with a group of questions.
        
        :param pyxform.section.GroupedSection grouped_section:
        '''

        # Record the question group and return.

        if grouped_section[constants.NAME] == constants.META_XFORM:
            # Do not export the 'meta' group as it is automatically added by 'pyxform'.
            return

        # Warn early in case of failure.
        if GROUP_EXPORT_WARNING not in self.warnings:
            self.warnings.append(GROUP_EXPORT_WARNING)

        # Generate the group's header.
        group_header= [''] * len(self.survey_sheet_columns)
        # Record the entry for the mandatory 'name' column.
        group_name= grouped_section[constants.NAME]
        group_header[self.survey_sheet_columns.index(constants.NAME)]= group_name
        # Record the entry for the mandatory 'type' column.
        group_header[self.survey_sheet_columns.index(constants.TYPE)]= u'begin group'
        # Record entries for the mandatory 'label' and/or 'label::X' columns.
        group_label_dict= self.get_survey_element_label(grouped_section)
        if not group_label_dict:
            raise PyXFormError('Question groups must have at least one label.')
        self.insert_dict_into_row(group_label_dict, group_header, self.survey_sheet_columns)

        # Insert the group header into the "survey" sheet.
        self.survey_sheet_rows.append(group_header)
        
        # Record the grouped questions and/or sub-groups.
        self.record_question_container(grouped_section)

        # Generate and insert the group's footer.
        group_footer= [''] * len(self.survey_sheet_columns)
        # Record the entry for the mandatory 'type' column.
        group_footer[self.survey_sheet_columns.index(constants.TYPE)]= u'end group'
        # Additionally record the group name, for clarity.
        group_footer[self.survey_sheet_columns.index(constants.NAME)]= group_name
        self.survey_sheet_rows.append(group_footer)
        

    def record_settings(self, survey):
        '''
        Record the information for the 'settings' sheet, if present.
        
        :param pyxform.survey.Survey survey:
        '''

        # TODO: More potential settings listed at xlsform.org.
        
        settings_row= list()
        if constants.NAME in survey:
            self.settings_sheet_columns.append('form_id')
            settings_row.append(survey[constants.NAME])
        if constants.TITLE in survey:
            self.settings_sheet_columns.append('form_title')
            settings_row.append(survey[constants.TITLE])

        self.settings_sheet_rows.append(settings_row)


    @staticmethod
    def get_survey_element_label(survey_element):
        '''
        Return a dictionary containing the survey element's singular label or its 
        translations, if present, ready for export to an XLSForm. Labels are keyed 
        by 'label' or 'label::Language'.

        :param pyxform.survey.SurveyElement survey_element:
        :type survey_element: pyxform.question.Question or pyxform.question.Option
        :return: Spreadsheet data (in rows) keyed by sheet name.
        :rtype: {str: DataFrame}
        '''

        labels= dict()
        if isinstance(survey_element.get(constants.LABEL), basestring) \
          and (survey_element[constants.LABEL] != ''):
            # Simple label.
            label_column= constants.LABEL
            labels[label_column]= survey_element[constants.LABEL]
        elif survey_element.get(constants.LABEL):
            # Label(s) provided in a 'dict' of translations.
            for language in survey_element[constants.LABEL].iterkeys():
                label_column= constants.LABEL + '::' + language
                labels[label_column]= survey_element[constants.LABEL][language]

        return labels


def to_xls(survey, path=None, warnings=None):
    '''
    Convert the provided survey to a XLS-encoded XLSForm.
    
    :param pyxform.survey.Survey survey:
    :param str path: Optional filesystem path to the desired output file.
    :param list warnings: Optional list into which any warnings generated during export will be appended.
    :returns: If the 'path' parameter was omitted, nothing. Otherwise, a buffer containing the exported form.
    :rtype: NoneType or 'cStringIO.StringIO'
    '''
    
    # Organize the data for spreadsheet output.
    sheet_dict= XlsFormExporter(survey, warnings).sheet_dict
    
    workbook= xlwt.Workbook(encoding='UTF-8')
    # Write out the data sheet-by-sheet.
    for sheet_name, sheet_rows in sheet_dict.iteritems():
        worksheet= workbook.add_sheet(sheet_name)
        for i_row, r in enumerate(sheet_rows):
            # Bold the top row.
            if i_row == 0:
                style_kwarg= {'style': xlwt.easyxf('font: bold on')}
            elif style_kwarg:
                style_kwarg= dict()
            # Enter the data.
            for i_col, cell_data in enumerate(r):
                worksheet.write(i_row, i_col, cell_data, **style_kwarg)
    
    if path:
        with open(path, 'w') as f:
            workbook.save(f)
    else:
        filelike_obj= cStringIO.StringIO()
        workbook.save(filelike_obj)
        filelike_obj.seek(0)    # As a courtesy.
        return filelike_obj


def to_csv(survey, path=None, warnings=None, koboform=False):
    '''
    Convert the provided survey to a CSV-formatted XLSForm.
    
    :param pyxform.survey.Survey survey:
    :param str path: Optional filesystem path to the desired output file.
    :param list warnings: Optional list into which any warnings generated during export will be appended.
    :param bool koboform: Optional flag to specially format the output for KoBoForm.
    :returns: If the 'path' parameter was omitted, nothing. Otherwise, a buffer containing the exported form.
    :rtype: NoneType or 'cStringIO.StringIO'
    '''
    
    # Organize the data for spreadsheet output.
    sheet_dict= XlsFormExporter(survey, warnings).sheet_dict

    # If exporting for KoBoForm, ensure there is one "label" column.
    survey_columns= sheet_dict[constants.SURVEY][0]
    if koboform and ('label' not in survey_columns):
        label_columns= [c for c in survey_columns if constants.LABEL in c]

        # Since the KoBoForm UI is in English, try using that first. 
        if 'label::English' in label_columns:
            chosen_label_column= 'label::English'
        else:
            # Otherwise, select a language quasi-randomly.
            chosen_label_column= label_columns[0]

        # If multiple translations were available, warn the user about one's preferential treatment.
        if (warnings != None) and (len(label_columns) > 1):
            chosen_language= chosen_label_column.split(constants.LABEL+'::')[1]
            language_default_warning= 'Multiple translations are not supported in KoBoForm. Defaulting to language "{}".'.format(chosen_language)
            warnings.append(language_default_warning)

        # Rename the selected label column to "label" in both the "survey" and "choices" sheets.
        survey_columns[survey_columns.index(chosen_label_column)]= constants.LABEL
        if constants.CHOICES in sheet_dict:
            choices_columns= sheet_dict[constants.CHOICES][0]
            choices_columns[choices_columns.index(chosen_label_column)]= constants.LABEL

    # Reorganize the data into multi-"sheet" CSV form and export.
    if path:
        filelike_obj= open(path, 'w')
    else:
        filelike_obj= cStringIO.StringIO()

    if koboform:
        # KoBoForm-specific CSV formatting options (copied from github.com/kobotoolbox/dkobo).
        csv_writer_kwargs= {'quotechar':'"', 'doublequote':False, 'escapechar':'\\', \
                      'delimiter':',', 'quoting':csv.QUOTE_ALL}
    else:
        csv_writer_kwargs= dict()
    csv_writer= csv.writer(filelike_obj, **csv_writer_kwargs)
    
    # Write out the data sheet-by-sheet.
    for sheet_name, sheet_rows in sheet_dict.iteritems():
        # Prepend in a row containing just the sheet's name.
        csv_writer.writerow([sheet_name])
        for row in sheet_rows:
            # Write out each row of data prepended with an empty cell and ensuring all cells are UTF-8 encoded.
            csv_writer.writerow([''] + [cell_data.encode('utf-8') for cell_data in row])

    if path:
        filelike_obj.close()
    else:
        filelike_obj.seek(0) # As a courtesy.
        return filelike_obj


# TODO: Reactivate pending use in KoBoForm.
#
# def to_ssjson(survey, path=None, warnings=None):
#     '''
#     Convert the provided survey to a (non-standard) JSON-formatted XLSForm.
#     
#     :param pyxform.survey.Survey survey:
#     :param str path: Optional filesystem path to the desired output file.
#     :param list warnings: Optional list into which any warnings generated during export will be appended.
#     :returns: If the 'path' parameter was omitted, nothing. Otherwise, a buffer containing the exported form.
#     :rtype: NoneType or 'cStringIO.StringIO'
#     '''
#     
#     # Organize the data for spreadsheet output.
#     sheet_dict= XlsFormExporter(survey, warnings).sheet_dict
#     
#     # Reorganize the data into multi-"sheet" JSON form and export.
#     sheets_list = list()
#     for sheet_name, df in sheet_dict.iteritems():
#         rows_list= list()
#         # Insert the column names as the first row.
#         header_row = (pandas.DataFrame(df.columns.to_series()).T).irow(0).tolist()
#         rows_list.append(header_row)
#         
#         # Append in the data rows.
#         for _, data_row in df.iterrows():
#             rows_list.append(data_row.tolist())
#             
#         sheets_list.append( [sheet_name, rows_list] )
#     json_string= json.dumps(sheets_list, indent=4)
# 
#     if path:
#         with open(path, 'w') as f:
#             f.write(json_string)
#     else:
#         return cStringIO.StringIO(json_string)
