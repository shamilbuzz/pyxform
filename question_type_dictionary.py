from pyxform.constants import *


# from xls2json import QuestionTypesReader, print_pyobj_to_json
# def generate_new_dict():
#     """
#     This is just here incase there is ever any need to generate the question type dictionary from all.xls again.
#     It shouldn't be called as part of any application.
#     """
#     # FIXME: You probably don't have this path on your machine.
#     path_to_question_types = "/home/nathan/aptana-workspace/pyxform/pyxform/question_types/all.xls"
#     json_dict = QuestionTypesReader(path_to_question_types).to_json_dict()
#     print_pyobj_to_json(json_dict, 'new_quesiton_type_dict.json')


_SELECT_1_TYPE_DICT= {
    CONTROL: {
        "tag": SELECT_ONE_XFORM
    }, 
    BIND: {
        TYPE: SELECT_ONE_XFORM
    }
}

_SELECT_TYPE_DICT= {
    CONTROL: {
        "tag": SELECT_ALL_THAT_APPLY_XFORM
    }, 
    BIND: {
        TYPE: SELECT_ALL_THAT_APPLY_XFORM
    }
}

_IMAGE_TYPE= {
    CONTROL: {
        "tag": "upload",
        "mediatype": IMAGE_XLSFORM + "/*"
    }, 
    BIND: {
        TYPE: BINARY_XFORM
    }
}

_VIDEO_TYPE= {
    CONTROL: {
        "tag": "upload", 
        "mediatype": VIDEO_XLSFORM + "/*"
    }, 
    BIND: {
        TYPE: BINARY_XFORM
    }
}

_AUDIO_TYPE= {
    CONTROL: {
        "tag": "upload", 
        "mediatype": AUDIO_XLSFORM + "/*"
    }, 
    BIND: {
        TYPE: BINARY_XFORM
    }
}

_DATE_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: DATE_XFORM
    }
}

_DATETIME_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: DATETIME_XFORM
    }
}

_GEOPOINT_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: GEOPOINT_XFORM
    }
}

_GEOPOINT_TYPE_W_HINT= dict(_GEOPOINT_TYPE, \
    **{"hint": "GPS coordinates can only be collected when outside."})

_GEOSHAPE_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: GEOSHAPE_XFORM
    }
}

_GEOSHAPE_TYPE_W_HINT= dict(_GEOSHAPE_TYPE, \
            **{"hint": "GPS coordinates can only be collected when outside."})

_GEOTRACE_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: GEOTRACE_XFORM
    }
}

_GEOTRACE_TYPE_W_HINT= dict(_GEOTRACE_TYPE, \
            **{"hint": "GPS coordinates can only be collected when outside."})

_INT_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: INT_XFORM
    }
}

_DECIMAL_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: DECIMAL_XFORM
    }
}

_STRING_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: STRING_XFORM
    }
}

_NOTE_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        "readonly": "true()", 
        TYPE: STRING_XFORM
    }
}

_TRIGGER_TYPE= {
    CONTROL: {
        "tag": TRIGGER_XFORM
    }, 
    BIND: {
        TYPE: STRING_XFORM
    }
}

_BARCODE_TYPE= {
    CONTROL: {
        "tag": "input"
    }, 
    BIND: {
        TYPE: BARCODE_XFORM
    }
}

_TODAY_TYPE= {
    BIND: {
        "jr:preload": DATE_XFORM, 
        TYPE: DATE_XFORM, 
        "jr:preloadParams": TODAY_XLSFORM
    }
}

_NONINPUT_STING_TYPE= {
    BIND: {
        TYPE: STRING_XFORM
    }
}

# XForm.
_START_TYPE= {
    BIND: {
        "jr:preload": "timestamp", 
        TYPE: DATETIME_XFORM, 
        "jr:preloadParams": START_XLSFORM
    }
}

# XForm.
_END_TYPE= {
    BIND: {
        "jr:preload": "timestamp", 
        TYPE: DATETIME_XFORM, 
        "jr:preloadParams": END_XLSFORM
    }
}

