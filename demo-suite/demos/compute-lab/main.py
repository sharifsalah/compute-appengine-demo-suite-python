__author__ = 'peersp'

import lib_path
import logging
import google_cloud.oauth as oauth
import google_cloud.gce as gce
import google_cloud.gce_appengine as gce_appengine
import jinja2
import webapp2
import oauth2client.appengine as oauth2client
import json

from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import ndb
from webapp2_extras import security


jinja_environment = jinja2.Environment(loader=jinja2.FileSystemLoader(''))
oauth_decorator = oauth.decorator

class Main(webapp2.RequestHandler):
    """Show main page."""

    @oauth_decorator.oauth_required
    def get(self):

        #if no valid refresh token for scope set in oauth.py then redirect to authorise_url
        if not oauth_decorator.credentials.refresh_token:
            self.redirect(oauth_decorator.authorize_url() + '&approval_prompt=force')

        variables = {
        }

        template = jinja_environment.get_template('demos/compute-lab/templates/index.html')
        self.response.out.write(template.render(variables))

class Lab(ndb.Model):
    """Data model to record labs"""
    name = ndb.StringProperty()
    project_id = ndb.StringProperty()
    lab_zone = ndb.StringProperty()

class Instance(ndb.Model):
    """Data model to record instances"""
    name = ndb.StringProperty()
    lab = ndb.KeyProperty(kind=Lab)

class CreateLab(webapp2.RequestHandler):
    """Handler for starting a new lab."""

    @oauth_decorator.oauth_required
    def get(self):

        variables = {
        }

        template = jinja_environment.get_template('demos/compute-lab/templates/createlab.html')
        self.response.out.write(template.render(variables))

    @oauth_decorator.oauth_required
    def post(self):

        #get data from form.
        lab_name = self.request.get('lab-name')
        project_id = self.request.get('project-id')
        lab_zone = self.request.get('lab-zone')
        instance_image = self.request.get('instance-image')
        machine_type = self.request.get('machine-type')
        number_students = int(self.request.get('total-students'))

        #get credentials stored in datastore
        user_id = users.get_current_user().user_id()
        credentials = oauth2client.StorageByKeyName(
        oauth2client.CredentialsModel, user_id, 'credentials').get()

        #configure project object
        gce_project = gce.GceProject(credentials, project_id=project_id, zone_name=lab_zone)

        #configure network
        network = gce.Network('default')
        network.gce_project = gce_project
        networks = [{'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
                                       'name': 'External NAT'}],
                    'network': network.url}]

        #configure disks (must be iterable list)
        disks = [gce.DiskMount(
            boot=True,
            auto_delete=True,
            init_disk_image=instance_image)]

        #create lab entity in datastore
        lab = Lab(name=lab_name,
                  project_id=project_id,
                  lab_zone=lab_zone)
        lab.put()

        # grant read access to GCS for startup script
        scopes = [{'kind': 'compute#serviceAccount',
                   'email': 'default',
                   'scopes': ['https://www.googleapis.com/auth/devstorage.read_only']}]



        #create instance objects
        instances = []
        for n in range(number_students):

            # set the username to the name of the instance
            username = '%s-%s' % (lab_name, n)
            pass_phrase = security.generate_random_string(length=8)
            if not memcache.add(username, pass_phrase):
                  logging.error('Failed to set memcache')

            metadata_items = [
            {
                'key': 'user',
                'value': username
            },
            {
                'key': 'pass',
                'value': pass_phrase
            },
            {
                'key': 'startup-script-url',
                'value': 'gs://startup-scripts-compute/startup.sh'
            }
        ]
            instances.append(gce.Instance(
                name="%s-%s" % (lab_name, n),
                zone_name=lab_zone,
                machine_type_name=machine_type,
                network_interfaces=networks,
                disk_mounts=disks,
                metadata=metadata_items,
                service_accounts=scopes))
            instance = Instance(name="%s-%s" % (lab_name, n),
                                lab=lab.key)
            instance.put()

        #send response
        response = gce_appengine.GceAppEngine().run_gce_request(
            self,
            gce_project.bulk_insert,
            'Error inserting instances: ',
            resources=instances)

        self.redirect('/compute-lab/%s' % lab.key.id())

class LabDetails(webapp2.RequestHandler):
    """Handler for lab details page."""

    @oauth_decorator.oauth_required
    def get(self, lab_id):

        #get lab key from url compute-lab/<lab id>
        lab_name = ndb.Key('Lab', int(lab_id)).get().name

        variables = {
            'lab_id': lab_id,
            'lab_name': lab_name
        }

        template = jinja_environment.get_template('demos/compute-lab/templates/lab.html')
        self.response.out.write(template.render(variables))

class GetInstanceStatus(webapp2.RequestHandler):
    """Handler for getting lab status"""

    def post(self):

        #get data from request.
        data = json.loads(self.request.body)
        lab_id = data['lab_id']

        #create lab key
        lab_key = ndb.Key('Lab', int(lab_id))

        #get lab entity from datastore
        lab = lab_key.get()
        project_id = lab.project_id
        lab_zone = lab.lab_zone

        #get expected instances from datastore
        query = Instance.query(Instance.lab == lab_key).fetch()

        #get active instances for project, add to dictionary
        gce_project = gce.GceProject(oauth_decorator.credentials, project_id=project_id, zone_name=lab_zone)
        instances = gce_appengine.GceAppEngine().run_gce_request(self,
                                                                 gce_project.list_instances,
                                                                 'Error listing instances: ',
                                                                 # filter='name eq ^%s.*' % 'test-instance',
                                                                 maxResults='500')
        status_dict = {}
        for instance in instances:
            status_dict[instance.name] = instance.status

        #compare expected instances with active instances and produce list for passing to client side js function
        instance_list = []
        for n in range(len(query)):
            instance_name = query[n].name
            pass_phrase = memcache.get(instance_name)
            if pass_phrase is not None:
                logging.debug("Did read from memcache!")
            if instance_name in status_dict:
                instance_state = status_dict[query[n].name]
            else:
                instance_state = "NOT RUNNING"
            instance_list.append({"address": '192.168.0.1',
                                  "state": instance_state,
                                  "name": instance_name,
                                  "pass": pass_phrase})

        self.response.out.write(json.dumps(instance_list))

app = webapp2.WSGIApplication(
    [
        ('/compute-lab', Main),
        ('/compute-lab/new', CreateLab),
        ('/compute-lab/(\d+)', LabDetails),
        ('/compute-lab/get-status', GetInstanceStatus)
    ],
    debug=True)