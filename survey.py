# Python standard library.
import re
import tempfile
import codecs
from datetime import datetime
from collections import defaultdict

# 'pyxform'-internal.
import pyxform.survey_to_xlsform
from section import Section
from question import Question
from utils import node
from odk_validate import check_xform
from survey_element import SurveyElement
from errors import PyXFormError
from pyxform import constants
import cStringIO


nsmap = {
    u"xmlns": u"http://www.w3.org/2002/xforms",
    u"xmlns:h": u"http://www.w3.org/1999/xhtml",
    u"xmlns:ev": u"http://www.w3.org/2001/xml-events",
    u"xmlns:xsd": u"http://www.w3.org/2001/XMLSchema",
    u"xmlns:jr": u"http://openrosa.org/javarosa",
    u"xmlns:orx": u"http://openrosa.org/xforms/"
    }

class Survey(Section):

    FIELDS = Section.FIELDS.copy()
    FIELDS.update(
        {
            u"_xpath": dict,
            u"_created": datetime.now, #This can't be dumped to json
            constants.TITLE: unicode,
            constants.ID_STRING: unicode,
            constants.SMS_KEYWORD: unicode,
            constants.SMS_SEPARATOR: unicode,
            constants.SMS_ALLOW_MEDIA: bool,
            constants.SMS_DATE_FORMAT: unicode,
            constants.SMS_DATETIME_FORMAT: unicode,
            constants.SMS_RESPONSE: unicode,
            u"file_name": unicode,
            constants.DEFAULT_LANGUAGE: unicode,
            u"_translations": dict,
            constants.SUBMISSION_URL: unicode,
            constants.PUBLIC_KEY: unicode,
            u"instance_xmlns": unicode,
            constants.VERSION: unicode,
            constants.CHOICES: dict,
            constants.STYLE: unicode
        }
    )
        

    def validate(self):
        super(Survey, self).validate()
        self._validate_uniqueness_of_section_names()

    def _validate_uniqueness_of_section_names(self):
        section_names = []
        for e in self.iter_descendants():
            if isinstance(e, Section):
                if e.name in section_names:
                    raise PyXFormError("There are two sections with the name %s." % e.name)
                section_names.append(e.name)

    def xml(self):
        """
        calls necessary preparation methods, then returns the xml.
        """
        self.validate()
        self._setup_xpath_dictionary()
        body_kwargs = {}
        if hasattr(self, constants.STYLE) and getattr(
                self, constants.STYLE):
            body_kwargs['class'] = getattr(
                self, constants.STYLE)
        return node(u"h:html",
                    node(u"h:head",
                         node(u"h:title", self.title),
                         self.xml_model()
                        ),
                    node(u"h:body", *self.xml_control(), **body_kwargs),
                    **nsmap
                    )

    def _generate_static_instances(self):
        """
        Generates <instance> elements for static data (e.g. choices for select type questions)
        """
        for list_name, choice_list in self.choices.items():
            instance_element_list = []
            for idx, choice in zip(range(len(choice_list)), choice_list):
                choice_element_list = []
                #Add a unique id to the choice element incase there is itext it refrences
                itextId = '-'.join(['static_instance', list_name, str(idx)])
                choice_element_list.append(node("itextId", itextId))

                for choicePropertyName, choicePropertyValue in choice.items():
                    if isinstance(choicePropertyValue, basestring) and choicePropertyName != 'label':
                        choice_element_list.append(node(choicePropertyName, unicode(choicePropertyValue)))
                instance_element_list.append(node("item", *choice_element_list))
            yield node("instance", node("root", *instance_element_list), id=list_name)

    def xml_model(self):
        """
        Generate the xform <model> element
        """
        self._setup_translations()
        self._setup_media()
        self._add_empty_translations()

        model_children = []
        if self._translations:
            model_children.append(self.itext())
        model_children += [node(constants.INSTANCE_XFORM, self.xml_instance())]
        model_children += list(self._generate_static_instances())
        model_children += self.xml_bindings()

        if self.submission_url or self.public_key:
            submission_attrs = dict()
            if self.submission_url:
                submission_attrs["action"] = self.submission_url
            if self.public_key:
                submission_attrs["base64RsaPublicKey"] = self.public_key
            submission_node = node("submission", method="form-data-post", **submission_attrs)
            model_children.insert(0, submission_node)
        return node(constants.MODEL_XFORM,  *model_children)

    def xml_instance(self):
        result = Section.xml_instance(self)
        result.setAttribute(u"id", self.id_string)

        #add instance xmlns attribute to the instance node
        if self.instance_xmlns:
            result.setAttribute(u"xmlns", self.instance_xmlns)

        if self.version:
            result.setAttribute(constants.VERSION, self.version)
        return result

    def _add_to_nested_dict(self, dicty, path, value):
        if len(path) == 1:
            dicty[path[0]] = value
            return
        if path[0] not in dicty:
            dicty[path[0]] = {}
        self._add_to_nested_dict(dicty[path[0]], path[1:], value)

    def _setup_translations(self):
        """
        set up the self._translations dict which will be referenced in the setup media and itext functions
        """
        self._translations = defaultdict(dict)
        for element in self.iter_descendants():
            for d in element.get_translations(self.default_language):
                self._translations[d['lang']][d['path']] = {"long" : d['text']}

        #This code sets up translations for choices in filtered selects.
        for list_name, choice_list in self.choices.items():
            for idx, choice in zip(range(len(choice_list)), choice_list):
                for choicePropertyName, choicePropertyValue in choice.items():
                    itextId = '-'.join(['static_instance', list_name, str(idx)])
                    if isinstance(choicePropertyValue, dict):
                        for mediatypeorlanguage, value in choicePropertyValue.items():
                            if isinstance(value, dict):
                                for langauge, value in value.items():
                                    self._add_to_nested_dict(self._translations, [langauge, itextId, mediatypeorlanguage], value)
                            else:
                                if choicePropertyName == 'media':
                                    self._add_to_nested_dict(self._translations, [self.default_language, itextId, mediatypeorlanguage], value)
                                else:
                                    self._add_to_nested_dict(self._translations, [mediatypeorlanguage, itextId, 'long'], value)
                    elif choicePropertyName == 'label':
                        self._add_to_nested_dict(self._translations, [self.default_language, itextId, 'long'], choicePropertyValue)

    def _add_empty_translations(self):
        """
        Adds translations so that every itext element has the same elements accross every language.
        When translations are not provided "-" will be used.
        This disables any of the default_language fallback functionality.
        """
        paths = {}
        for lang, translation in self._translations.items():
            for path, content in translation.items():
                paths[path] = paths.get(path, set()).union(content.keys())

        for lang, translation in self._translations.items():
            for path, content_types in paths.items():
                if path not in self._translations[lang]:
                    self._translations[lang][path] = {}
                for content_type in content_types:
                    if content_type not in self._translations[lang][path]:
                        self._translations[lang][path][content_type] = u"-"

    def _setup_media(self):
        """
        Traverse the survey, find all the media, and put in into the _translations data structure which looks like this:
        {language : {element_xpath : {media_type : media}}}
        It matches the xform nesting order.
        """
        if not self._translations:
            self._translations = defaultdict(dict)

        for survey_element in self.iter_descendants():

            translation_key = survey_element.get_xpath() + ":label"
            media_dict = survey_element.get(u"media")

            for media_type, possibly_localized_media in media_dict.items():

                if media_type not in SurveyElement.SUPPORTED_MEDIA:
                    raise PyXFormError("Media type: " + media_type + " not supported")

                localized_media = dict()

                if type(possibly_localized_media) is dict:
                    #media is localized
                    localized_media = possibly_localized_media
                else:
                    #media is not localized so create a localized version using the default language
                    localized_media = { self.default_language : possibly_localized_media }

                for language, media in localized_media.items():

                    #Create the required dictionaries in _translations, then add media as a leaf value:

                    if language not in self._translations:
                        self._translations[language] = {}

                    translations_language = self._translations[language]

                    if translation_key not in translations_language:
                        translations_language[translation_key] = {}

                    #if type(translations_language[translation_key]) is not dict:
                    #    translations_language[translation_key] = {"long" : translations_language[translation_key]}

                    translations_trans_key = translations_language[translation_key]

                    if media_type not in translations_trans_key:
                            translations_trans_key[media_type] = {}

                    translations_trans_key[media_type] = media

    def itext(self):
        """
        This function creates the survey's itext nodes from _translations
        @see _setup_media _setup_translations
        itext nodes are localized images/audio/video/text
        @see http://code.google.com/p/opendatakit/wiki/XFormDesignGuidelines
        """
        result = []
        for lang, translation in self._translations.items():
            if lang == self.default_language:
                result.append(node("translation", lang=lang, default=u"true()"))
                #result.append(node("translation", lang=lang))
            else:
                result.append(node("translation", lang=lang))

            for label_name, content in translation.items():
                itext_nodes = []
                label_type = label_name.partition(":")[-1]

                if type(content) is not dict: raise Exception()

                for media_type, media_value in content.items():

                    #There is a odk/jr bug where hints can't have a value for the "form" attribute.
                    #This is my workaround.
                    if label_type == u"hint":
                        value, outputInserted = self.insert_output_values(media_value)
                        itext_nodes.append(node("value", value, toParseString=outputInserted))
                        continue

                    if media_type == "long":
                        value, outputInserted = self.insert_output_values(media_value)
                        #I'm ignoring long types for now because I don't know how they are supposed to work.
                        #itext_nodes.append(node("value", value, form=media_type, toParseString=outputInserted))
                        itext_nodes.append(node("value", value, toParseString=outputInserted))
                    elif media_type == "image":