# XForm.
_DEVICEID_TYPE= {
    BIND: {
        "jr:preload": "property", 
        TYPE: STRING_XFORM, 
        "jr:preloadParams": DEVICEID_XLSFORM
    }
}

# XForm.
_EMAIL_TYPE= {
    BIND: {
        "jr:preload": "property", 
        TYPE: STRING_XFORM, 
        "jr:preloadParams": "email"
    }
}

# XForm.
_USERNAME_TYPE= {
    BIND: {
        "jr:preload": "property", 
        TYPE: STRING_XFORM, 
        "jr:preloadParams": "username"
    }
}

# XForm.
_PHONENUMBER_TYPE= {
    BIND: {
        "jr:preload": "property", 
        TYPE: STRING_XFORM, 
        "jr:preloadParams": PHONENUMBER_XLSFORM
    }
}

# XForm.
_SIMSERIAL_TYPE= {
    BIND: {
        "jr:preload": "property", 
        TYPE: STRING_XFORM, 
        "jr:preloadParams": SIMSERIAL_XLSFORM
    }
}

# XForm.
_SUBSCRIBERID_TYPE= {
    BIND: {
        "jr:preload": "property", 
        TYPE: STRING_XFORM, 
        "jr:preloadParams": SUBSCRIBERID_XLSFORM
    }
}

