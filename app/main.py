# -*- coding: utf-8 -*-
"""WSGI app setup."""
import os, sys
from google.appengine.ext.webapp import util
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
sys.path = ['lib', 'lib/dist', 'lib/dist.zip'] +sys.path
import webapp2

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.api import memcache




def enable_jinja2_debugging():
    """Enables blacklisted modules that help Jinja2 debugging."""
    if not debug:
        return
    from google.appengine.tools.dev_appserver import HardenedModulesHook
    HardenedModulesHook._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']



app = webapp2.WSGIApplication([
    webapp2.Route('/', 'views.IndexHandler'),

], debug=debug)



enable_jinja2_debugging()



def main():
    app.run()

if __name__ == '__main__':
    main()
