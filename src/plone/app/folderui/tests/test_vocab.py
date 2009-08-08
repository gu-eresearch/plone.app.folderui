import unittest
from zope.interface import implements
from plone.app.folderui.interfaces import ITitleLookup
from zope.schema.interfaces import IVocabularyTokenized
from plone.app.folderui.tests.base import BaseTestCase

from plone.app.folderui.vocab import member_fullname, all_creators_vfactory, \
     UniqueValuesFactory

class MockCatalog(object):
    def __init__(self, values=[]):
        self.values = values
        
    def uniqueValuesFor(self, index):
        return self.values

class MockContext(object):

    def __init__(self, catalog):
        self.portal_catalog = catalog

class MockTitlefn(object):
    implements(ITitleLookup)
    
    def __call__(self, value, context):
        return u'MockTitle'
        
class TestVocabularies(BaseTestCase):
    ''' tests for BaseTestCase '''

    def test_uvf(self):
        '''
        Test the UniqeValueFactory
        '''
        uvf = UniqueValuesFactory('_does_not_matter_here_')
        # empty index
        mock_context = MockContext(
            MockCatalog( values=[] )
            )
        vocabulary = uvf(mock_context)
        assert len(vocabulary) == 0
        assert IVocabularyTokenized.providedBy(vocabulary)

        # index with a value
        mock_context = MockContext(
            MockCatalog( values = ['value'] )
            )
        vocabulary = uvf(mock_context)
        assert IVocabularyTokenized.providedBy(vocabulary)
        assert len(vocabulary) == 1
        assert 'value' in vocabulary

    def test_uvf_titlefn(self):
        uvf = UniqueValuesFactory('_does_not_matter_here_', titlefn = MockTitlefn())
        # empty index
        mock_context = MockContext(
            MockCatalog( values=['value'] )
            )
        vocabulary = uvf(mock_context)
        term = vocabulary.getTerm('value')
        assert term.title == u'MockTitle'
        
    def test_fullname(self):
        '''
        give us the fullname or, if no fullname is saved, the username
        '''
        self.add_member('testuser', fullname='Test User')
        fullname = member_fullname('testuser', self.portal)
        assert fullname == 'Test User'

        self.add_member('nameless', fullname='')
        fullname = member_fullname('nameless', self.portal)
        assert fullname == 'nameless'

        self.add_member('none', fullname=None)
        fullname = member_fullname('none', self.portal)
        assert fullname == 'none'

    def test_all_creators(self):
        '''
        all_creators gives us a SimpleVocabulary with all users that have
        created content in the portal
        '''
        self.add_member('testuser', fullname='Test User')
        self.add_content('testcontent', username='testuser')
        self.add_member('second')
        vocabulary = all_creators_vfactory(self.portal)
        assert len(vocabulary) == 2
        assert 'testuser' in vocabulary

        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestVocabularies))
    return suite
