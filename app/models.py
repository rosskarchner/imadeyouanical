import random, webapp2

from google.appengine.ext import db
from google.appengine.ext.db.polymodel import PolyModel
from google.appengine.api.users import User
from google.appengine.api import memcache

from utils import slugify

from aetycoon import DerivedProperty

import vobject, logging, simplejson
from vobject import ics_diff
from datetime import datetime
from utils import clean_date





class Calendar(PolyModel):
    title=db.StringProperty()
    config_data=db.TextProperty()
  
  
    def is_follower(self, profile):
		existing_shard_q= CalendarFollowerShard.all().filter('followers =', profile.key())
		existing_shard_q.ancestor(self)
		return bool(existing_shard_q.get())  

    
    def follow(self,profile):
    	existing_shard_q= CalendarFollowerShard.all().filter('followers =', profile.key())
    	existing_shard_q.ancestor(self)
    	existing_shard=existing_shard_q.get()
    	if existing_shard:return
    	shard_key="shard%s"% int(random.random()*100)
    	shard=CalendarFollowerShard.get_or_insert(parent=self, key_name=shard_key)
    	shard.followers.append(profile.key())
    	shard.put()
    	
    	
    def unfollow(self,profile):
    	existing_shard_q= CalendarFollowerShard.all().filter('followers =', profile.key())
    	existing_shard_q.ancestor(self)
    	existing_shard=existing_shard_q.get()
    	if existing_shard:
    	    	existing_shard.followers.remove(profile.key())
    	    	if existing_shard.followers:
    	    		existing_shard.put()
    	    	else:
    	    		db.delete(existing_shard)
        
        
    @webapp2.cached_property
    def config(self):
        return simplejson.loads(self.config_data or "{}")
        
    def clear(self):
        cache_key=self.key().name()
        memcache.delete('calendar:'+cache_key)
        
        
    def get_option(self, option):
        pass
        




class CalendarFollowerShard(db.Model):
	followers=db.ListProperty(db.Key)
    
class ProfileCalendar(Calendar):
    pass
        
class EditedCalendar(Calendar):
	timezone=db.StringProperty(indexed=False)
	owner=db.StringProperty()
	domain=db.StringProperty()
	provision_token=db.StringProperty()
	provisioned=db.BooleanProperty()
	#TODO expiration date for un-provisioned calendars
	

	@webapp2.cached_property
	def view_uri(self):
		return url_for("calendar/view", calendar_slug=self.slug)
		
	@webapp2.cached_property
	def edit_uri(self):
		return url_for("calendar/edit", calendar_slug=self.slug)
	
    
class SourceCalendar(Calendar):
	source_uri=db.LinkProperty()
	driver=db.StringProperty()
	
	@webapp2.cached_property
	def view_uri(self):
		return url_for("calendar/view-sourced", calendar_slug=self.slug)
		
	@webapp2.cached_property
	def edit_uri(self):
		return None
	
	
	@classmethod
	def for_uri(cls,uri):
		return cls.all().filter('source_uri =', uri).get()
	

	
class ProjectedEvent(PolyModel):
    start= db.DateTimeProperty()
    end=db.DateTimeProperty()
    allday=db.BooleanProperty()
    tombstoned=db.BooleanProperty(default=True)



class ProfileProjectedEvent(ProjectedEvent):
    profile=db.ReferenceProperty()
    

	
class Event(PolyModel):
    title = db.StringProperty(required=True)
    start= db.DateTimeProperty()
    end=db.DateTimeProperty(indexed=True)
    allday=db.BooleanProperty(required=False)
    location=db.PostalAddressProperty(required=False, indexed=False)
    link=db.LinkProperty(required=False, indexed=False)
    description=db.TextProperty()
    cost=db.TextProperty(required=False)
    created=db.DateTimeProperty(auto_now_add=True)
    updated=db.DateTimeProperty(auto_now_add=True)
    tombstoned=db.BooleanProperty(default=False)
    
    @DerivedProperty
    def slug(self):
        return self.start.strftime("%Y-%m-%d-")+slugify(self.title)
        #todo: ensure this is unique
        
        
    def project_to_followers(self):
        pipe= ProjectEventToFollowers(str(self.key()), str(self.parent_key()))
        pipe.start()
    


class SubmittedEvent(Event):
    calendar=db.ReferenceProperty(EditedCalendar)
    approval_state=db.StringProperty(required=True, default="submitted")
    submitted_by=db.StringProperty(required=True)
    approved_by=db.StringProperty()
    approved_on=db.DateTimeProperty(auto_now_add=False)



class SourcedEvent(Event):
	last_seen=db.DateTimeProperty(auto_now_add=True, required=True)
	raw_ical=db.TextProperty(required=True)
	source_uid=db.StringProperty(required=False)
	
	def update_from_ics_diff(self,diff, all_day):
		changed=False
		self.tombstoned=False
		if diff and diff[0][1]:
			self.allday=all_day
			for component in diff[0][1].getChildren():
				if component.name in ['SUMMARY','LOCATION','DTSTART','DTEND','DESCRIPTION','LINK']:
					changed=True
					if component.name == 'SUMMARY': self.title=component.value or 'Untitled Event'
					if component.name == 'LOCATION': self.location=component.value
					if component.name == 'DTSTART': self.start=clean_date(component.value)
					if component.name == 'DTEND': self.end=clean_date(component.value)
					if component.name == 'URL': self.link=component.value
					if component.name == 'DESCRIPTION': self.description=component.value
		return self, changed
		
# class ProjectEventToFollowers(pipeline.Pipeline):
#     def run(self, event_key, calendar_key):
#         shard_q= CalendarFollowerShard.all()
#         shard_q.ancestor(db.Key(calendar_key))
#         for shard in shard_q:
#             yield ProjectEventToFollowersShard(event_key,str(shard.key()))
#             
#     def finalized(self):
#         logging.warning("projected!")
#         
#         
# class ProjectEventToFollowersShard(pipeline.Pipeline):
#     def run(self, event_key, shard_key):
#         event, shard=db.get([db.Key(event_key), db.Key(shard_key)])
#         followers=db.get(shard.followers)
#         peps=[]
#         for follower in followers:
#             key_name="profile%sevent%s" %( follower.key().id(), event.key().id())
#             pep=ProfileProjectedEvent.get_or_insert(key_name=key_name, parent=event, profile=follower)
#             pep.profile=follower
#             pep.start=event.start
#             pep.end=event.end
#             pep.allday=event.allday
#             pep.tombstoned=event.tombstoned
#             logging.warning("%s to %s" % (event, follower))
#             peps.append(pep)
#         db.put(peps)
            