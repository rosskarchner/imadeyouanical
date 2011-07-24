from urllib2 import urlopen
from urlparse import urlparse, urljoin
from cgi import parse_qs
from BeautifulSoup import BeautifulSoup
import re

# given a URL or HTML, try to extract any structured event data or calendars
# 
# There should also be some sort of ranking, if multiple calendars are available.
#


gcal_link_re=re.compile(r'http[s]*://.+google.com/calendar/.+/((.)+)/public/.+', flags=re.IGNORECASE)
gcal_embed_re= re.compile(r'http[s]*://www.google.com/calendar.embed?((.)+)', flags=re.IGNORECASE)
extract_meetup_id_from_js=re.compile(r'var Chapter={id:((\d)+)')
webcal_re = re.compile(r'webcal://(.)+',re.IGNORECASE)
eventbrite_organizer_link_re=re.compile(r'.+eventbrite.com/org/((\d)+)', flags=re.IGNORECASE)
eventbrite_backup_organizer_link_re=re.compile('.+eventbrite.com/rss/organizer_list_events.((\d)+)', flags=re.IGNORECASE)
eventbrite_event_link=re.compile('http[s]*://[^www]+\.eventbrite.com',flags=re.IGNORECASE)

      
def search_for_calendars(uri=None, html=None, recursive=False):
    if uri:
    	html= urlopen(uri).read()
    soup = BeautifulSoup(html)
    # search for <link rel=alternate type=text/calendar />  
    # This should always win.
    discovered=[]
    gcal_ids=set() 
    found = soup.findAll('link', rel=re.compile(r'ALTERNATE', flags=re.IGNORECASE),
                      type=re.compile(r'text/calendar', flags=re.IGNORECASE ))
    if found and "eventbrite.com" not in uri:   # on eventbrite, these will be single-event ical files about the particular event-- what we want here is the organizer ID
        for link in found:
            complete_uri=urljoin(uri,dict(link.attrs)['href'])
            discovered.append((complete_uri, 'ical'))

    # webcal:// links
    found=soup.findAll('a',href=webcal_re)
    if found: 
        for webcal in found:
            href=dict(webcal.attrs)['href'].replace('webcal://','http://')
            complete_uri=urljoin(uri,href)
            discovered.append((complete_uri, 'ical'))

    # next, look for embedded google calendars
    found= soup.findAll('iframe', src=gcal_embed_re) 
    if found: 
        for iframe in found:
            query= urlparse(dict(iframe.attrs)['src']).query
            calendar_id = parse_qs(query)['src'][0]
            gcal_ids.add(calendar_id)

    # now, links to google calendars iCal or Atom feed
    
    found= soup.findAll('a', href=gcal_link_re)
    if found:  
        for link in found:
            match=gcal_link_re.match(dict(link.attrs)['href'])
            gcal_ids.add(match.group(1).replace('%40','@'))

    # next, look for links to  the HTML version of a google calendar, this is how "add to google calendar" buttons usually work
    found= soup.findAll('a', href=gcal_embed_re) 
    if found: 
        for iframe in found:
            query= urlparse(dict(iframe.attrs)['href']).query
            calendar_id = parse_qs(query)['src'][0]
            gcal_ids.add(calendar_id)


    # is this a Meetup?
    found=soup.find('meta', property="og:site_name", content="Meetup")
    if found:
        #if so, look for the block of javascript where we can extract the group ID
        js_data=soup.find(text=extract_meetup_id_from_js)
        meetup_ids_found=set()
        if js_data: 
            for line in  js_data.split(';'):
                match= extract_meetup_id_from_js.match( line)
                if match:
                    meetup_ids_found.add(match.group(1))

        for meetup_group_id in meetup_ids_found:
            discovered.append((meetup_group_id, 'meetup.group'))
        
    # look for links to an Eventbrite organizer
    eb_ids=set()
    regexes_to_try=[eventbrite_organizer_link_re, eventbrite_backup_organizer_link_re]
    for regex in regexes_to_try:
        found=soup.findAll('a', href=regex)
        if found:
            for link in found:
                href=dict(link.attrs)['href']
                match=regex.match(href)
                eb_ids.add(match.group(1))
    
    
    for eb_id in eb_ids:
        discovered.append((eb_id,'eventbrite.group'))
    
    for gcal in gcal_ids:
            discovered.append((gcal, 'gdata',))
    
    #last ditch attempt: are there any links to Eventbrite events?
    if not recursive and not discovered :
        found=soup.find('a', href=eventbrite_event_link)
        if found:
            discovered=search_for_calendars(dict(found.attrs)['href'],recursive=True)
    
    return discovered
    
    

             
    
calendars=[ 'http://meetup.zpugdc.org/',
                'http://icalshare.com/calendars/5201',
                'http://dcbeer.com/dc-beer-events-calendar/',
                'http://www.meetup.com/DC-Tech-Meetup/',
                "http://startupbaltimore.org/events-calendar/",
                'http://www.i3detroit.com/',
                'http://www.birchandbarley.com/calendar.html',
                'http://plancast.com/category/technology/259208#category/7/local',
                'http://www.dctechevents.com/',
                'http://www.hacdc.org/',
                'http://refreshdc-april2011-eorg.eventbrite.com/',
                'http://www.eventbrite.com/org/1039770801?s=3731973',
                'http://eventful.com/washingtondc/events?q=Conferences&ga_search=Conferences&ga_type=events&c=technology',
                'http://sites.google.com/site/detroitjug/',
                'http://www.capmac.org/phpicalendar/month.php',
                'http://austinlug.org/event'
          ]

          #  'http://sites.google.com/site/detroitjug/', #links to an eventbrite page
          #  'http://www.facebook.com/group.php?gid=156512411342&v=app_2344061033', #facebook group with events
          #  http://eventful.com/washingtondc/events?q=Conferences&ga_search=Conferences&ga_type=events&c=technology   links to an ical
          # http://www.dc-flex.com/  embeds  facebook page
          #    'http://upcoming.yahoo.com/search/?type=events&rt=1&rollup=&q=&loc=Washington',
      
    
if __name__ == '__main__': 
    for calendar_uri in calendars:
      print calendar_uri
      print search_for_calendars(calendar_uri)
