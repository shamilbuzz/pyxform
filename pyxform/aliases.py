from pyxform.constants import * # This and 'pyxform.constants' are tightly related.
from pyxform.question_type_dictionary import QUESTION_TYPE_DICT
from pyxform.errors import PyXFormError

#Aliases:
#Ideally aliases should resolve to elements in the json form schema

#select, control and settings alias keys used for parsing,
#which is why self mapped keys are necessary.

control = {
    GROUP: GROUP,
    u"lgroup": REPEAT,
    REPEAT: REPEAT,
    LOOP: LOOP,
    u"looped group": REPEAT
}

select1= {
    SELECT_ONE:                               SELECT_ONE,
    SELECT_ONE_XLSFORM:                       SELECT_ONE,
    SELECT_ONE_XFORM:                         SELECT_ONE, # KoBoForm.
    SELECT_ONE + u" from":                    SELECT_ONE,
    u"add " + SELECT_ONE + u" prompt using":  SELECT_ONE,
}

select= {
  SELECT_ALL_THAT_APPLY:            SELECT_ALL_THAT_APPLY,
  SELECT_ALL_THAT_APPLY_XLSFORM:    SELECT_ALL_THAT_APPLY,
  SELECT_ALL_THAT_APPLY_XFORM:      SELECT_ALL_THAT_APPLY,
  SELECT_ALL_THAT_APPLY + u" from": SELECT_ALL_THAT_APPLY,
  u"add select multiple prompt using":        SELECT_ALL_THAT_APPLY,
}

multiple_choice = {u"select_one_external": u"select one external"}
multiple_choice.update(select1)
multiple_choice.update(select)

cascading = {
    u'cascading select': CASCADING_SELECT,
    CASCADING_SELECT: CASCADING_SELECT,
}

settings_header = {
    u"form_title": TITLE,
    u"set form title": TITLE,
    u"form_id": ID_STRING,
    SMS_KEYWORD: SMS_KEYWORD,
    SMS_SEPARATOR: SMS_SEPARATOR,
    SMS_ALLOW_MEDIA: SMS_ALLOW_MEDIA,
    SMS_DATE_FORMAT: SMS_DATE_FORMAT,
    SMS_DATETIME_FORMAT: SMS_DATETIME_FORMAT,
    u"set form id": ID_STRING,
    PUBLIC_KEY: PUBLIC_KEY,
    SUBMISSION_URL: SUBMISSION_URL
}

#TODO: Check on bind prefix approach in json.
#Conversion dictionary from user friendly column names to meaningful values
survey_header = {
    u"Label": LABEL,
    u"Name": NAME,
    u"SMS Field": SMS_FIELD,
    u"SMS Option": SMS_OPTION,
    u"SMS Sepatator": SMS_SEPARATOR,
    u"SMS Allow Media": SMS_ALLOW_MEDIA,
    u"SMS Date Format": SMS_DATE_FORMAT,
    u"SMS DateTime Format": SMS_DATETIME_FORMAT,
    u"SMS Response": SMS_RESPONSE,
    u"Type": TYPE,
    u"List_name": u"list_name",
    u"repeat_count": u"jr:count",
    u"read_only": BIND + u"::readonly",
    u"readonly": BIND + u"::readonly",
    u"relevant": BIND + u"::relevant",
    u"caption": LABEL,
    APPEARANCE: CONTROL + u"::" + APPEARANCE,  # TODO: this is also an issue
    u"relevance": BIND + u"::relevant",
    u"required": BIND + u"::required",
    u"constraint": BIND + u"::constraint",
    u"constraining message": BIND + u"::jr:constraintMsg",
    u"constraint message": BIND + u"::jr:constraintMsg",
    u"constraint_message": BIND + u"::jr:constraintMsg",
    u"calculation": BIND + u"::" + CALCULATE_XFORM,
    u"command": TYPE,
    u"tag": NAME,
    u"value": NAME,
    IMAGE_XLSFORM: MEDIA + u"::" + IMAGE_XLSFORM,
    AUDIO_XLSFORM: MEDIA + u"::" + AUDIO_XLSFORM,
    VIDEO_XLSFORM: MEDIA + u"::" + VIDEO_XLSFORM,
    u"count": CONTROL + u"::jr:count",
    u"repeat_count": CONTROL + u"::jr:count",
    u"jr:count": CONTROL + u"::jr:count",
    u"autoplay": CONTROL + u"::autoplay",
    u"rows": CONTROL + u"::rows",
    #New elements that have to go into itext elements:
    u"noAppErrorString" : BIND + u"::jr:noAppErrorString",
    u"no_app_error_string" : BIND + u"::jr:noAppErrorString",
    u"requiredMsg" : BIND + u"::jr:requiredMsg",
    u"required_message" : BIND + u"::jr:requiredMsg",
}

