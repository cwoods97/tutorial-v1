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
import lib.cloudstorage as gcs
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
PHOTO_BUCKET = 'tutorial-trial.appspot.com'

# A notification has a requester, event type, photo name,
# and date/time of creation
class Notification(ndb.Model):
  message = ndb.StringProperty()
  date = ndb.DateTimeProperty(auto_now_add=True)
  generation = ndb.StringProperty()

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
  def get(self):
    # Fetch all notifications in reverse date order
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
    # possibly make a dict mapping references to thumbnails instead
    thumbnails = {}
    # For loop may not be ordered
    for thumbnail_reference in thumbnail_references:
      img = get_photo(thumbnail_reference.thumbnail_name, THUMBNAIL_BUCKET)
      self.response.headers['Content-Type'] = 'image/jpeg'
      self.response.write(img)
      thumbnails[thumbnail_reference] = img
      img.close()
    template_values = {'thumbnails':thumbnails}
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
    logging.debug('Post body: {}'.format(self.request.body))
    message = json.loads(urllib.unquote(self.request.body).rstrip('='))
    attributes = message['message']['attributes']

    self.response.status = 204

    event_type = attributes.get('eventType')
    photo_name = attributes.get('objectId')
    generation_number = str(attributes.get('objectGeneration'))
    overwrote_generation = attributes.get('overwroteGeneration')
    overwritten_by_generation = attributes.get('overwrittenByGeneration')
    email = attributes.get('requesterEmailAddress')

    # Add known contributors to datastore if not already added.
    # Contributors are those who have performed actions on the album,
    # not necessarily just those who have uploaded photos.
    if email is None:
      email = 'Unknown'
    '''else:
      # Only add contributor if not already in datastore.
      this_contributor = Contributor.query(email=email).fetch()
      if len(this_contributor.keys()) == 0:
        # Specify some default photo to create contributor with here
        new_contributor = Contributor(email=email)
        new_contributor.put()
    
    index = photo_name.index(".JPG")
    thumbnail_key = photo_name[:index] + generation_number + photo_name[index:]

    # Check to make sure user is not attempting invalid profile picture upload.
    # If so, send specialized notification and do not perform any
    # action with thumbnails or photos.
    if photo_name.startswith('profile-'):
        new_notification = create_notification(photo_name, email, invalid_profile=True)
        new_notification.put()
        return'''

    # Check if user is attempting to upload profile picture for themself.
    expected_profile_pic = 'profile-' + email + '.jpg'
    profile = False
    if photo_name == expected_profile_pic:
      is_profile = True # Might be repetitive with following line
      new_notification = create_notification(photo_name, event_type, email, generation_number, overwrote_generation=overwrote_generation, overwritten_by_generation=overwritten_by_generation, profile=True)
    else:
      new_notification = create_notification(photo_name, event_type, email, generation_number, overwrote_generation=overwrote_generation, overwritten_by_generation=overwritten_by_generation)
    notifications = Notification.query().fetch()
    for notification in notifications:
      if new_notification == notification:
        return
    new_notification.put() # put into database

    # If create message: get photo from photos gcs bucket, shrink to thumbnail,
    # and store thumbnail in thumbnails gcs bucket. Store thumbnail reference in
    # datastore.

    '''if event_type == 'OBJECT_FINALIZE':
      image = get_photo(photo_name, PHOTO_BUCKET) # not implemented
      thumbnail = get_thumbnail(image)
      store_thumbnail_in_gcs(self, thumbnail_key, thumbnail) # store under name thumbnail_key. Not implemented
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
      thumbnail_reference.key.delete()'''
    # No action performed if event_type is OBJECT_UPDATE

    # self.response.status = 204

# Create notification
def create_notification(photo_name, event_type, requester_email_address, generation, overwrote_generation=None, overwritten_by_generation=None, profile=False, invalid_profile=False):
  if invalid_profile:
    message = 'Invalid profile picture update attempted: ' + photo_name + '.'
  elif profile:
    if event_type == 'OBJECT_FINALIZE':
      message = requester_email_address + ' uploaded a new profile picture.'
    elif event_type == 'OBJECT_ARCHIVE' or event_type == 'OBJECT_DELETE':
      message = requester_email_address + ' has removed their old profile picture.'
  else:
    if event_type == 'OBJECT_FINALIZE':
      if overwrote_generation is not None:
        message = photo_name + ' was uploaded by ' + requester_email_address + ' and overwrote an older version of itself.'
      else:
        message = requester_email_address + ' uploaded ' + photo_name + '.'
    elif event_type == 'OBJECT_ARCHIVE':
      if overwritten_by_generation is not None:
        message = photo_name + ' was overwritten by a newer version, uploaded by ' + requester_email_address + '.'
      else:
        message = photo_name + ' was archived by ' + requester_email_address + '.'
    elif event_type == 'OBJECT_DELETE':
      if overwritten_by_generation is not None:
        message = photo_name + ' was overwritten by a newer version, uploaded by ' + requester_email_address + '.'
      else:
        message = photo_name + ' was deleted by ' + requester_email_address + '.'
    else:
      message = 'The metadata of ' + photo_name + ' was updated by ' + requester_email_address + '.'

  return Notification(message=message, generation=generation)

# Shrinks a given image to thumbnail size.
'''def get_thumbnail(image):
  image.resize(width=80, height=100)
  return image.execute_transforms(output_encoding=images.JPEG)

# Retrieve photo from GCS
# Note: file must be closed elsewhere
def get_photo(photo_name, bucket):
  filename = '/gs/' + bucket + '/' + photo_name
  gcs_file = gcs.open(filename)
  return gcs_file.read()

# Write photo to GCS thumbnail bucket
def store_thumbnail_in_gcs(self, thumbnail_key, thumbnail, bucket):
  write_retry_params = gcs.RetryParams(backoff_factor=1.1)
  filename = '/gs/' + bucket + '/' + thumbnail_key
  gcs_file = gcs.open(filename, retry_params=write_retry_params)
  gcs_file.write(thumbnail)
  gcs_file.close()
  self.tmp_filenames_to_clean_up.append(filename)

# Delete thumbnail from GCS bucket
def delete_thumbnail(thumbnail_key, bucket):
  filename = '/gs/' + bucket + '/' + thumbnail_key
  files.delete(filename)'''

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    #('/photos', PhotosHandler),
    ('/contributors', ContributorsHandler),
    ('/_ah/push-handlers/receive_message', ReceiveMessage)
], debug=True)
