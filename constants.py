"""
This file contains constants that correspond with the property names in the json survey format. (@see json_form_schema.json)
These names are to be shared between X2json and json2Y programs.
By putting them in a shared file, the literal names can be easily changed, typos can be avoided, and references are easier to find.
"""
#TODO: Replace matching strings in the json2xforms code (builder.py, survey.py, survey_element.py, question.py) with these constants

TITLE = u"title"
NAME = u"name"
ID_STRING = u"id_string"
SMS_KEYWORD = u"sms_keyword"
SMS_FIELD = u"sms_field"
SMS_OPTION = u"sms_option"
SMS_SEPARATOR = u"sms_separator"
SMS_ALLOW_MEDIA = u"sms_allow_media"
SMS_DATE_FORMAT = u"sms_date_format"
SMS_DATETIME_FORMAT = u"sms_datetime_format"
SMS_RESPONSE = u"sms_response"
VERSION = u"version"
PUBLIC_KEY = u"public_key"
SUBMISSION_URL = u"submission_url"
DEFAULT_LANGUAGE = u"default_language"
STYLE = u"style"

BIND = u"bind"#TODO: What should I do with the nested types? (readonly and relevant)
MEDIA = u"media"
CONTROL = u"control"
APPEARANCE = u"appearance"

LOOP = u"loop"
COLUMNS = u"columns"

CHILDREN = u"children"
PARENT= u'parent'
MODEL_XFORM= u'model'
BODY_XFORM= u'body'
INSTANCE_XFORM= u'instance'
META_XFORM= u'meta'
REF_XFORM= u'ref'


# XFrom bind attributes: http://opendatakit.github.io/odk-xform-spec/#bind-attributes.
NODESET_XFORM= u'nodeset'
TYPE = u"type"
READONLY_XFORM= u'readonly'
REQUIRED_XFORM= u'required'
RELEVANT_XFORM= u'relevant'
CALCULATE_XFORM= u'calculate'
CONSTRAINT_XFORM= u'constraint'
CONSTRAINT_MSG_XFORM= u'jr:constraintMsg'
PRELOAD_XFORM= u'jr:preload'
PRELOAD_PARAMS_XFORM= u'jr:preloadParams'

BIND_ATTRIBUTES_XFORM= {NODESET_XFORM, TYPE, READONLY_XFORM, REQUIRED_XFORM, \
  RELEVANT_XFORM, CALCULATE_XFORM, CONSTRAINT_XFORM, CONSTRAINT_MSG_XFORM, \
  PRELOAD_XFORM, PRELOAD_PARAMS_XFORM}


# Question/data types.
# ODK XForm data types: http://opendatakit.github.io/odk-xform-spec/#data-types.
# XLSForm question types: http://xlsform.org/#question%20types.
STRING_XFORM= u'string'
STRING_XLSFORM= u'text'

INT_XFORM= u'int'
INT_XLSFORM= u'integer'

BOOLEAN_XFORM= u'boolean'
# Presumably boolean questions are represented as "select one" questions in XLSForms.

DECIMAL_XFORM= u'decimal'
DECIMAL_XLSFORM= DECIMAL_XFORM

DATE_XFORM= u'date'
DATE_XLSFORM= DATE_XFORM

TIME_XFORM= u'time'
TIME_XLSFORM= TIME_XFORM

DATETIME_XFORM= u'dateTime'
DATETIME_XLSFORM= DATETIME_XFORM

SELECT_ALL_THAT_APPLY_XFORM= u'select'
SELECT_ALL_THAT_APPLY_XLSFORM= u'select_multiple'
SELECT_ALL_THAT_APPLY = u"select all that apply"

SELECT_ONE_XFORM= u'select1'
SELECT_ONE_XLSFORM= u'select_one'
SELECT_ONE = u"select one"

GEOPOINT_XFORM= u'geopoint'
GEOPOINT_XLSFORM= GEOPOINT_XFORM

GEOTRACE_XFORM= u'geotrace'

GEOSHAPE_XFORM= u'geoshape'

BINARY_XFORM= u'binary'
IMAGE_XLSFORM= u'image'
AUDIO_XLSFORM= u'audio'
VIDEO_XLSFORM= u'video'

BARCODE_XFORM= u'barcode'
BARCODE_XLSFORM= BARCODE_XFORM

NOTE_XLSFORM= u'note'

CALCULATE_XLSFORM= u'calculation'

TRIGGER_XLSFORM= u'acknowledge' # Currently undocumented in XLSForm standard (2014/09/25).

