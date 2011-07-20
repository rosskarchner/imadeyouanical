# -*- coding: utf-8 -*-
"""
    urls
    ~~~~

    URL definitions.

    :copyright: 2009 by tipfy.org.
    :license: BSD, see LICENSE.txt for more details.
"""
from tipfy import Rule
from werkzeug import import_string
from config import config



#  Here we show an example of joining all rules from the
# ``apps_installed`` definition set in config.py.
rules = []

for app_module in config['tipfy']['apps_installed']:
	try:
		# Load the urls module from the app and extend our rules.
		app_rules = import_string('%s.urls' % app_module)
		rules.extend(app_rules.get_rules())
	except ImportError:
		pass

