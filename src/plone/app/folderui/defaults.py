"""
defaults.py -- default components for configuration and setup code for default
facets configuration.
"""

from zope.interface import implements
from interfaces import ( IFacetPathRules, IFacetSettings, IFacetSpecification,
    IFilterSpecification, FACETS_ALL, )
from zope.component import getGlobalSiteManager
from zope.schema import getFieldsInOrder, getFieldNames
from zope.schema.fieldproperty import FieldProperty


class BaseFilterSpecification(object):
    """Base (transient) filter specification object"""
    
    implements(IFilterSpecification)
    
    for _fieldname, _field in getFieldsInOrder(IFilterSpecification):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self):
        pass


class BaseFacetSpecification(object):
    """Base (transient) facet specification object"""
    
    implements(IFacetSpecification)
    
    for _fieldname, _field in getFieldsInOrder(IFacetSpecification):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, name, **kwargs):
        self.filters = []
        for k,v in kwargs.items():
            if k in getFieldNames(IFacetSpecification):
                setattr(self, k, v)
    
    def __call__(self):
        raise NotImplementedError('todo') #TODO


class BaseSettings(object):
    """
    Default transient mapping of configuration, mapping facet names to 
    IFacetSpecification objects.
    """
    
    implements(IFacetSettings)
    
    def __init__(self, *args):
        self._facets = {} # facet name (str) --> IFacetSpecification
        for arg in args:
            if IFacetSpecification.providedBy(arg):
                self._facets[arg.name] = arg
    
    def __getitem__(self, name):
        return self._facets.__getitem__(name)
    
    def __setitem__(self, name, value):
        self._facets.__setitem__(k,v)
    
    def __contains__(self, name):
        return self._facets.__contains__(name)
    
    def __len__(self):
        return len(self._facets)
    
    def __iter__(self):
        return self._facets.__iter__()
    
    def keys(self):
        return list(self._facets.keys())
    
    def values(self):
        return list(self._facets.values())
    
    def items(self):
        return list(self._facets.items())
    
    def iterkeys(self):
        return self._facets.iterkeys()
    
    def itervalues(self):
        return self._facets.itervalues()
    
    def iteritems(self):
        return self._facets.iteritems()
        
    def __delitem__(self, name):
        del(self._facets[name])


class BasePathRules(object):
    """
    Default transient global utility for path predicates mapped to 
    names of facets
    """
    
    implements(IFacetPathRules)
    
    def __init__(self):
        self._whitelist = {}
        self._blacklist = {}
    
    @property
    def whitelist(self):
        return dict(self._whitelist)
    
    @property
    def blacklist(self):
        return dict(self._blacklist)
    
    def include(self, expr, names=()):
        existing = self._whitelist.get(expr, [])
        self._whitelist[expr] = tuple(set(existing + list(names)))
    
    def exclude(self, expr, names=()):
        if names == FACETS_ALL:
            self._blacklist[expr] = FACETS_ALL
            return
        existing = self._blacklist.get(expr, [])
        self._blacklist[expr] = tuple(set(existing + list(names)))
    
    def reset(self, expr):
        self._whitelist[expr] = ()
    
    def _disabled_for(self, path):
        if path in self.blacklist:
            return self.blacklist[path] == FACETS_ALL
        return False
    
    def _list_path(self, path):
        included = set()
        excluded = set()
        if path in self._whitelist:
            included = set(self.whitelist[path])
        if path in self._blacklist:
            excluded = set(self.blacklist[path])
        return (included, excluded)
    
    def __call__(self, value):
        result = set()
        for i in range(len(value)+1):
            if self._disabled_for(value):
                # disable for path deeper levels can override this, but must
                # do so with specific facet names.
                result = set()
            else:
                included, excluded = self._list_path(tuple(value[0:i]))
                result = (result | included) - excluded
        return tuple(result) #note: facet order not determined here


FACETS = BaseSettings(
    BaseFacetSpecification(
        name=u'owner',
        title=u'Owner',
        description=u'Owner of content',
        multiset=False,
        filters=[],
        query_vocabulary=True, ),
)

