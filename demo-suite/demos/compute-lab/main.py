__author__ = 'peersp'

import lib_path
import google_cloud.oauth as oauth
import google_cloud.gce as gce
import google_cloud.gce_appengine as gce_appengine
import jinja2
import webapp2
import oauth2client.appengine as oauth2client

from google.appengine.api import users

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

        #Get data from form.
        project_id = self.request.get('project-id')
        lab_zone = self.request.get('lab-zone')
        instance_image = self.request.get('instance-image')
        machine_type = self.request.get('machine-type')

        #Get credentials stored in datastore
        user_id = users.get_current_user().user_id()
        credentials = oauth2client.StorageByKeyName(
        oauth2client.CredentialsModel, user_id, 'credentials').get()

        #Configure project object
        gce_project = gce.GceProject(credentials, project_id=project_id, zone_name=lab_zone)

        #Configure network
        network = gce.Network('default')
        network.gce_project = gce_project
        networks = [{'accessConfigs': [{'type': 'ONE_TO_ONE_NAT',
                                       'name': 'External NAT'}],
                    'network': network.url}]

        #Configure disks (must be iterable list)
        disks = [gce.DiskMount(
            boot=True,
            auto_delete=True,
            init_disk_image=instance_image)]

        #Compile instance object
        instance = gce.Instance(
            name="test-instance",
            zone_name=lab_zone,
            machine_type_name=machine_type,
            network_interfaces=networks,
            disk_mounts=disks)

        #Send response
        response = gce_appengine.GceAppEngine().run_gce_request(
            self,
            gce_project.insert,
            'Error inserting instances: ',
            resource=instance)


app = webapp2.WSGIApplication(
    [
        ('/compute-lab', Main),
        ('/compute-lab/new', CreateLab)
    ],
    debug=True)