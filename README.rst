This project siplify use google forms. Google forms provides form by iframe, but this can destroy web page design and validation of such form is very limited. 

django-googloform generate form class which is very similar as original django forms. You can add validation, set default value or style google form into a design of your web page.  

Features:
========

	* Better validaton of google forms
	* The ability to style google form
	* The ability to set default value
	* Posibility to control of double submit
	* Save model object after send google form or some other activity



Installation:
============

easy_install/pip
----------------

Firstly install must install beautifulsoup, django-google-forms use it for parsing HTML:
	* ``pip install -U beautifulsoup4``
	* ``easy_install beautifulsoup4``
	
and finally install django-google-forms:
	* ``pip install -U django-google-forms``
	* ``easy_install django-google-forms``




Usage:
======

model:
------

In your model, you can use ``GoogleFormCodeField``. This field is used to store your google code of form. If user add google form URL to this field, from the URL is automatically parsed google form CODE. example::
	from googleforms.models.fields import GoogleFormCodeField, GoogleSpreadsheetCodeField

	class MyModel(models.Model):
    	form_code = GoogleFormCodeField(_(u'Form'), help_text=_(u'You can only copy google form URL'), max_length=255)      
    

forms:
------

``GoogleForm`` is very similar as original django form. This form has this constructor:
	
	``GoogleForm(code, data=None)``
		* data - this is POST data of request, if you can set data, form is send to your original-google-form (if form is valid).  
		* code - code of google form, this code you can get from ``GoogleFormCodeField``
		
	methods:
		* ``is_valid()`` - same function as original google form. This function return True if form can be send or False if form has some validation errors
		* ``save()`` - this method is empty and you can use it if you want save some data to database
		* ``is_post_valid()`` - return True if there is no problem via saving data to google spreadsheet
		* ``as_table()`` - return HTML code in table form
		* ``as_ul()`` - return HTML code in list form
		* ``as_p()`` - return HTML code in p form
		* `` _create_field(self, type, label_text, help_text, html, required)`` this function return form field class. Only selects right field class and call its constructor. You can use your own field class here.
		
from the original-google-form is removed submit button.

Default fields:
---------------
field classes is selected from dictionary which you can overload. Default dictionary is here::
	
	fields_class = {
	       'ss-scale':          ScaleField,
	       'ss-paragraph-text': TextareaField,
	       'ss-text':           InputField,
	       'ss-radio':          RadioField,  
	       'ss-checkbox':       CheckboxField,
	       'ss-select':         SelectField,
	       'ss-grid':           GridField
	}	

you can write your custom field which will inherit from this classes and change this dictionary to use your own field class. (keys of the dictionary is similar as google names of the fields)



Template:
---------

in the template you can use as_table, as_ul or as_p functions or from array of fields. For example::
	
	<h1>form.title</h1>
	<form action="" method="post">{% csrf_token %}
		<p>{{ form.description }}</p>
		{% for field in form.fields %}
			<p>{{ field.label }} <span class="help"> {{field.help_text }}</span>{{ field }}{{ field.errors }}</p>
		{% endfor %}
		<p><input type="submit" value="submit" /></p>
	</form>
	
	
Limitations
===========
Google paging not working now. But will be added in the next version.
	

