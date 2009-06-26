"""
result.py : present catalog results as iterable mapping, while not
foregoing advantages of lazy sequences.  The primary purpose of doing this
is to support use-cases where it is helpful to keep the catalog record ids,
for calculating (and possibly caching) set intersections for faceted
search.
"""

from zope.interface import implements
from interfaces import IQueryResults, ILazySequence
from zope.component import adapts


try:
    from Products.ZCatalog.interfaces import IZCatalog
    from Products.ZCatalog.Lazy import Lazy, LazyCat, LazyMap
    islazymap = lambda o: isinstance(o, LazyMap)
    islazycat = lambda o: isinstance(o, LazyCat)
    islazy = lambda o: isinstance(o, Lazy)
except ImportError:
    # for use of Lazy sequences outside of Zope2 (standalone Lazy.py)
    classname = lambda o: o.__class__.__name__
    islazymap = lambda o: classname(o) == 'LazyMap'
    islazycat = lambda o: classname(o) == 'LazyCat'
    islazy = lambda o: classname(o) in ('Lazy', 'LazyMap', 'LazyCat')


_marker = object()


class CatalogRIDValuesIterator(object):
    def __init__(self, catalog, keyiter):
        self._catalog = catalog
        self._keyiter = keyiter
    def __iter__(self):
        return self
    def next(self):
        k = self._keyiter.next() #get next key
        return self._catalog[k]


class CatalogRIDItemsIterator(CatalogRIDValuesIterator):
    def next(self):
        k = self._keyiter.next() #get next key
        return (k, self._catalog[k])


class IterableCatalogResults(object):
    """
    Iterable mapping that proxies to underlying LazyMap returned by catalog
    query, providing a stable means of access to integer record ids without
    having to forego advantages of Lazy sequences returned by catalog.
    
    The primary reason for this class is to make acessing record ids for a
    result easy and simple.
    
    IterableCatalogResults multi-adapts a LazyMap of returned results
    and the catalog that generated the results; it provides integer record
    ids as keys, and the brains one normally gets from iterating a LazyMap
    as iterable values.  Calling IterableCatalogResults.values() returns
    the adapted LazyMap; calling itervalues(), however, bypasses the LazyMap
    and uses the underlying sequence of integer record ids and catalog item
    access to get a brain as needed -- accomplishes similar end of only 
    fetching catalog brains/records as needed (though lazy sequences are
    better than iterators for slices and batching).
    """
    
    implements(IQueryResults)
    
    if 'IZCatalog' in globals():
        adapts(ILazySequence, IZCatalog)
    
    def __init__(self, context, catalog):
        if not islazy(context):
            raise TypeError('context does not appear to be lazy type.')
        #if not IZCatalog.providedBy(catalog):
        #    raise ValueError('catalog does not provide IZCatalog.')
        self.context = context # LazyMap results
        self.catalog = catalog
    
    def __getitem__(self, key):
        return self.catalog[key] #key is catalog record id
    
    def get(self, key, default=_marker):
        try:
            return self.__getitem__(key)
        except KeyError:
            if default is _marker:
                return None
            return default
    
    def _keys(self):
        if islazymap(self.context):
            if not hasattr(self, '_catalog_rids'):
                try:
                    self._catalog_rids = list(self.context._seq)
                except AttributeError:
                    # LazyMap instance _seq undefined, means _data is
                    # populated with all brains, and we need to get RIDs from 
                    # brains; this is less than ideal, but less common...
                    self._catalog_rids = [b.getRID() 
                        for b in self.context._data]
            return self._catalog_rids
        raise NotImplementedError('LazyCat not supported yet.') #TODO
    
    def keys(self):
        return self._keys()
    
    def values(self):
        """Returns LazyMap of brains (raw result from catalog)"""
        return self.context #returns LazyMap of result values
    
    def items(self):
        """Returns LazyMap of (rid, brain) tuples"""
        fitem = lambda v: (v, self.catalog[v])
        return LazyMap(fitem, self._keys())
    
    def __iter__(self):
        return self.iterkeys()
    
    def iterkeys(self):
        return self._keys().__iter__()
    
    def itervalues(self):
        return CatalogRIDValuesIterator(self.catalog, self.iterkeys())
    
    def iteritems(self):
        return CatalogRIDItemsIterator(self.catalog, self.iterkeys())
    
    def __len__(self):
        return len(self._keys())
    
    def __add__(self, other):
        """
        Add two IterableCatalogResults items together using LazyCat as
        backend, supposes LazyCat support in this class""" #TODO
        raise NotImplementedError('todo') #TODO


