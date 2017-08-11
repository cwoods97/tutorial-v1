"""TODO(ggchien): DO NOT SUBMIT without one-line documentation for notifications.

TODO(ggchien): DO NOT SUBMIT without a detailed description of notifications.
"""
import webapp2
import jinja2
import os
import logging
import base64
import json
import urllib
import cloudstorage as gcs
from google.cloud import pubsub
from google.appengine.ext import ndb
from google.appengine.ext import blobstore
#from google.appengine.ext webapp import blobstore_handlers
from google.appengine.api import users
from google.appengine.api import images
from google.appengine.api import app_identity
from google.appengine.api import files

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_environment = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir))

THUMBNAIL_BUCKET = 'tutorial-thumbnails'

# A notification has a requester, event type, photo name,
# and date/time of creation
class Notification(ndb.Model):
  requester_email_address = ndb.StringProperty()
  event_type = ndb.StringProperty()
  photo_name = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

# A thumbnail reference has the name of the photo,
# the name of the poster, and the date it was posted.
class ThumbnailReference(ndb.Model):
  thumbnail_name = ndb.StringProperty()
  thumbnail_key = ndb.StringProperty()
  poster_email_address = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)

# A contributor has an email address and
# a profile picture, which is a thumbnail reference.
class Contributor(ndb.Model):
  email = ndb.StringProperty()
  profile_pic = ndb.StructuredProperty(ThumbnailReference)

# Home/news feed page (notification listing).
class MainHandler(webapp2.RequestHandler):
  # Initialize the Pub/Sub resources.
  def __init__(self, request=None, response=None):
    super(MainHandler, self).__init__(request, response)
    #client = pubsub.Client(project='tutorial-trial')
    #topic = client.topic('tutorial-trial.appspot.com')
    #subscription = topic.subscription('subscription')

  def get(self):
    # Fetch all notifications in reverse date order
    notification = create_notification('photo.jpg', 'OBJECT_DELETE', 'user@yay.com', None, None)
    notification.put()
    notifications = Notification.query().order(-Notification.date).fetch()
    template_values = {'notifications':notifications}
    template = jinja_environment.get_template("notifications.html")
    # Write to the appropriate html file
    self.response.write(template.render(template_values))

# All photos page (displays thumbnails).
'''class PhotosHandler(webapp2.RequestHandler):
  def get(self):
    # Get thumbnail references from datastore in reverse date order
    thumbnail_references = ThumbnailReference.query().order(-ThumbnailReference.date).fetch()
    # thumbnails should be in same order as thumbnail_references
    thumbnails = []
    # For loop may not be ordered
    for thumbnail_reference in thumbnail_references:
      img = get_photo(thumbnail_reference.thumbnail_name)
      thumbnails.append(img.read())
      img.close()
    template_values = {'thumbnail_references':thumbnail_references, 'thumbnails':thumbnails}
    template = jinja_environment.get_template("photos.html")
    # Make header so images are displayed correctly. Otherwise they might be
    # plain text?
    self.response.headers['Content-Type'] = 'image/jpeg'
    # Write to appropriate html file
    self.response.write(template.render(template_values))'''

# Contributors page (contributor emails).
# LATER: also display contributor profile pics. Get
# thumbnail reference from given contributor and use it
# to create thumbnail array, then format in HTML file similarly
# to in photos.html
class ContributorsHandler(webapp2.RequestHandler):
  def get(self):
    contributors = Contributor.query().fetch()
    template_values = {'contributors':contributors}
    template = jinja_environment.get_template("contributors.html")
    self.response.write(template.render(template_values))

