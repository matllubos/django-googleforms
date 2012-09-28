# coding: utf-8
import re
import httplib
import urllib

from django import forms
from django.utils.safestring import mark_safe
from django.forms.util import ErrorList
from django.core.exceptions import ValidationError
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from bs4 import BeautifulSoup
from django.utils.encoding import force_unicode

class GoogleSpreadsheetField(forms.CharField):
    def clean(self, value):
        value = re.sub(r'^.*\?key=([^&#"]*).*$',r'\g<1>', value)
        return super(GoogleSpreadsheetField, self).clean(value) 
    
class GoogleFormCodeField(forms.CharField):
    def clean(self, value):
        value = re.sub(r'^.*\?formkey=([^&#"]*).*$',r'\g<1>', value)
        return super(GoogleFormCodeField, self).clean(value)
    
    
    
'''
    Google Forms
'''
    
    
class Field(object):
    value = None
    error_messages = {
        'required': _(u'This field is required.'),
        'invalid': _(u'Enter a valid value.'),
    }
    
    def __init__(self, label, help_text, html, required, default_value=None, attrs={}):
        self.label_text = label
        self.help_text = help_text
        self.html = html
        self.required = required
        self.default_value = default_value
        self.attrs = attrs
        self.errors = ErrorList()

    @property
    def label(self):
        return mark_safe(u'<label for="%s" class="label-text">%s</label>' % (self.first_name, self.label_text))
    
    @property
    def type(self):
        return self.__class__.__name__
    
    def render(self, value):
        self._set_attrs(self.attrs)
        
        if self.default_value:
            self._set_value(self.default_value)
        
        if value:
            self._set_value(value)
        
        
        return mark_safe(' '.join([unicode(tag) for tag in self.html.contents]))
        
    def __unicode__(self):
        return self.render(self.value)
    
    def clean(self, value):
        self.errors = ErrorList()
        self.value = value
        try:
            self.validate(value)
        except ValidationError as e:
            self.errors.extend(e.messages)
       
        if self.errors:
            raise ValidationError(self.errors) 
        return value

    def validate(self, value):
        if value in validators.EMPTY_VALUES and self.required:
            raise ValidationError(self.error_messages['required'])

    @property
    def names(self):
        duplicated_names = [el['name'] for el in self.html.find_all('input') + self.html.find_all('textarea') + self.html.find_all('select')]
        names = []
        for name in duplicated_names:
            if not name in names:
                names.append(name)
        return names
    
    @property
    def first_name(self):
        return self.names[0]
     
    def _set_attrs(self, attrs):
        pass
    
    def _set_value(self, value):
        pass
    
    
      
class InputField(Field):
       
    def _set_attrs(self, attrs):
        for attr_key, attr_val in attrs.items():
            self.html.input[attr_key] = attr_val
    
    def _set_value(self, value):
        self.html.input['value'] = value
        
class TextareaField(Field):
    
    def _set_attrs(self, attrs):
        for attr_key, attr_val in attrs.items():
            self.html.textarea[attr_key] = attr_val
    
    def _set_value(self, value):
        self.html.textarea.clear()
        self.html.textarea.append(value)
        
#add default value a atrs
class ScaleField(Field): 
    
    def _set_value(self, value):
        input = self.html.find('input', {'value': value})
        if input:
            input['checked'] = 'checked'
    
class RadioField(Field): 
    
    def __init__(self, label, help_text, html, required, default_value=None, attrs={}):
        self.other_value = False
        if html.find('input', {'type':'text'}):
            self.other_value = True
        super(RadioField, self).__init__(label, help_text, html, required, default_value, attrs)
        
    def _set_value(self, value):
        if self.other_value:
            input = self.html.find('input', {'value': value[0]})
            other_input = self.html.find('input', {'type':'text'})
            if input:
                input['checked'] = 'checked'
            if other_input and value[1] and value[0] == '__option__':
                other_input['value'] = value[1]               
            
        else:
            input = self.html.find('input', {'value':value})
            if input:
                input['checked'] = 'checked'
                   
    def validate(self, values):
        if self.other_value and self.required:
            if values[0] in validators.EMPTY_VALUES:
                raise ValidationError(self.error_messages['required'])
            
            if values[0] == '__option__' and values[1] in validators.EMPTY_VALUES:
                raise ValidationError(self.error_messages['required'])
        else:
            super(RadioField, self).validate(values)
        
     
class CheckboxField(Field): 
    
    def _set_value(self, values):
        if not isinstance(values, list):
            values = [values]
        for value in values:
            input = self.html.find('input', {'value':value})
            if input:
                input['checked'] = 'checked'
      
class SelectField(Field): 
    
    def _set_value(self, value):
        option = self.html.find('option', {'value': value})
        if option:
            option['selected'] = 'selected'
                
     
class GridField(Field):

    def validate(self, values):
        if self.required:
            for value in values:
                if value in validators.EMPTY_VALUES:
                    raise ValidationError(self.error_messages['required'])
                
     
    def _set_value(self, values):
        i=0
        for value in values:
            input = self.html.find('input', {'value':value, 'name': self.names[i]})
            i += 1
            if input:
                input['checked'] = 'checked'
                           
    
