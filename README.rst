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

In your model, you can use ``GoogleFormCodeField``. This field is used to store your google code of form. If user add google form URL to this field, from the URL is automatically parsed google form CODE.

example::
	from googleforms.models.fields import GoogleFormCodeField, GoogleSpreadsheetCodeField

	class MyModel(models.Model):
    	form_code = GoogleFormCodeField(_(u'Form'), help_text=_(u'You can only copy google form URL'), max_length=255)      
    

forms:
------