# For receiving Cloud Pub/Sub push messages.
class ReceiveMessage(webapp2.RequestHandler):
  def post(self):
    if constants.SUBSCRIPTION_UNIQUE_TOKEN != self.request.get('token'):
      self.response.status = 404
      return

    logging.debug('Post body: {}'.format(self.request.body))
    message = json.loads(urllib.unquote(self.request.body).rstrip('='))

    # Invalidate the cache
    memcache.delete(MESSAGE_CACHE_KEY)

    event_type = message.get('eventType')
    photo_name = message.get('objectId')
    generation_number = str(message.get('objectGeneration'))
    overwrote_generation = message.get('overwroteGeneration')
    overwritten_by_generation = message.get('overwrittenByGeneration')
    '''email = message.get('requesterEmailAddress')
    # Add known contributors to datastore if not already added.
    # Contributors are those who have performed actions on the album,
    # not necessarily just those who have uploaded photos.
    if email is None:
      email = 'Unknown'
    else:
      contributors = Contributor.query().fetch().filter(email=email)
      # Only add contributor if not already in datastore.
      if len(contributors.keys()) == 0:
        # Specify some default photo to create contributor with here
        new_contributor = Contributor(email=email)
        new_contributor.put()
    index = photo_name.index(".jpg")
    thumbnail_key = photo_name[:index] + generation_number + photo_name[index:]'''

    # Perform profile pic logic here; create string of what profile name would
    # be. Change
    # notification to "___ changed their profile picture" or "goodbye old
    # profile" depending on if the FINALIZE or DELETE/ARCHIVE message was
    # received (rather than general object change messages).
    expected_profile_pic = 'profile-' + email + '.jpg'
    profile = False
    if photo_name == expected_profile_pic:
      profile = True # Might be repetitive with following line
      new_notification = create_notification(photo_name, event_type, email, overwrote_generation, overwritten_by_generation, profile=True)
    else:
      new_notification = create_notification(photo_name, event_type, email, overwrote_generation, overwritten_by_generation)
    new_notification.put() # put into database

    # If create message: get photo from photos gcs bucket, shrink to thumbnail,
    # and store thumbnail in thumbnails gcs bucket. Store thumbnail reference in
    # datastore.
    '''if event_type == 'OBJECT_FINALIZE':
      image = get_photo(photo_name) # not implemented
      thumbnail = get_thumbnail(image)
      store_thumbnail_in_gcs(thumbnail_key) # store under name thumbnail_key. Not implemented
      thumbnail_reference = ThumbnailReference(thumbnail_name=photo_name, thumbnail_key=thumbnail_key, poster_email_address=email)
      thumbnail_reference.put()
      image.close()
      if profile:
        # Update contributor info
        contributor = Contributor.query(email=email)
        contributor.profile_pic = thumbnail_reference
        contributor.put()
    # If delete/archive message: delete thumbnail from gcs bucket and delete
    # thumbnail reference from datastore.
    elif event_type == 'OBJECT_DELETE' or event_type == 'OBJECT_ARCHIVE':
      delete_thumbnail(thumbnail_key, THUMBNAIL_BUCKET)
      thumbnail_reference = ThumbnailReference.query(thumbnail_key=thumbnail_key)
      thumbnail_reference.key.delete()
    # No action performed if event_type is OBJECT_UPDATE'''

    self.response.status = 200
    # Automatically refresh to notifications page? Will this force you to go to
    # an undesired page?
    self.redirect('/')

# Given an array of attributes, create notification
def create_notification(photo_name, event_type, requester_email_address, overwrote_generation, overwritten_by_generation, profile=False):
  if profile:
    if event_type == 'OBJECT_FINALIZE':
      event_type = 'profile picture updated, finalize' # change to more comprehensive message
    elif event_type == 'OBJECT_ARCHIVE' or event_type == 'OBJECT_DELETE':
      event_type = 'profile picture updated, archive/delete' # change to more comprehensive message
  else:
    if event_type == 'OBJECT_FINALIZE':
      if overwrote_generation is not None:
        event_type = 'overwritten, finalize' # change to more comprehensive message
      else:
        event_type = 'created'
    elif event_type == 'OBJECT_ARCHIVE':
      if overwritten_by_generation is not None:
        event_type = 'overwritten, archive' # change to more comprehensive message
      else:
        event_type = 'archived'
    elif event_type == 'OBJECT_DELETE':
      if overwritten_by_generation is not None:
        event_type = 'overwritten, delete' # change to more comprehensive message
      else:
        event_type = 'deleted'
    else:
      event_type = 'metadata updated'

  return Notification(requester_email_address=requester_email_address, event_type=event_type, photo_name=photo_name)

# Shrinks a given image to thumbnail size.
'''def get_thumbnail(image):
  image.resize(width=80, height=100)
  return image.execute_transforms(output_encoding=images.JPEG)

# Retrieve photo from GCS
# Note: file must be closed elsewhere
def get_photo(self, photo_name):
  return gcs.open(photo_name)

# Write photo to GCS thumbnail bucket
def store_thumbnail_in_gcs(self, thumbnail_key)
  write_retry_params = gcs.RetryParams(backoff_factor=1.1)
  gcs_photo = gcs.open(thumbnail_key)
  gcs_photo.close()
  self.tmp_filenames_to_clean_up.append(thumbnail_key)

# Delete thumbnail from GCS bucket
def delete_thumbnail(self, thumbnail_key, bucket)
  file = '/gs/' + bucket + '/' + thumbnail_key
  files.delete(file)'''

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    #('/photos', PhotosHandler),
    ('/contributors', ContributorsHandler),
    ('/_ah/push-handlers/receive_message', ReceiveMessage)
], debug=True)
