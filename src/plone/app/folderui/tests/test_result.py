"""
Tests for IterableCatalogResults proxy/adapter around fake catalog, results.
"""

import unittest
from Products.ZCatalog.Lazy import Lazy, LazyCat, LazyMap
from plone.app.folderui.result import IterableCatalogResults


class FakeBrain(object):
    """brain-like only in sense that this has getRID()"""
    def __init__(self, rid=None):
        self.rid = rid
    
    def getRID(self):
        return self.rid


class FakeCatalog(object):
    """
    catalog-like only in sense that this has __getitem__() and is callable to
    return fake results; fake brains can be added with __setitem__().
    """
    def __init__(self):
        self._data = {}
    def __getitem__(self, k):
        return self._data[k]
    def __setitem__(self, k, v):
        if v.rid is None:
            v.rid = int(k)
        self._data[k] = v #add a fake brain
    def __call__(self):
        return LazyMap(self.__getitem__, self._data.keys())


class TestIterableCatalogResults(unittest.TestCase):
    
    def setUp(self):
        from plone.app.folderui.config import register_defaults
        register_defaults()
        self.cat = FakeCatalog()
        self.cat[11235813] = FakeBrain()
        self.cat[12345678] = FakeBrain()
        self.cat[11223344] = FakeBrain()
        self.orig_rids = list(self.cat()._seq)
    
    def _mk_iter_result(self):
        result = self.cat()
        return IterableCatalogResults(result, self.cat)
    
    def testKeys(self):
        """
        iterate through keys, should be original record ids, get
        same result of iteration from keys(), iterkeys(), original rids
        from catalog query.
        """
        r = self._mk_iter_result()
        assert list(r.iterkeys()) == r.keys() == self.orig_rids
    
    def testValues(self):
        """
        itervalues() uses catalog, values() returns original LazyMap. casting
        both to list should yield equivalent lists of brains in identical
        order.
        """
        r = self._mk_iter_result()
        assert list(r.itervalues()) == list(r.values())
    
    def testItems(self):
        """
        test item iteration, iterating (via cast to list) should yeild
        equavalent lists of items tuples from iteritems(), items().
        """
        r = self._mk_iter_result()
        assert list(r.iteritems()) == list(r.items()) == zip(
            self.orig_rids, list(r.values()))
    
    def testLazyKeys(self):
        """
        LazyMap gets rid of _seq attribute storing original sequence of 
        record ids from a catalog result when all items have been accessed
        through iteration; we want to ensure we still get keys via the 
        brains when this happens, though this is a slower edge case we will
        never likely trigger in production.
        """
        result = self.cat()
        assert hasattr(result, '_seq')
        dummy = list(result) #force LazyMap to iterate completely
        assert not hasattr(result, '_seq')
        r = IterableCatalogResults(result, self.cat)
        ## calling r.keys() / _keys() calls getRID() for each brain
        assert list(r.keys()) == self.orig_rids


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestIterableCatalogResults))
    return suite


if __name__ == '__main__':
    unittest.main()