#                        itext_nodes.append(node("value", "jr://images/" + media_value, form=media_type))
                        value, outputInserted = self.insert_output_values(media_value)
                        itext_nodes.append(node("value", "jr://images/" + value, form=media_type, toParseString=outputInserted))
                    else:
#                        itext_nodes.append(node("value", "jr://" + media_type + "/" + media_value, form=media_type))
                        value, outputInserted = self.insert_output_values(media_value)
                        itext_nodes.append(node("value", "jr://" + media_type + "/" + value, form=media_type, toParseString=outputInserted))


                result[-1].appendChild(node("text", *itext_nodes, id=label_name))

        return node("itext", *result)

    def date_stamp(self):
        return self._created.strftime("%Y_%m_%d")

    def _to_pretty_xml(self):
        """
        I want the to_xml method to by default validate the xml we are
        producing.
        """
        # Hacky way of pretty printing xml without adding extra white
        # space to text
        # TODO: check out pyxml
        # http://ronrothman.com/public/leftbraned/xml-dom-minidom-toprettyxml-and-silly-whitespace/
        xml_with_linebreaks = self.xml().toprettyxml(indent='  ')
        text_re = re.compile('>\n\s+([^<>\s].*?)\n\s+</', re.DOTALL)
        output_re = re.compile('\n.*(<output.*>)\n(  )*')
        prettyXml = text_re.sub('>\g<1></', xml_with_linebreaks)
        inlineOutput = output_re.sub('\g<1>', prettyXml)
        inlineOutput = re.compile('<label>\s*\n*\s*\n*\s*</label>').sub('<label></label>', inlineOutput)
        return '<?xml version="1.0"?>\n' + inlineOutput

    def __unicode__(self):
        return "<survey name='%s' element_count='%s'>" % (self.name, len(self.children))

    def _setup_xpath_dictionary(self):
        self._xpath = {}
        for element in self.iter_descendants():
            if isinstance(element, Question) or isinstance(element, Section):
                if element.name in self._xpath:
                    self._xpath[element.name] = None
                else:
                    self._xpath[element.name] = element.get_xpath()

    def _var_repl_function(self, matchobj):
        """
        Given a dictionary of xpaths, return a function we can use to
        replace ${varname} with the xpath to varname.
        """
        name = matchobj.group(1)
        intro = "There has been a problem trying to replace ${%s} with the XPath to the survey element named '%s'." % (name, name)
        if name not in self._xpath:
            raise PyXFormError(intro + " There is no survey element with this name.")
        if self._xpath[name] is None:
            raise PyXFormError(intro + " There are multiple survey elements with this name.")
        return " " + self._xpath[name] + " "


    def insert_xpaths(self, text):
        """
        Replace all instances of ${var} with the xpath to var.
        """
        #bracketed_tag = r"\$\{(" + XFORM_TAG_REGEXP + r")\}"
        bracketed_tag = r"\$\{(.*?)\}"
        return re.sub(bracketed_tag, self._var_repl_function, unicode(text))

    def _var_repl_output_function(self,matchobj):
        """
        A regex substitution function that will replace
        ${varname} with an output element that has the xpath to varname.
        """
