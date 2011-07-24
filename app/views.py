import webapp2, feedparser

from webapp2_extras import jinja2

from eventscrape import search_for_calendars

from models import Organizer


class IndexHandler(webapp2.RequestHandler):
	@webapp2.cached_property
	def jinja2(self):
		# Returns a Jinja2 renderer cached in the app registry.
		return jinja2.get_jinja2(app=self.app)

		
	def render_response(self, _template, **context):
		# Renders a template and writes the result to the response.
		rv = self.jinja2.render_template(_template, **context)
		self.response.write(rv)

	def get(self):
		self.render_response('index.html')

	def post(self):
		url=self.request.str_POST.get('url')
		#TODO: search by page URL
		results=search_for_calendars(url)
		if results and results[0][1]== 'eventbrite.group':
			oid=results[0][0]
			o=Organizer.get_by_key_name(oid)
			if o:
				return webapp2.redirect('/%s' % oid)
			else:
				rss_uri="http://www.eventbrite.com/rss/organizer_list_events/"+str(results[0][0])
				feed=feedparser.parse(rss_uri)
				o=Organizer(key_name=oid, name=feed.feed.title)
				o.put()

			return webapp2.redirect('/%s' % oid)
		
		else:
			self.response.write("that doesn't appear to be an eventbrite page, or there is no oranization associated with the event")