XFORM_TYPES= {STRING_XFORM, INT_XFORM, BOOLEAN_XFORM, DECIMAL_XFORM, DATE_XFORM, \
  TIME_XFORM, DATETIME_XFORM, SELECT_ALL_THAT_APPLY_XFORM, SELECT_ONE_XFORM, \
  GEOPOINT_XFORM, GEOTRACE_XFORM, GEOSHAPE_XFORM, BINARY_XFORM, BARCODE_XFORM}

XLSFORM_TYPES= {STRING_XLSFORM, INT_XLSFORM, DECIMAL_XLSFORM, DATE_XLSFORM, \
  TIME_XLSFORM, DATETIME_XLSFORM, SELECT_ALL_THAT_APPLY_XLSFORM, SELECT_ONE_XLSFORM, \
  GEOPOINT_XLSFORM, IMAGE_XLSFORM, AUDIO_XLSFORM, VIDEO_XLSFORM, \
  BARCODE_XLSFORM, NOTE_XLSFORM, CALCULATE_XLSFORM, TRIGGER_XLSFORM}

XFORM_TO_XLSFORM_TYPES= {
    STRING_XFORM: STRING_XLSFORM,
    INT_XFORM: INT_XLSFORM,
#     BOOLEAN_XFORM: None,
    DECIMAL_XFORM: DECIMAL_XLSFORM,
    DATE_XFORM: DATE_XLSFORM,
    TIME_XFORM: TIME_XLSFORM,
    DATETIME_XFORM: DATETIME_XLSFORM,
    SELECT_ALL_THAT_APPLY_XFORM: SELECT_ALL_THAT_APPLY_XLSFORM,
    SELECT_ONE_XFORM: SELECT_ONE_XLSFORM,
    GEOPOINT_XFORM: GEOPOINT_XLSFORM,
#     GEOTRACE_XFORM: None,
#     GEOSHAPE_XFORM: None,
#     BINARY_XFORM: [IMAGE_XLSFORM, AUDIO_XLSFORM, VIDEO_XLSFORM],
    BARCODE_XFORM: BARCODE_XFORM,
}

XLSFORM_TO_XFORM_TYPES= {xlsform_type: xform_type for xform_type, xlsform_type in XFORM_TO_XLSFORM_TYPES.iteritems()}

# Metadata types: http://xlsform.org/#metadata
START_XLSFORM=          u'start'
END_XLSFORM=            u'end'
TODAY_XLSFORM=          u'today'
DEVICEID_XLSFORM=       u'deviceid'
SUBSCRIBERID_XLSFORM=   u'subscriberid'
SIMSERIAL_XLSFORM=      u'simserial'
PHONENUMBER_XLSFORM=    u'phonenumber'

XLSFORM_METADATA_TYPES= {START_XLSFORM, END_XLSFORM, TODAY_XLSFORM, \
  DEVICEID_XLSFORM, SUBSCRIBERID_XLSFORM, SIMSERIAL_XLSFORM, PHONENUMBER_XLSFORM}


# XForm body elements: http://opendatakit.github.io/odk-xform-spec/#body-elements
INPUT_XFORM= u'input'
UPLOAD_XFORM= u'upload'
TRIGGER_XFORM= u'trigger'
GROUP = u"group"
REPEAT = u"repeat"

XFORM_BODY_ELEMENTS= {INPUT_XFORM, SELECT_ONE_XFORM, SELECT_ALL_THAT_APPLY_XFORM, \
  UPLOAD_XFORM, TRIGGER_XFORM, GROUP, REPEAT}

# Special body element types that are also question types (?).
XFORM_TYPE_BODY_ELEMENTS= {SELECT_ONE_XFORM, SELECT_ALL_THAT_APPLY_XFORM, TRIGGER_XFORM}


# XForm body sub-elements: http://opendatakit.github.io/odk-xform-spec/#body-elements
HINT = u"hint"
LABEL = u"label"
OUTOPUT_XFORM= u'output'
ITEM_XFORM= u'item'
ITEMSET_XFORM= u'itemset'
VALUE_XFORM= u'value'



# XLS Specific constants
LIST_NAME = u"list name"
CASCADING_SELECT = u"cascading_select"
TABLE_LIST = u"table-list" # hyphenated because it goes in appearance, and convention for appearance column is dashes
# The following are the possible sheet names:
SURVEY = u"survey"
SETTINGS = u"settings"
# These sheet names are for list sheets
CHOICES = u"choices"
COLUMNS = u"columns" #this is for loop statements
CHOICES_AND_COLUMNS = u"choices and columns"
CASCADING_CHOICES = u"cascades"