list_header = {
    u"caption": LABEL,
    u"list_name": LIST_NAME,
    u"value": NAME,
    IMAGE_XLSFORM: MEDIA + u"::" + IMAGE_XLSFORM,
    AUDIO_XLSFORM: MEDIA + u"::" + AUDIO_XLSFORM,
    VIDEO_XLSFORM: MEDIA + u"::" + VIDEO_XLSFORM,
}

#Note that most of the type aliasing happens in all.xls
type = {
    u"imei": DEVICEID_XLSFORM,
    IMAGE_XLSFORM: u"photo",
    u"add " + IMAGE_XLSFORM + u" prompt": u"photo",
    u"add photo prompt": u"photo",
    u"add " + AUDIO_XLSFORM + u" prompt": AUDIO_XLSFORM,
    u"add " + VIDEO_XLSFORM + u" prompt": VIDEO_XLSFORM,
}

yes_no = {
    "yes": True,
    "Yes": True,
    "YES": True,
    "true": True,
    "True": True,
    "TRUE": True,
    "true()": True,
    "no": False,
    "No": False,
    "NO": False,
    "false": False,
    "False": False,
    "FALSE": False,
    "false()": False,
}

label_optional_types = [
    DEVICEID_XLSFORM,
    PHONENUMBER_XLSFORM,
    SIMSERIAL_XLSFORM,
    CALCULATE_XFORM, # Not 'CALCULATE_XLSFORM'?
    START_XLSFORM,
    END_XLSFORM,
    TODAY_XLSFORM,
]


def get_xform_question_type(original_question_type_str):
    '''
    Determine the XForm-compatible question type that corresponds to the given type.
    
    :param str original_question_type_str:
    :return: An XForm-compatible question type.
    :rtype: str
    '''
    
    xform_question_type_str= None
    
    # Strip off the "xsd:" prefix, if present.
    if original_question_type_str.startswith('xsd:'):
        question_type_str= original_question_type_str.split('xsd:')[-1]
    else:
        question_type_str= original_question_type_str
    
    if question_type_str in select1:
        xform_question_type_str= SELECT_ONE_XFORM
    elif question_type_str in select:
        xform_question_type_str= SELECT_ALL_THAT_APPLY_XFORM
    elif question_type_str in XFORM_TYPES:
        # The question type is already valid for use in an XForm.
        xform_question_type_str= question_type_str
    
    elif question_type_str in XLSFORM_TO_XFORM_TYPES:
        # The question type is an XLSForm type with a known XLSForm equivalent.
        xform_question_type_str= XLSFORM_TO_XFORM_TYPES[question_type_str]

    elif question_type_str in QUESTION_TYPE_DICT:
        # The question type is a known type possibly with an XForm equivalent.
        possible_xform_question_type= \
          QUESTION_TYPE_DICT[question_type_str][BIND][TYPE]
        if possible_xform_question_type in XFORM_TYPES:
            xform_question_type_str= possible_xform_question_type
    elif question_type_str == GROUP:
        xform_question_type_str= question_type_str

    if not xform_question_type_str:
        raise PyXFormError('Unexpected XForm type "{}".'.format(question_type_str))
    
    return xform_question_type_str


def get_xlsform_question_type(original_question_type_str):
    '''
    Determine the XLSForm-compatible question type that corresponds to the given type.
    
    :param str original_question_type_str:
    :return: An XLSForm-compatible question type.
    :rtype: str
    '''
    
    xlsform_question_type_str= None
    
    if original_question_type_str in set(XLSFORM_TYPES).union(XLSFORM_METADATA_TYPES):
        # The question type is already valid for use in an XLSForm.
        xlsform_question_type_str= original_question_type_str
    
    elif original_question_type_str in XFORM_TO_XLSFORM_TYPES:
        # The question type is an XForm type with a known XLSForm equivalent.
        xlsform_question_type_str= XFORM_TO_XLSFORM_TYPES[original_question_type_str]

    elif original_question_type_str == GROUP:
        xlsform_question_type_str= original_question_type_str
    else:
        # FIXME: This wouldn't be necessary if 'Question' internally standardized \
        #   to use types from the XForm (or alternatively XLSForm) spec.
        xform_question_type= get_xform_question_type(original_question_type_str)
        if xform_question_type in XFORM_TO_XLSFORM_TYPES:
            xlsform_question_type_str= XFORM_TO_XLSFORM_TYPES[xform_question_type]

    if not xlsform_question_type_str:
        raise PyXFormError('Unexpected XLSForm type "{}".'.format(original_question_type_str))
    else:
        return xlsform_question_type_str