class GoogleForm(object):
    
    post_response = None
    response = None
    remove_submit = True
    valid = True
    
    default_fields_class = {
       'ss-scale':          ScaleField,
       'ss-paragraph-text': TextareaField,
       'ss-text':           InputField,
       'ss-radio':          RadioField,  
       'ss-checkbox':       CheckboxField,
       'ss-select':         SelectField,
       'ss-grid':           GridField
    }
    
    
    def __init__(self, code, data=None, files=None, initial=None):
        self.code = code
        self.data = data
        self.response = self._get()
        
        self._parse_html(self.response)
        if self.data:
            if self.is_valid():
                self.post_response = self._post();
                if not self.is_post_valid():
                    self._parse_html(self.post_response)
                    
                    
    
    def _create_field(self, type, label_text, help_text, html, required): 
        field_class = self.fields_class.get(type, None) or self.default_fields_class.get(type, Field)
        return field_class(label_text, help_text, html, required)
    
    
    def _parse_entry(self, entry):
        required = False
        label_text = ''
        help_text = ''
        if  u'ss-item-required' in entry.parent['class']:
            required = True
        
        if self.remove_submit and u'ss-navigate' in entry.parent['class']:
            return
        
        label =  entry.find('label', { "class" : "ss-q-title" })
        if label.span:
            label.span.replaceWith('')
        if label:
            label_text = ' '.join([unicode(tag) for tag in label.contents])
        label.replaceWith('')
        
        
        help_label  =  entry.find('label', { "class" : "ss-q-help" })
        if help_label:
            help_text = ' '.join([unicode(tag) for tag in help_label.contents])
        help_label.replaceWith('')
        
        type = entry.parent['class'][-1]
        html = entry
        return self._create_field(type, label_text, help_text, html, required) 
    
         
    def _parse_html(self, html):
        self.fields = []
        soup = BeautifulSoup(html)
        entries = soup.find_all('div', { "class" : "ss-form-entry" })
        
        for entry in entries:
            field = self._parse_entry(entry)
            if field:            
                self.fields.append(field)
                
        self.title = ' '.join([unicode(tag) for tag in soup.h1.contents])
        self.description = ' '.join([unicode(tag) for tag in soup.find('div', {'class':'ss-form-desc'}) or ['']])

               
    def _get(self):
        conn = httplib.HTTPSConnection("docs.google.com")
        headers = {'Accept-Language': '%s;q=0.8' % translation.get_language()}

        conn.request("GET", "/spreadsheet/viewform?formkey=%s#gid=0" % self.code, headers=headers)
        response = conn.getresponse()
        html = response.read()
        conn.close()
        html = html.decode("utf-8")
        return re.sub(u'\n', u'', unicode(html))


    def _post(self):
        data = self.data.copy()
        params =  urllib.urlencode(dict(self.data.copy()), doseq=True)
        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain", 'Accept-Language': '%s;q=0.5' % translation.get_language()}

        conn = httplib.HTTPSConnection("docs.google.com")
        conn.request("POST", re.sub('docs.google.com', '', self._google_url(self.response)), params, headers)
        response = conn.getresponse()
        html = response.read()
        conn.close()
        html = html.decode("utf-8")
        return re.sub(u'\n', u'', unicode(html))
    
    
    def save(self):
        pass
    
    def is_valid(self):
        self.validate()
        return self.valid
    
    def validate(self):
        for field in self.fields:
            try:
                values = []
                for name in field.names:
                    if len(self.data.getlist(name)) <= 1:
                        value = self.data.get(name, None)
                    else:
                        value = self.data.getlist(name)
                    values.append(value)
                
                
                if len(values) == 1:
                    field.clean(values[0])
                elif len(values) == 0:
                    field.clean(None)
                else:
                    field.clean(values)
                 
            except ValidationError as e:
                self.valid = self.valid and False
        
    def is_post_valid(self):
        if self.post_response and not re.match( u".*<form.*", self.post_response):
            return True
        return False

    def _form_content(self, html):
        html = re.sub(u'^.*<form[^>]*>(.*)</form>.*$', '\g<1>', html)
        html = re.sub(u'<input[^>]*type="submit"[^>]*>', '', html)
        return html
    
    def _google_url(self, html):
        m = re.match( u".*action=\"([^\"]*)\".*", html)
        url = m.group(1)
        return url
    
    
    def as_table(self):
        "The same code as original django form: Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self._html_output(
            normal_row = u'<tr%(html_class_attr)s><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>',
            error_row = u'<tr><td colspan="2">%s</td></tr>',
            row_ender = u'</td></tr>',
            help_text_html = u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row = False)

    def as_ul(self):
        "The same code as original django form: Returns this form rendered as HTML <li>s -- excluding the <ul></ul>."
        return self._html_output(
            normal_row = u'<li%(html_class_attr)s>%(errors)s%(label)s %(field)s%(help_text)s</li>',
            error_row = u'<li>%s</li>',
            row_ender = '</li>',
            help_text_html = u' <span class="helptext">%s</span>',
            errors_on_separate_row = False)

    def as_p(self):
        "The same code as original django form: Returns this form rendered as HTML <p>s."
        return self._html_output(
            normal_row = u'<p%(html_class_attr)s>%(label)s %(field)s%(help_text)s</p>',
            error_row = u'%s',
            row_ender = '</p>',
            help_text_html = u' <span class="helptext">%s</span>',
            errors_on_separate_row = True)
         
         
    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        output = []
        for field in self.fields:
            output.append(normal_row % {
                    'errors': force_unicode(field.errors),
                    'label': field.label,
                    'field': unicode(field),
                    'help_text': field.help_text,
                    'html_class_attr': ''
                })
    
        return mark_safe(u'\n'.join(output))