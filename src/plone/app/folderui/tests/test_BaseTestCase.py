import unittest
from plone.app.folderui.tests.base import BaseTestCase

class TestAddContent(BaseTestCase):
    ''' tests for BaseTestCase '''
    
    def test_add_event(self):
        content = self.add_content(id = 'an_event',
                                   portal_type = 'Event',
                                   start_date = '2009-01-02',
                                   end_date= '2009-01-03',
                                   )
        self.assertTrue(content.Title() == 'an_event')
        self.assertTrue(content.getId() == 'an_event')
        self.catalog()
        
    def test_cataloging(self):
        content = self.add_content(id = 'catalogtest')
        results = self.catalog(Title='catalogtest')
        self.assertTrue(len(results)==1)

    def test_samples(self):
        self.add_samples()
        results = self.catalog(portal_type='Document')
        self.assertTrue(len(results) == 2)
        results = self.catalog()
        self.assertTrue(len(results) == 6)

    def test_publish(self):
        content = self.add_content(id = 'publishtest',
                                   workflow_action = 'publish')

        chain = self.workflow.getChainFor(content)
        wf_state = self.workflow.getStatusOf(chain[0], content)
        self.assertTrue(wf_state['review_state'] == 'published')
        
    def test_owner(self):
        self.add_member('testuser', '_')
        content = self.add_content('testcontent',
                         username='testuser')
        self.assertTrue(content.Creator() == 'testuser')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAddContent))
    return suite
