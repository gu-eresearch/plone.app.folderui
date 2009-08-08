import unittest

from plone.app.folderui.defaults import BaseFilterSpecification
from plone.app.folderui.interfaces import IQueryFilter


class FilterTest(unittest.TestCase):
    def setUp(self):
        from plone.app.folderui.config import register_defaults
        register_defaults()
 
    def test_call_spec(self):
        """
        calling BaseFilterSpecification obj should return object 
        providing IQueryFilter.
        """
        spec = BaseFilterSpecification()
        spec.index = u'creator'
        spec.value = 'admin'
        spec.name = u'creator'
        spec.title = u'Creator'
        qf = spec()
        assert IQueryFilter.providedBy(qf)
        assert spec.index == qf.index
        assert spec.value == qf.value
        assert spec.query_range == qf.query_range


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FilterTest))
    return suite


if __name__ == '__main__':
    unittest.main()

