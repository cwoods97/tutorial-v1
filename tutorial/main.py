"""TODO(ggchien): DO NOT SUBMIT without one-line documentation for notifications.

TODO(ggchien): DO NOT SUBMIT without a detailed description of notifications.
"""
import webapp2
import jinja2
import os
import logging
import base64 # from push example file
import json # from push example file
from google.appengine.ext import ndb
from google.appengine.api import users
#from flask import current_app, Flask, render_template, request # from push example file
#from google.cloud import pubsub # from push example file

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))
#app = Flask(__name__) # came from push example file

# Configure the following environment variables via app.yaml
# This is used in the push request handler to veirfy that the request came from
# pubsub and originated from a trusted source.
# This is from the push example file.
'''
app.config['PUBSUB_VERIFICATION_TOKEN'] = \
    os.environ['PUBSUB_VERIFICATION_TOKEN']
app.config['PUBSUB_TOPIC'] = os.environ['PUBSUB_TOPIC'] '''

# There should be some method, either here or in some other python
# file, where notifications are created from pub/sub messages and
# added to the database. For now, I just stuck it at the end.

# A notification has a requester, event type, photo name,
# and date/time of creation
class Notification(ndb.Model):
  requester_email_address = ndb.StringProperty()
  event_type = ndb.StringProperty()
  photo_name = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

class MainHandler(webapp2.RequestHandler):
  def get(self):
    # Fetch all notifications in reverse date order
    notifications = Notification.query().order(-Notification.date).fetch()
    template_values = {'notifications':notifications}
    template = jinja_environment.get_template("notifications.html")
    # Write to the appropriate html file
    self.response.write(template.render(template_values))


'''
# USING PUSH METHODS:
# [START push]
@app.route('/pubsub/push', methods=['POST'])
def pubsub_push():
    if (request.args.get('token', '') !=
            current_app.config['PUBSUB_VERIFICATION_TOKEN']):
        return 'Invalid request', 400

    # Hopefully instead of whatever is actually happening here,
    # we can get the attributes dict and call create_notification,
    # then receiving a new_notification that can be added to datastore.
    envelope = json.loads(request.data.decode('utf-8'))
    payload = base64.b64decode(envelope['message']['data'])

    MESSAGES.append(payload)

    # This may not work; I'm not sure if payload is a dict of attributes
    new_notification = create_notification(payload)
    new_notification.put() # put into database

    # Returning any 2xx status indicates successful receipt of the message.
    return 'OK', 200
# [END push] '''

# Given an array of attributes, create notification
def create_notification(attributes):
  requester_email_address = attributes.get('requesterEmailAddress')
  if requester_email_address is None:
    requester_email_address = 'Unknown'
  photo_name = attributes.get('resource') # this may need to be reformatted
  event_type = attributes.get('eventType')
  if event_type == 'OBJECT_FINALIZE':
    if attributes.get('overwroteGeneration') is not None:
      event_type = 'overwritten, finalize' # change to more comprehensive message
    else:
      event_type = 'created'
  elif event_type == 'OBJECT_ARCHIVE':
    if attributes.get('overwrittenByGeneration') is not None:
      event_type = 'overwritten, archive' # change to more comprehensive message
    else:
      event_type = 'archived'
  elif event_type == 'OBJECT_DELETE':
    if attributes.get('overwrittenByGeneration') is not None:
      event_type = 'overwritten, delete'
    else:
      event_type = 'deleted'
  else:
    event_type = 'updated'

  return Notification(requester_email_address=requester_email_address, event_type=event_type, photo_name=photo_name)


app = webapp2.WSGIApplication([
    ('/', MainHandler)
], debug=True)