QUESTION_TYPE_DICT = \
{
    # FIXME: These seemingly could be condensed to one entry per question type if 'pyxform.aliases.select' were put to use.
    # Select one.
    SELECT_ONE:                               _SELECT_1_TYPE_DICT,
    "add " + SELECT_ONE + " prompt using":    _SELECT_1_TYPE_DICT, # Already in 'pyxform.aliases.select'.
    SELECT_ONE + " using":                    _SELECT_1_TYPE_DICT,
    "q " + SELECT_ONE_XFORM:                  _SELECT_1_TYPE_DICT,
    
    # Select multiple.
    SELECT_ALL_THAT_APPLY:                _SELECT_TYPE_DICT,  # Already in 'pyxform.aliases.select'.
    SELECT_ALL_THAT_APPLY + " from":      _SELECT_TYPE_DICT, # Already in 'pyxform.aliases.select'.
    "add select multiple prompt using":             _SELECT_TYPE_DICT, # Already in 'pyxform.aliases.select'.
    "select multiple from":                         _SELECT_TYPE_DICT,
    "q " + SELECT_ALL_THAT_APPLY_XFORM:   _SELECT_TYPE_DICT,
    "select multiple using":                        _SELECT_TYPE_DICT,
    
    "q picture":                                    _IMAGE_TYPE,
    "photo":                                        _IMAGE_TYPE,
    "q " + IMAGE_XLSFORM:                 _IMAGE_TYPE,
    "add " + IMAGE_XLSFORM + " prompt":   _IMAGE_TYPE,
    IMAGE_XLSFORM:                        _IMAGE_TYPE,
    
    "add date time prompt":     _DATETIME_TYPE,
    "q date time":              _DATETIME_TYPE,
    
    VIDEO_XLSFORM:                        _VIDEO_TYPE,
    "add " + VIDEO_XLSFORM + " prompt":   _VIDEO_TYPE,
    "q " + VIDEO_XLSFORM:                 _VIDEO_TYPE,
    
    "add " + AUDIO_XLSFORM + " prompt":   _AUDIO_TYPE,
    "q " + AUDIO_XLSFORM:                 _AUDIO_TYPE,
    AUDIO_XLSFORM:                        _AUDIO_TYPE,
    
    "add " + DATE_XFORM + " prompt":  _DATE_TYPE,
    "q " + DATE_XFORM:                _DATE_TYPE,
    DATE_XFORM:                       _DATE_TYPE,
    
    "datetime":                                     _DATETIME_TYPE, 
    DATETIME_XFORM:                       _DATETIME_TYPE, 
    "add " + DATETIME_XFORM + " prompt":  _DATETIME_TYPE, 
    "q " + DATETIME_XFORM:                _DATETIME_TYPE, 
    "date time":                                    _DATETIME_TYPE, 
    
    "q " + GEOPOINT_XFORM:    _GEOPOINT_TYPE,
    "location":                         _GEOPOINT_TYPE,
    "q location":                       _GEOPOINT_TYPE,
    "add location prompt":              _GEOPOINT_TYPE,
    
    GEOPOINT_XFORM:   _GEOPOINT_TYPE_W_HINT,
    "gps":                      _GEOPOINT_TYPE_W_HINT,
    
    "q " + GEOTRACE_XFORM:    _GEOTRACE_TYPE,
    
    GEOTRACE_XFORM:     _GEOTRACE_TYPE_W_HINT,
    
    "q " + GEOSHAPE_XFORM:    _GEOSHAPE_TYPE,
    
    GEOSHAPE_XFORM:   _GEOSHAPE_TYPE_W_HINT,

    INT_XLSFORM:                      _INT_TYPE,
    "q " + INT_XFORM:                 _INT_TYPE,
    INT_XFORM:                        _INT_TYPE,
    "add " + INT_XLSFORM + " prompt": _INT_TYPE,
    
    DECIMAL_XFORM:                        _DECIMAL_TYPE,
    "add " + DECIMAL_XFORM + " prompt":   _DECIMAL_TYPE,
    "q " + DECIMAL_XFORM:                 _DECIMAL_TYPE,
    
    STRING_XLSFORM:                       _STRING_TYPE,
    STRING_XFORM:                         _STRING_TYPE,
    "q " + STRING_XFORM:                  _STRING_TYPE,
    "select one external":                          _STRING_TYPE,
    "add " + STRING_XLSFORM + " prompt":  _STRING_TYPE,
    
    "add " + NOTE_XLSFORM + " prompt":    _NOTE_TYPE,
    "q " + NOTE_XLSFORM:                  _NOTE_TYPE,
    NOTE_XLSFORM:                         _NOTE_TYPE,

    "add " + TRIGGER_XLSFORM + " prompt": _TRIGGER_TYPE,
    TRIGGER_XLSFORM:                      _TRIGGER_TYPE,
    "q " + TRIGGER_XLSFORM:               _TRIGGER_TYPE,
    
    "add " + BARCODE_XFORM + " prompt":   _BARCODE_TYPE,
    "q " + BARCODE_XFORM:                 _BARCODE_TYPE,
    BARCODE_XFORM:                        _BARCODE_TYPE,

    PHONENUMBER_XLSFORM:  _PHONENUMBER_TYPE,
    "get phone number":             _PHONENUMBER_TYPE,
    
    START_XLSFORM:    _START_TYPE,
    "get start time":           _START_TYPE,
    
    "get end time":         _END_TYPE,
    "end time":             _END_TYPE,
    END_XLSFORM:  _END_TYPE,
    
    "get sim id":                   _SIMSERIAL_TYPE,
    SIMSERIAL_XLSFORM:    _SIMSERIAL_TYPE,
    "sim id":                       _SIMSERIAL_TYPE,
    
    "imei":                     _DEVICEID_TYPE,
    "device id":                _DEVICEID_TYPE,
    "get device id":            _DEVICEID_TYPE,
    DEVICEID_XLSFORM: _DEVICEID_TYPE,

    "subscriber id":                _SUBSCRIBERID_TYPE,
    SUBSCRIBERID_XLSFORM: _SUBSCRIBERID_TYPE,
    "get subscriber id":            _SUBSCRIBERID_TYPE,
    
    "get today":                _TODAY_TYPE,
    TODAY_XLSFORM:    _TODAY_TYPE,
    
    "start time":   _START_TYPE,
    
    CALCULATE_XFORM:                        _NONINPUT_STING_TYPE,
    "q " + CALCULATE_XFORM:                 _NONINPUT_STING_TYPE,
    "add " + CALCULATE_XFORM + " prompt":   _NONINPUT_STING_TYPE, 
    "hidden":                                           _NONINPUT_STING_TYPE,
    
    "username": _USERNAME_TYPE, 
    
    "email": _EMAIL_TYPE,
    
    "number of days in last month": {
        CONTROL: {
            "tag": "input"
        }, 
        BIND: {
            TYPE: INT_XFORM, 
            "constraint": "0 <= . and . <= 31"
        }, 
        "hint": "Enter a number 0-31."
    }, 
    TRIGGER_XFORM: {
        CONTROL: {
            "tag": TRIGGER_XFORM
        }
    }, 
    "percentage": {
        CONTROL: {
            "tag": "input"
        }, 
        BIND: {
            TYPE: INT_XFORM, 
            "constraint": "0 <= . and . <= 100"
        }
    }, 
    "number of days in last six months": {
        CONTROL: {
            "tag": "input"
        }, 
        BIND: {
            TYPE: INT_XFORM, 
            "constraint": "0 <= . and . <= 183"
        }, 
        "hint": "Enter a number 0-183."
    }, 
    "phone number": {
        CONTROL: {
            "tag": "input"
        }, 
        BIND: {
            TYPE: STRING_XFORM, 
            "constraint": "regex(., '^\\d*$')"
        }, 
        "hint": "Enter numbers only."
    }, 
    "number of days in last year": {
        CONTROL: {
            "tag": "input"
        }, 
        BIND: {
            TYPE: INT_XFORM, 
            "constraint": "0 <= . and . <= 365"
        }, 
        "hint": "Enter a number 0-365."
    }, 
    TIME_XFORM: {
        CONTROL: {
            "tag": "input"
        }, 
        BIND: {
            TYPE: TIME_XFORM
        }
    }, 
    "uri:" + SUBSCRIBERID_XLSFORM: {
        BIND: {
            "jr:preload": "property", 
            TYPE: STRING_XFORM, 
            "jr:preloadParams": "uri:" + SUBSCRIBERID_XLSFORM
        }
    },
    "uri:" + PHONENUMBER_XLSFORM: {
        BIND: {
            "jr:preload": "property", 
            TYPE: STRING_XFORM, 
            "jr:preloadParams": "uri:" + PHONENUMBER_XLSFORM
        }
    },
    "uri:" + SIMSERIAL_XLSFORM: {
        BIND: {
            "jr:preload": "property", 
            TYPE: STRING_XFORM, 
            "jr:preloadParams": "uri:" + SIMSERIAL_XLSFORM
        }
    },
    "uri:" + DEVICEID_XLSFORM: {
        BIND: {
            "jr:preload": "property", 
            TYPE: STRING_XFORM, 
            "jr:preloadParams": "uri:" + DEVICEID_XLSFORM
        }
    }, 
    "uri:username": {
        BIND: {
            "jr:preload": "property", 
            TYPE: STRING_XFORM, 
            "jr:preloadParams": "uri:username"
        }
    }, 
    "uri:email": {
        BIND: {
            "jr:preload": "property",
            TYPE: STRING_XFORM, 
            "jr:preloadParams": "uri:email"
        }
    },
}

#import os
#class QuestionTypeDictionary(dict):
#    """
#    A dictionary parsed from an xls file that defines question types.
#    """
#    def __init__(self, file_name="base"):
#        # Right now we're using an excel file to describe question
#        # types we will use in creating XForms, we'll switch over to
#        # json soon.
#        self._name = file_name
#        path_to_this_file = os.path.abspath(__file__)
#        path_to_this_dir = os.path.dirname(path_to_this_file)
#        path_to_question_types = os.path.join(
#            path_to_this_dir,
#            "question_types",
#            "%s.xls" % file_name
#            )
#        excel_reader = QuestionTypesReader(path_to_question_types)
#        for k, v in excel_reader.to_json_dict().iteritems():
#            self[k] = v
#
#    def get_definition(self, question_type_str):
#        return self.get(question_type_str, {})
#
#DEFAULT_QUESTION_TYPE_DICTIONARY = QuestionTypeDictionary("all")
