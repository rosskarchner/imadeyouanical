import random, webapp2

from google.appengine.ext import db

from google.appengine.api.users import User
from google.appengine.api import memcache



class Organizer(db.Model):
    name=db.StringProperty()
    slug=db.StringProperty()
    rss_last_fetched=db.DateTimeProperty()
    to_process=db.BooleanProperty(default=False)
    urls=db.StringListProperty()
    
