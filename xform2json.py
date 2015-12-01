from __future__ import absolute_import

import os
import re
import json
import copy
import codecs
from operator import itemgetter

from lxml import etree
from lxml.etree import ElementTree

from . import aliases
from . import constants
from . import builder
from .errors import PyXFormError


# XForm import warnings.
NONCONFORMANCE_WARNING= 'This XForm is not conformant to the standard. Please refer to the specification document at http://opendatakit.github.io/odk-xform-spec/'
TYPE_DEPRECATION_WARNING_TEMPLATE= 'Use of question type "{}" in XForms is deprecated. Please use "{}" instead.'
# TODO: Validate XForm importing and remove this.
XFORM_IMPORT_WARNING= 'XForm imports are not fully supported. Please check the correctness of the resulting survey.'

## {{{ http://code.activestate.com/recipes/573463/ (r7)
class XmlDictObject(dict):
    """
    Adds object like functionality to the standard dictionary.
    """

    def __init__(self, initdict=None):
        if initdict is None:
            initdict = {}
        dict.__init__(self, initdict)

    def __getattr__(self, item):
        return self.__getitem__(item)

    def __setattr__(self, item, value):
        self.__setitem__(item, value)

    def __str__(self):
        if '_text' in self:
            return self.__getitem__('_text')
        else:
            return ''

    @staticmethod
    def Wrap(x):
        """
        Static method to wrap a dictionary recursively as an XmlDictObject
        """

        if isinstance(x, dict):
            return XmlDictObject(
                (k, XmlDictObject.Wrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject.Wrap(v) for v in x]
        else:
            return x

    @staticmethod
    def _UnWrap(x):
        if isinstance(x, dict):
            return dict(
                (k, XmlDictObject._UnWrap(v)) for (k, v) in x.iteritems())
        elif isinstance(x, list):
            return [XmlDictObject._UnWrap(v) for v in x]
        else:
            return x

    def UnWrap(self):
        """
        Recursively converts an XmlDictObject to a standard dictionary
        and returns the result.
        """

        return XmlDictObject._UnWrap(self)


def _ConvertDictToXmlRecurse(parent, dictitem):
    assert not isinstance(dictitem, list)

    if isinstance(dictitem, dict):
        for (tag, child) in dictitem.iteritems():
            if str(tag) == '_text':
                parent.text = str(child)
            elif isinstance(child, list):
                # iterate through the array and convert
                for listchild in child:
                    elem = ElementTree.Element(tag)
                    parent.append(elem)
                    _ConvertDictToXmlRecurse(elem, listchild)
            else:
                elem = ElementTree.Element(tag)
                parent.append(elem)
                _ConvertDictToXmlRecurse(elem, child)
    else:
        parent.text = str(dictitem)


def ConvertDictToXml(xmldict):
    """
    Converts a dictionary to an XML ElementTree Element
    """

    roottag = xmldict.keys()[0]
    root = ElementTree.Element(roottag)
    _ConvertDictToXmlRecurse(root, xmldict[roottag])
    return root


def _ConvertXmlToDictRecurse(node, dictclass):
    nodedict = dictclass()

    if len(node.items()) > 0:
        # if we have attributes, set them
        nodedict.update(dict(node.items()))

    for child in node:
        # recursively add the element's children
        newitem = _ConvertXmlToDictRecurse(child, dictclass)
        # if tag in between text node, capture the tail end
        if child.tail is not None and child.tail.strip() != '':
            newitem['tail'] = child.tail
        if child.tag in nodedict:
            # found duplicate tag, force a list
            if isinstance(nodedict[child.tag], list):
                # append to existing list
                nodedict[child.tag].append(newitem)
            else:
                # convert to list
                nodedict[child.tag] = [nodedict[child.tag], newitem]
        else:
            # only one, directly set the dictionary
            nodedict[child.tag] = newitem

    if node.text is None:
        text = ''
    else:
        text = node.text.strip()

    if len(nodedict) > 0:
        # if we have a dictionary
        # add the text as a dictionary value (if there is any)
        if len(text) > 0:
            nodedict['_text'] = text
    else:
        # if we don't have child nodes or attributes, just set the text
        nodedict = text

    return nodedict


def ConvertXmlToDict(root, dictclass=XmlDictObject):
    """
    Converts an XML file or ElementTree Element to a dictionary
    """

    # If a string is passed in, try to open it as a file
    if isinstance(root, basestring):
        if os.path.exists(root):
            root = etree.parse(root).getroot()
        else:
            root = etree.fromstring(root)
    elif not isinstance(root, etree._Element):
        raise TypeError('Expected ElementTree.Element or file path string')

    return dictclass({root.tag: _ConvertXmlToDictRecurse(root, dictclass)})
## end of http://code.activestate.com/recipes/573463/ }}}


def create_survey_element_from_xml(xml_file):
    sb = XFormToDictBuilder(xml_file)
    return sb.survey()


class XFormToDictBuilder:
    '''Experimental XFORM xml to XFORM JSON'''
    QUESTION_TYPES = {
        constants.SELECT_ALL_THAT_APPLY_XFORM: constants.SELECT_ALL_THAT_APPLY,
        constants.SELECT_ONE_XFORM: constants.SELECT_ONE,
        constants.INT_XFORM: constants.INT_XLSFORM,
        constants.DATETIME_XFORM: constants.DATETIME_XFORM,
        constants.STRING_XFORM: constants.STRING_XFORM
    }

    def __init__(self, path=None, filelike_obj=None, warnings=None):
        if path:
            assert os.path.isfile(path)
            with open(path) as f:
                doc_as_dict= self.get_dict_from_xml(f)
        elif filelike_obj:
            doc_as_dict= self.get_dict_from_xml(filelike_obj)
        else:
            raise RuntimeError('\'XFormToDictBuilder()\' requires either the '\
                               + '\'path\' or the \'filelike_obj\' parameter.')
        
        # TODO: Implement warnings for partially/un-supported form elements.
        if isinstance(warnings, list):
            self.warnings= warnings
        else:
            self.warnings= list()
        self.warnings.append(XFORM_IMPORT_WARNING)

        assert 'html' in doc_as_dict
        assert 'body' in doc_as_dict['html']
        assert 'head' in doc_as_dict['html']
        assert constants.MODEL_XFORM in doc_as_dict['html']['head']
        assert constants.TITLE in doc_as_dict['html']['head']
        assert constants.BIND in doc_as_dict['html']['head'][constants.MODEL_XFORM]

        self.body = doc_as_dict['html']['body']
        self.model = doc_as_dict['html']['head'][constants.MODEL_XFORM]
        self.bindings = copy.deepcopy(self.model[constants.BIND])
        if isinstance(self.bindings, dict):
            self.bindings= [self.bindings]
        self._bind_list = copy.deepcopy(self.bindings)
        self.title = doc_as_dict['html']['head'][constants.TITLE]
        # FIXME: Brittle workaround for titles with translations that also provide default text (old KF).
        if isinstance(self.title, dict):
            self.title= self.title['_text']
        self.new_doc = {
            constants.TYPE: constants.SURVEY,
            constants.TITLE: self.title,
            constants.CHILDREN: [],
            constants.ID_STRING: self.title,
            constants.SMS_KEYWORD: self.title,
            constants.DEFAULT_LANGUAGE: "default",
        }
        self._set_submission_info()
        self._set_survey_name()
        self.children = []
        self.ordered_binding_refs = []
        self._set_binding_order()

        # set self.translations
        self._set_translations()

        for body_element_tag, body_element in self.body.iteritems():
            if isinstance(body_element, dict):
                self.children.append(
                        self._get_question_from_object(body_element, \
                                element_tag=body_element_tag))
            elif isinstance(body_element, list):
                for sub_element in body_element:
                    self.children.append(
                        self._get_question_from_object(sub_element, \
                                element_tag=body_element_tag))
        self._cleanup_bind_list()
        self._cleanup_children()
        self.new_doc[constants.CHILDREN] = self.children


    @staticmethod
    def get_dict_from_xml(xml_file_object):
        parser = etree.XMLParser(remove_comments=True)
        xml_root= etree.parse(xml_file_object, parser=parser).getroot()
        xml_dict= ConvertXmlToDict(xml_root)
        
        json_str = json.dumps(xml_dict)
        for k in xml_root.nsmap:
            json_str = json_str.replace('{%s}' % xml_root.nsmap[k], '')
        return json.loads(json_str)


    def _set_binding_order(self):
        self.ordered_binding_refs = []
        for bind in self.bindings:
            self.ordered_binding_refs.append(bind[constants.NODESET_XFORM])

    def _set_survey_name(self):
        obj = self.bindings[0]
        name = obj[constants.NODESET_XFORM].split('/')[1]
        self.new_doc[constants.NAME] = name
        
        # If there are multiple 'instance' elements, get the primary.
        if not isinstance(self.model[constants.INSTANCE_XFORM], dict):
            for i in self.model[constants.INSTANCE_XFORM]:
                # See http://opendatakit.github.io/odk-xform-spec/#primary-instance.
                # TODO: Check child for 'id' attribute too?
                if len(i) == 1:
                    primary_instance= i
        else:
            primary_instance= self.model[constants.INSTANCE_XFORM]
        self.new_doc[constants.ID_STRING] = primary_instance[name]['id']

    def _set_submission_info(self):
        if 'submission' in self.model:
            submission = self.model['submission']
            if 'action' in submission:
                self.new_doc[constants.SUBMISSION_URL] = submission['action']
            if 'base64RsaPublicKey' in submission:
                self.new_doc[constants.PUBLIC_KEY] = submission['base64RsaPublicKey']

    def _cleanup_children(self):
        def remove_refs(children):
            for child in children:
                if isinstance(child, dict):
                    if constants.NODESET_XFORM in child:
                        del child[constants.NODESET_XFORM]
                    if constants.REF_XFORM in child:
                        del child[constants.REF_XFORM]
                    if '__order' in child:
                        del child['__order']
                    if constants.CHILDREN in child:
                        remove_refs(child[constants.CHILDREN])

        # do some ordering, order is specified by bindings
        def order_children(children):
            if isinstance(children, list):
                try:
                    children.sort(key=itemgetter('__order'))
                except KeyError:
                    pass
                for child in children:
                    if isinstance(child, dict) and 'children' in child:
                        order_children(child['children'])
        order_children(self.children)
        remove_refs(self.children)

    def _cleanup_bind_list(self):
        for bndng in self._bind_list:
            ref = bndng['nodeset']
            name = self._get_name_from_ref(ref)
            parent_ref = ref[:ref.find('/%s' % name)]
            question = self._get_question_params_from_bindings(ref)
            question[constants.NAME] = name
            question['__order'] = self._get_question_order(ref)
            if 'calculate' in bndng:
                question['type'] = 'calculate'
            if ref.split('/').__len__() == 3:
                # just append on root node, has no group
                question['ref'] = ref
                self.children.append(question)
                continue
            for child in self.children:
                if child['ref'] == parent_ref:
                    question['ref'] = ref
                    updated = False
                    for c in child['children']:
                        if isinstance(c, dict) \
                                and 'ref' in c and c['ref'] == ref:
                            c.update(question)
                            updated = True
                    if not updated:
                        child['children'].append(question)
            if 'ref' not in question:
                new_ref = u'/'.join(ref.split('/')[2:])
                root_ref = u'/'.join(ref.split('/')[:2])
                question_or_choice = self._get_item_func(root_ref, new_ref, bndng)
                if 'type' not in question_or_choice and 'type' in question:
                    question_or_choice.update(question)
                if question_or_choice['type'] == 'group' and question_or_choice[constants.NAME] == 'meta':
                    question_or_choice['control'] = {'bodyless': True}
                    question_or_choice['__order'] = self._get_question_order(ref)
                self.children.append(question_or_choice)
                self._bind_list.append(bndng)
                break
        if self._bind_list:
            self._cleanup_bind_list()

    def _get_item_func(self, ref, name, item):
        rs = {}
        name_splits = name.split('/')
        rs[constants.NAME] = name_splits[0]
        ref = '%s/%s' % (ref, rs[constants.NAME])
        rs['ref'] = ref
        if name_splits.__len__() > 1:
            rs['type'] = 'group'
            rs['children'] = [
                self._get_item_func(ref, '/'.join(name_splits[1:]), item)]
        return rs

    def survey(self):
        new_doc = json.dumps(self.new_doc)
        _survey = builder.create_survey_element_from_json(new_doc)
        return _survey

    def _get_question_order(self, ref):
        try:
            return self.ordered_binding_refs.index(ref)
        except ValueError:
            # likely a group
            for i in self.ordered_binding_refs:
                if i.startswith(ref):
                    return self.ordered_binding_refs.index(i) + 1
            return self.ordered_binding_refs.__len__() + 1

    def _get_question_from_object(self, obj, element_tag=None):

        if 'ref' in obj:
            ref = obj['ref']
        elif 'nodeset' in obj:
            ref = obj['nodeset']
        # Look for the 'nodeset' in this question's associated 'bind'.
        elif any( (True for binding in self.bindings if binding['id'] == obj[constants.BIND]) ):
            associated_binding= [binding for binding in self.bindings if binding['id'] == obj[constants.BIND]][0]
            ref= associated_binding[constants.NODESET_XFORM]
        else:
            raise TypeError('cannot find "ref" or "nodeset" in {} or associated bind {}'.format(repr(obj), associated_binding))
        
        question = {'ref': ref, '__order': self._get_question_order(ref)}
        question[constants.NAME] = self._get_name_from_ref(ref)
        if 'hint' in obj:
            k, v = self._get_label(obj['hint'], 'hint')
            question[k] = v
        if 'label' in obj:
            k, v = self._get_label(obj['label'])
            if isinstance(v, dict) and 'label' in v.keys() \
                    and 'media' in v.keys():
                for _k, _v in v.iteritems():
                    question[_k] = _v
            else:
                question[k] = v
        if 'autoplay' in obj or 'appearance' in obj \
                or 'count' in obj or 'rows' in obj:
            question['control'] = {}
        if 'appearance' in obj:
            question["control"].update({'appearance': obj['appearance']})
        if 'rows' in obj:
            question['control'].update({'rows': obj['rows']})
        if 'autoplay' in obj:
            question['control'].update({'autoplay': obj['autoplay']})
        question_params = self._get_question_params_from_bindings(ref)
        if isinstance(question_params, dict):
            for k, v in question_params.iteritems():
                question[k] = v
        # has to come after the above block
        if 'mediatype' in obj:
            question['type'] = obj['mediatype'].replace('/*', '')
        if 'item' in obj:
            children = []
            item_list= [obj['item']] if isinstance(obj['item'], dict) else obj['item']
            for itm in item_list:
                if isinstance(itm, dict) and\
                        'label' in itm.keys() and 'value' in itm.keys():
                    k, v = self._get_label(itm['label'])
                    children.append(
                        {constants.NAME: itm['value'], k: v})
            question['children'] = children
        
        if obj.get(constants.ITEMSET_XFORM):
            question[constants.ITEMSET_XFORM]= obj[constants.ITEMSET_XFORM]
        
        # Warn if the question type isn't conformant to the XForm spec.
        # TODO: Calculations?
        if (element_tag != constants.GROUP) \
          and (element_tag not in constants.XFORM_TYPE_BODY_ELEMENTS):
            # Not an XForm type.
            
            # Try to get the dealiased question type from the XML element tag.
            dealiased_tag= None
            try:
                dealiased_tag= aliases.get_xform_question_type(element_tag)
            except PyXFormError:
                pass
            
            if dealiased_tag in constants.XFORM_TYPE_BODY_ELEMENTS:
                original_type= element_tag
                dealiased_type= dealiased_tag

                # Include warnings only once.
                if NONCONFORMANCE_WARNING not in self.warnings:
                    self.warnings.append(NONCONFORMANCE_WARNING)
                
                type_deprecation_warning= TYPE_DEPRECATION_WARNING_TEMPLATE.format(original_type, dealiased_type)
                if type_deprecation_warning not in self.warnings:
                    self.warnings.append(type_deprecation_warning)
        
        # Record the question type.
        if question.get('type', '').startswith('xsd:'):
            # When encountering types prefixed with 'xsd:', remove the prefix \
            #   and see if the element_tag defined in the form body should be used.
            question['type']= question['type'].split('xsd:')[-1]
            if element_tag != 'input':
                question_type= element_tag
            else:
                question_type= question['type']
        elif 'type' in question:
            question_type= question['type']
        else:
            question_type= element_tag
        # Form notes.
        if question_type == 'text' and constants.BIND in question \
                and 'readonly' in question[constants.BIND]:
            question_type = question['type'] = 'note'
            # Remove the 'readonly' field of the 'bind' and remove it altogether if now empty.
            del question[constants.BIND]['readonly']
            if len(question[constants.BIND].keys()) == 0:
                del question[constants.BIND]
        if question_type in ['group', 'repeat']:
            if question_type == 'group' and 'repeat' in obj:
                question['children'] = \
                    self._get_children_questions(obj['repeat'])
                question_type = 'repeat'
                if 'count' in obj['repeat']:
                    if 'control' not in question:
                        question['control'] = {}
                    question['control'].update(
                        {'jr:count':
                            self._shorten_xpaths_in_string(
                                obj['repeat']['count'].strip())})
            else:
                # A question group that is not repeated (?).
                question['children'] = self._get_children_questions(obj)
        if element_tag == constants.TRIGGER_XFORM:
            question_type = constants.TRIGGER_XLSFORM
        if question_type == 'geopoint' and 'hint' in question:
            del question['hint']
        
        # Denote multiple choice questions as prescribed by xlsform.org.
        if (question_type in aliases.multiple_choice):
            if  aliases.multiple_choice[question_type] == constants.SELECT_ONE:
                question_type= constants.SELECT_ONE_XLSFORM
            elif aliases.multiple_choice[question_type] == constants.SELECT_ALL_THAT_APPLY:
                question_type= constants.SELECT_ALL_THAT_APPLY_XLSFORM
        
        if question_type:
            question['type'] = question_type
            
        return question

    def _get_children_questions(self, obj):
        children = []
        for k, v in obj.iteritems():
            if k in ['ref', 'label', 'nodeset']:
                continue
            if isinstance(v, dict):
                child = self._get_question_from_object(v, element_tag=k)
                children.append(child)
            elif isinstance(v, list):
                for i in v:
                    child = self._get_question_from_object(i, element_tag=k)
                    children.append(child)
        return children


    def _get_question_params_from_bindings(self, ref):
        
        # Locate the binding for this form element.
        for b in self.bindings:
            if b[constants.NODESET_XFORM] == ref:
                associated_binding= b
                break
        else:
            # No associated binding found.
            return
        
        try:
            self._bind_list.remove(associated_binding)
        except ValueError:
            pass
        
        # Create a copy of the binding to mutate and record.
        binding_copy= copy.deepcopy(associated_binding)
        
        # Create a sub-binding into which some attributes will be nested (why?).
        binding_copy[constants.BIND]= binding_copy.get(constants.BIND, {})
        sub_binding= binding_copy[constants.BIND]
        
        # Don't record the "nodeset" attribute.
        del binding_copy[constants.NODESET_XFORM]

        # Manually nest some attributes within a 'bind' attribute.        
        # Also manually mangle the XPath values of some of those attributes (why?).
        # Also manually override the names of some of those attributes (why?).
        nest_attributes= ['relevant', 'required', 'constraint',
                     'constraintMsg', 'readonly', 'calculate',
                    'noAppErrorString', 'requiredMsg']
        xpath_mangle_attributes= ['constraint', 'relevant', 'calculate']
        rename_attributes= ['noAppErrorString', 'requiredMsg', 'constraintMsg']
        for attrbt in nest_attributes:
            if attrbt in binding_copy:
                # Remove and nest the attribute.
                sub_binding[attrbt]= binding_copy.pop(attrbt)

                if attrbt in xpath_mangle_attributes:
                    # Mangle the attribute's XPath value.
                    sub_binding[attrbt]= self._shorten_xpaths_in_string(sub_binding[attrbt])

                if attrbt in rename_attributes:
                    # Remove the attribute and reinsert with 'jr:' prepended to the name.
                    sub_binding['jr:' + attrbt]= sub_binding.pop(attrbt)                

        # Manually override some attribute values (why?).
        if constants.TYPE in binding_copy:
            
            original_type= binding_copy[constants.TYPE]
            dealiased_type= aliases.get_xform_question_type(original_type)
            if original_type != dealiased_type:
                # Complain (once) about non-standard types before they are mangled.
                if NONCONFORMANCE_WARNING not in self.warnings:
                    self.warnings.append(NONCONFORMANCE_WARNING)
                type_deprecation_warning= TYPE_DEPRECATION_WARNING_TEMPLATE.format(original_type, dealiased_type)
                if type_deprecation_warning not in self.warnings:
                    self.warnings.append(type_deprecation_warning)
                
            binding_copy[constants.TYPE]= self._get_question_type(original_type)

        if 'preloadParams' in binding_copy and 'preload' in binding_copy:
            binding_copy['type'] = binding_copy['preloadParams']
            del binding_copy['preloadParams']
            del binding_copy['preload']

        if 'jr:constraintMsg' in sub_binding:
            sub_binding['jr:constraintMsg']= self._get_constraintMsg(sub_binding['jr:constraintMsg'])
        if constants.REQUIRED_XFORM in sub_binding:
            if sub_binding[constants.REQUIRED_XFORM] == 'true()':
                sub_binding[constants.REQUIRED_XFORM] = 'yes'
            elif sub_binding[constants.REQUIRED_XFORM] == 'false()':
                sub_binding[constants.REQUIRED_XFORM] = 'no'

        return binding_copy


    def _get_question_type(self, type):
        if type in self.QUESTION_TYPES.keys():
            return self.QUESTION_TYPES[type]
        return type

    def _set_translations(self):
        if 'itext' not in self.model:
            self.translations = []
            return
        assert 'translation' in self.model['itext']
        self.translations = self.model['itext']['translation']
        if isinstance(self.translations, dict):
            self.translations = [self.translations]
        assert 'text' in self.translations[0]
        assert 'lang' in self.translations[0]

    def _get_label(self, label_obj, key='label'):
        if isinstance(label_obj, dict):
            try:
                ref = label_obj['ref'].replace(
                    'jr:itext(\'', '').replace('\')', '')
            except KeyError:
                return key, self._get_output_text(label_obj)
            else:
                return self._get_text_from_translation(ref, key)
        return key, label_obj

    def _get_output_text(self, value):
        text = ''
        if 'output' in value and '_text' in value:
            v = [value['_text']]
            v.append(self._get_bracketed_name(
                value['output']['value']))
            text = u' '.join(v)
            if 'tail' in value['output']:
                text = u''.join(
                    [text, value['output']['tail']])
        elif 'output' in value and '_text' not in value:
            text = self._get_bracketed_name(
                value['output']['value'])
        else:
            return value
        return text

    def _get_text_from_translation(self, ref, key='label'):
        label = {}
        for translation in self.translations:
            lang = translation['lang']
            label_list = translation['text']
            for l in label_list:
                if l['value'] == '-':  # skip blank label
                    continue
                if l['id'] == ref:
                    text = value = l['value']
                    if isinstance(value, dict):
                        if 'output' in value:
                            text = self._get_output_text(value)
                        if 'form' in value and '_text' in value:
                            key = u'media'
                            v = value['_text']
                            if value['form'] == 'image':
                                v = v.replace('jr://images/', '')
                            else:
                                v = v.replace('jr://%s/' % value['form'], '')
                            if v == '-':  # skip blank
                                continue
                            text = {value['form']: v}
                    if isinstance(value, list):
                        for item in value:
                            if 'form' in item and '_text' in item:
                                k = u'media'
                                m_type = item['form']
                                v = item['_text']
                                if m_type == 'image':
                                    v = v.replace('jr://images/', '')
                                else:
                                    v = v.replace('jr://%s/' % m_type, '')
                                if v == '-':
                                    continue
                                if k not in label:
                                    label[k] = {}
                                if m_type not in label[k]:
                                    label[k][m_type] = {}
                                label[k][m_type][lang] = v
                                continue
                            if isinstance(item, basestring):
                                if item == '-':
                                    continue
                            if 'label' not in label:
                                label['label'] = {}
                            label['label'][lang] = item
                        continue

                    label[lang] = text
                    break
        if key == u'media' and label.keys() == ['default']:
            label = label['default']
        return key, label

    def _get_bracketed_name(self, ref):
        name = self._get_name_from_ref(ref)
        return u''.join([u'${', name.strip(), u'}'])

    def _get_constraintMsg(self, constraintMsg):
        if isinstance(constraintMsg, basestring):
            if constraintMsg.find(':jr:constraintMsg') != -1:
                ref = constraintMsg.replace(
                    'jr:itext(\'', '').replace('\')', '')
                k, constraintMsg = self._get_text_from_translation(ref)
        return constraintMsg

    def _get_name_from_ref(self, ref):
        '''given /xlsform_spec_test/launch,
        return the string after the last occurance of the character '/'
        '''
        pos = ref.rfind('/')
        if pos == -1:
            return ref
        else:
            return ref[pos + 1:].strip()

    def _expand_child(self, obj_list):
        return obj_list

    def _shorten_xpaths_in_string(self, text):
        def get_last_item(xpathStr):
            l = xpathStr.split("/")
            return l[len(l) - 1].strip()

        def replace_function(match):
            return "${%s}" % get_last_item(match.group())
        #moving re flags into compile for python 2.6 compat
        pattern = "( /[a-z0-9\-_]+(?:/[a-z0-9\-_]+)+ )"
        text = re.compile(pattern, flags=re.I).sub(replace_function, text)
        pattern = "(/[a-z0-9\-_]+(?:/[a-z0-9\-_]+)+)"
        text = re.compile(pattern, flags=re.I).sub(replace_function, text)
        return text


def write_object_to_file(filename, obj):
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(json.dumps(obj, indent=2))
    f.close()
    print "object written to file: ", filename
