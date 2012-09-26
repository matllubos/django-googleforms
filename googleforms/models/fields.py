from django.db import models
from django.utils.translation import ugettext_lazy as _

from googleforms import forms as google_forms

class GoogleSpreadsheet(object):
    
    def __init__(self, value):
        self.value = value
    
    @property
    def graph_hyperlink(self):
        return u'https://docs.google.com/spreadsheet/gform?key=%s&gridId=0#chart' % self.value
        
    @property
    def spreadsheet_hyperlink(self):
        return u'https://docs.google.com/spreadsheet/ccc?key=%s#gid=0' % self.value
    
    @property
    def form_hyperlink(self):
        return u'https://docs.google.com/spreadsheet/gform?key=%s&gridId=0#edit' % self.value

    def __unicode__(self):
        return "%s" % (self.value,)
    
    def __str__(self):
        return "%s" % (self.value,)
    
    def __len__(self):
        return len(self.value)

class GoogleSpreadsheetCodeField(models.CharField):

    description = _(u"Google spreadsheet url")
    __metaclass__ = models.SubfieldBase
    
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 100
        super(GoogleSpreadsheetCodeField, self).__init__(*args, **kwargs)

     
    def formfield(self, **kwargs):
        return super(GoogleSpreadsheetCodeField, self).formfield(form_class=google_forms.GoogleSpreadsheetField, **kwargs)

    #Not working in SQKLite3
    def to_python(self, value):
        if isinstance(value, GoogleSpreadsheet):
            return value
        return GoogleSpreadsheet(value)
    
    
    
class GoogleFormCodeField(models.CharField):
         
    def formfield(self, **kwargs):
        return super(GoogleFormCodeField, self).formfield(form_class=google_forms.GoogleFormCodeField, **kwargs)