#        if matchobj.group(1) not in self._xpath:
#            raise PyXFormError("There is no survey element with this name.",
#                            matchobj.group(1))
        return '<output value="' + self._var_repl_function(matchobj) + '" />'

    def insert_output_values(self, text):
        """
        Replace all the ${variables} in text with xpaths.
        Returns that and a boolean indicating if there were any ${variables} present.
        """
        #There was a bug where escaping is completely turned off in labels where
        #variable replacement is used.
        #For exampke, `${name} < 3` causes an error but `< 3` does not.
        #This is my hacky fix for it, which does string escaping prior to variable replacement:
        from xml.dom.minidom import Text
        text_node = Text()
        text_node.data = text
        xml_text = text_node.toxml()

        bracketed_tag = r"\$\{(.*?)\}"
        # need to make sure we have reason to replace
        # since at this point < is &lt,
        # the net effect &lt gets translated again to &amp;lt;
        if unicode(xml_text).find('{') != -1:
            result = re.sub(
                bracketed_tag, self._var_repl_output_function,
                unicode(xml_text))
            return result, not result == xml_text
        return text, False

    def print_xform_to_file(self, path=None, validate=True, warnings=None):
        """
        Print the xForm to a file and optionally validate it as well by throwing exceptions
        and adding warnings to the warnings array.
        """
        if warnings is None:
            warnings = []
        if not path:
            path = self._print_name + ".xml"
        print path
        fp = codecs.open(path, mode="w", encoding="utf-8")
        fp.write(self._to_pretty_xml())
        fp.close()
        if validate:
            warnings.extend(check_xform(path))

    def temporaryFilename(self, prefix=None, suffix='tmp', dir=None, text=False, removeOnExit=False):
        import os
        import atexit
        """Returns a temporary filename that, like mkstemp(3), will be secure in
        its creation.  The file will be closed immediately after it's created, so
        you are expected to open it afterwards to do what you wish.  The file
        will be removed on exit unless you pass removeOnExit=False.  (You'd think
        that amongst the myriad of methods in the tempfile module, there'd be
        something like this, right?  Nope.)"""

        if prefix is None:
            prefix = "%s_%d_" % (os.path.basename(sys.argv[0]), os.getpid())

        (fileHandle, path) = tempfile.mkstemp(prefix=prefix, suffix=suffix, dir=dir, text=text)
        os.close(fileHandle)

        def removeFile(path):
            os.remove(path)
            logging.debug('temporaryFilename: rm -f %s' % path)

        if removeOnExit:
            atexit.register(removeFile, path)

        return path

    def to_xml(self, validate=True, warnings=None):
        # with tempfile.NamedTemporaryFile() as tmp:
            # this will throw an exception if the xml is not valid
        # tmp = tempfile.NamedTemporaryFile(mode='w')
        path = self.temporaryFilename(prefix='', suffix='')
        self.print_xform_to_file(path=path, validate=validate, warnings=warnings)
        return self._to_pretty_xml()

    def instantiate(self):
        """
        Instantiate as in return a instance of SurveyInstance for collected data.
        """
        from instance import SurveyInstance
        return SurveyInstance(self)


    def to_xform(self, path=None, warnings=None):
        '''
        Convert the survey to a XML XForm.
        
        :param str path: Optional filesystem path to the desired output file.
        :param list warnings: Optional list into which any warnings generated during export will be appended.
        :returns: If the 'path' parameter was omitted, nothing. Otherwise, a buffer containing the exported form.
        :rtype: NoneType or 'cStringIO.StringIO'
        '''
        
        if path:
            self.print_xform_to_file(path, warnings=warnings)
        else:
            return cStringIO.StringIO(self.to_xml(warnings=warnings))


    def to_xls(self, path=None, warnings=None):
        '''
        Wrapper around 'pyxform.survey_to_xlsform.to_xls'; see that function for 
        documentation.
        '''
        
        return pyxform.survey_to_xlsform.to_xls(self, path, warnings=warnings)


    def to_csv(self, path=None, warnings=None, koboform=False):
        '''
        Wrapper around 'pyxform.survey_to_xlsform.to_csv'; see that function for 
        documentation.
        '''
        
        return pyxform.survey_to_xlsform.to_csv(self, path, warnings=warnings, koboform=koboform)


    def to_ssjson(self, path=None, warnings=None):
        '''
        Wrapper around 'pyxform.survey_to_xlsform.to_ssjson'; see that function for 
        documentation.
        '''
        
        return pyxform.survey_to_xlsform.to_ssjson(self, path, warnings=warnings)
