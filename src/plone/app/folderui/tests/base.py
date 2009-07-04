from Products.Five import zcml, fiveconfigure

from DateTime.DateTime import DateTime


from Testing import ZopeTestCase as ztc
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup

from Products.CMFCore.utils import getToolByName
import plone.app.folderui

sample_content = [
    {'portal_type': 'Document',
     'id': 'document1',
     'title': 'Document 1',
     'categories': ['one', 'document'],},
    {'portal_type': 'Document',
     'id': 'document2',
     'title': 'Document 2',
     'categories': ['two', 'document'],},
    {'portal_type': 'News Item',
     'id': 'newsitem1',
     'title': 'News Item 1',
     'categories': ['one', 'news item'],},
    {'portal_type': 'News Item',
     'id': 'newsitem2',
     'title': 'News Item 2',
     'categories': ['two', 'news item'],},
    {'portal_type': 'Event',
     'id': 'event1',
     'title': 'Event 1',
     'categories': ['one', 'event'],
     'start_date': '2009-01-01',
     'end_date': '2009-01-10',
     'location': 'location1'},
    {'portal_type': 'Event',
     'id': 'event2',
     'title': 'Event 2',
     'categories': ['two', 'event'],
     'start_date': '2009-01-05',
     'end_date': '2009-01-15',
     'location': 'location2'},
]

@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml', plone.app.folderui)
    fiveconfigure.debug_mode = False

    ztc.installPackage('plone.app.folderui')


setup_product()
ptc.setupPloneSite(products=['example.tests'])


class BaseTestCase(ptc.PloneTestCase):

    def afterSetUp(self):
        self.catalog = getToolByName(self.portal, 'portal_catalog')
        self.workflow = getToolByName(self.portal, 'portal_workflow')
        self.membership = getToolByName(self.portal, 'portal_membership')
        self.loginAsPortalOwner()
        #remove all content so we don't get it in catalog queries.
        content_ids = self.portal.contentIds()
        self.portal.manage_delObjects(content_ids)
        self.catalog.refreshCatalog(clear=1)

    def add_member(self, username, fullname="", roles=('Manager',),
                  last_login_time=None):
        self.membership.addMember(username, 'secret', roles, [])
        member = self.membership.getMemberById(username)
        member.setMemberProperties({'fullname': fullname, 'email': '',
                                    'last_login_time': DateTime(last_login_time),})

    def add_samples(self):
        for item in sample_content:
            self.add_content(**item)

    def add_content(self,
                    id,
                    portal_type = 'Document',
                    title = None,
                    description = '',
                    categories = ['all'],
                    start_date = '2009-01-01',
                    end_date   = '2009-01-01',
                    location   = 'somewhere',
                    username = None,
                    workflow_action = None,):
        """
        convenience method.
        title   default: same as id
        username: ... of an existing member that should be used to create the
                  content
        wf_action: the name of an workflow action if the initial state should
                   be changed
        
        only for events:
        start_date
        end_date
        location
        """

        old_username = None
        if username is not None:
            old_member = self.membership.getAuthenticatedMember().getUserName()
            self.login(username)
        else:
            self.loginAsPortalOwner()

        if title is None:
            title = id
        
        self.portal.invokeFactory(portal_type, id)
        content = self.portal[id]
        content.setTitle(title)
        content.setDescription(description)
        content.setSubject( '\n'.join(categories) )
        if portal_type == 'Event':
            content.setStartDate(start_date)
            content.setEndDate(end_date)
            content.setLocation(location)
            
        if workflow_action is not None:
            self.workflow.doActionFor(content, workflow_action)

        content.reindexObject()
        
        if old_username is not None:
            self.login(old_username)
            
        return content        


