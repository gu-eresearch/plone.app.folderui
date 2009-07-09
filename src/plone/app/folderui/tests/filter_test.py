import unittest

from plone.app.folderui.defaults import BaseFilterSpecification
from plone.app.folderui.interfaces import IQueryFilter

class FilterTest(unittest.TestCase):
    def setUp(self):
        pass
    
    def test_call_spec(self):
        """
        calling BaseFilterSpecification obj should return object 
        providing IQueryFilter.
        """
        spec = BaseFilterSpecification()
        spec.index = u'creator'
        spec.values = ('admin',)
        spec.name = u'creator'
        spec.title = u'Creator'
        qf = spec()
        assert IQueryFilter.providedBy(qf)
        assert spec.index == qf.index
        assert spec.values == qf.values
        assert spec.query_range == qf.query_range


if __name__ == '__main__':
    unittest.main()

