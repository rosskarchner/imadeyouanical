# -*- coding: utf-8 -*-
"""WSGI app setup."""
import os, sys
from google.appengine.ext.webapp import util
debug = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')
sys.path = ['lib', 'lib/dist', 'lib/dist.zip'] +sys.path
import webapp2
from utils import deserialize_entities, serialize_entities

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.api import memcache


root_domain='shareevents.com'
if debug:root_domain='shareevents.local:8080'




def enable_jinja2_debugging():
    """Enables blacklisted modules that help Jinja2 debugging."""
    if not debug:
        return
    from google.appengine.tools.dev_appserver import HardenedModulesHook
    HardenedModulesHook._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']


root_app  = webapp2.WSGIApplication([
    ('/provision', 'provision.ProvisionHandler'),

], debug=debug)

calendar_app = webapp2.WSGIApplication([
    webapp2.Route('/', 'se_calendar.FrontPageHandler'),
     webapp2.Route('/config', 'se_calendar.ConfigurationRegistryHandler'),
     webapp2.Route('/add', 'se_calendar.SubmitEventHandler'),
    webapp2.Route('/setup/<guid>','provision.DeployHandler'),
], debug=debug)



enable_jinja2_debugging()


# "virtual hosting" for calendars
def calendar_host(environ, start_response):
    from models import EditedCalendar
    key=environ['HTTP_HOST']
    calendar = deserialize_entities(memcache.get('calendar:'+key))
    if not calendar:
        calendar= EditedCalendar.get_by_key_name(key)
        if calendar: memcache.set('calendar:'+key, serialize_entities(calendar))
        
    
    if calendar:
        environ['calendar'] = calendar
        return calendar_app(environ, start_response)
    else:
        response_body = ""
        status = '302 Redirect'
        if root_domain in environ['HTTP_HOST']:
            response_headers = [('Location', 'http://www.%s/provision?domain=%s' % (root_domain,environ['HTTP_HOST'].split('.')[0])),
                  ]
        else:
            response_headers = [('Location', 'http://www.%s/provision' % root_domain),
                  ]
        
        
        start_response(status, response_headers)
        return response_body


def default_host(environ, start_response):
        response_body = ""
        status = '302 Redirect'
        response_headers = [('Location', 'http://www.%s/' % root_domain),
                  ]
        start_response(status, response_headers)
        return response_body

    
    

    


# set up domain routing
import wfront

mapping = [
            ('www.'+root_domain, root_app, None),
           ('*.'+root_domain, calendar_host, None),
           ]

router = wfront.route(mapping, default=default_host)


def main():
    util.run_wsgi_app(router)


if __name__ == '__main__':
    main()