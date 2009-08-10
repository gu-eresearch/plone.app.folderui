"""
defaults.py -- default components for configuration and setup code for default
facets configuration.
"""

from zope.interface import implements
from zope.component import getGlobalSiteManager, queryUtility, IFactory
from zope.schema import getFieldsInOrder, getFieldNames
from zope.schema.fieldproperty import FieldProperty
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary
from BTrees.IIBTree import IISet, intersection

from interfaces import ( IFacetPathRules, IFacetSettings, IFacetSpecification,
    IQueryFilter, IFilterSpecification, IDateRange, IDateRangeFactory,
    ISetCacheTools, IQueryResults, FACETS_ALL, is_daterange, )
import vocab #triggers utility registration, TODO: move reg. to ZCML
from daterange import RANGES
from utils import dottedname, sitemanager_for
from catalog import AdvancedQueryRunner
from query import date_range_filter


class BaseFilterSpecification(object):
    """Base (transient) filter specification object"""
    
    implements(IFilterSpecification)
    
    for _fieldname, _field in getFieldsInOrder(IFilterSpecification):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            if k=='value' and isinstance(v, str):
                self.value = v.decode('utf=8')
                continue
            elif k in getFieldNames(IFilterSpecification):
                setattr(self, k, v)
    
    @property
    def token(self):
        v = self.value
        if IDateRangeFactory.providedBy(v) or IDateRange.providedBy(v):
            return str(self.name)
        if not self.value and self.name:
            return str(self.name)
        return repr(self.value)
    
    def count(self, context, facet, intersect=None):
        if IQueryResults.providedBy(intersect):
            intersect = IISet(intersect.keys())
        sm = sitemanager_for(context)
        unique_name = '%s.%s' % (facet.name, self.name)
        cache_tools = queryUtility(ISetCacheTools, context=sm)
        invalidated = cache_tools.invalidated_records
        if not isinstance(invalidated, IISet):
            invalidated = IISet(invalidated)
        if isinstance(intersect, IISet):
            invalid = len(intersection(intersect, invalidated)) > 0
        if unique_name in cache_tools.filter_setid_cache:
            setid = cache_tools.filter_setid_cache[unique_name]
            if setid in cache_tools.set_cache:
                if invalid:
                    del(cache_tools.set_cache[setid])
                    del(cache_tools.filter_setid_cache[unique_name])
                else:
                    records = cache_tools.set_cache[setid]
                    if intersect is None:
                        return len(records)
                    if isinstance(intersect, IISet):
                        #optimal to cast smaller set to match IISet.
                        return len(intersection(intersect, IISet(records)))
                    return len(set(intersect) & records)
        #otherwise, at this point, no cached value, so query catalog...
        qf = self(unique_name)
        runner = AdvancedQueryRunner(context)
        result = runner(qf)
        setid = result.setid
        cache_tools.set_cache[setid] = result.frozen
        cache_tools.filter_setid_cache[unique_name] = setid
        if intersect is None:
            return len(result)
        if isinstance(intersect, IISet):
            return len(intersection(intersect, IISet(result.frozen)))
        return len(set(intersect) & result.frozen)
    
    def __call__(self, unique_name=None):
        v = self.value
        if IDateRangeFactory.providedBy(v) or IDateRange.providedBy(v):
            qf = date_range_filter(v)
        else:
            factory = queryUtility(IFactory, dottedname(IQueryFilter))
            qf = factory()
            qf.value = v
            qf.query_range = self.query_range
        if self.index:
            qf.index = self.index
        qf.negated = self.negated
        if unique_name is not None:
            qf.uid = str(unique_name)
        return qf


class BaseFacetSpecification(object):
    """Base (transient) facet specification object"""
    
    implements(IFacetSpecification)
    
    for _fieldname, _field in getFieldsInOrder(IFacetSpecification):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, name, **kwargs):
        self.filters = []
        self.name = unicode(name)
        for k,v in kwargs.items():
            if k in getFieldNames(IFacetSpecification):
                setattr(self, k, v)
    
    def _bind_index(self, seq, name):
        """bind index name to filters"""
        for filter_spec in seq:
            filter_spec.index = unicode(name)
    
    def __call__(self, context):
        static = SimpleVocabulary(terms=self.filters) #static vocab via filters
        if self.index:
            self._bind_index(static, self.index)
        if self.query_vocabulary:
            dynamic = queryUtility(IVocabularyFactory, name=str(self.name))
            if dynamic:
                v = dynamic(context) #dynamic vocab, sourced from named utility
                if self.index:
                    self._bind_index(v, self.index)
                if self.filters:
                     #hybrid static/dynamic vocab
                    return SimpleVocabulary(terms=list(v)+list(static))
                return SimpleVocabulary(terms=v)
        return SimpleVocabulary(terms=self.filters) #static vocab via filters


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


## factories for config
def facets(*args):
    return BaseSettings(*args)


def facet(**kwargs):
    if 'name' not in kwargs:
        raise ValueError('name argument is required')
    return BaseFacetSpecification(**kwargs)


def daterange_facet(**kwargs):
    kw = dict(kwargs.items())
    if 'ranges' in kw:
        ranges = kwargs.get('ranges',{})
        del(kw['ranges'])
    f = facet(**kw)
    f.filters = []
    for k,v in ranges.items():
        if not is_daterange(v):
            raise ValueError('Value is not date range or range factory.')
        df = BaseFilterSpecification()
        df.title = df.name = unicode(k)
        df.value = v
        f.filters.append(df)
    return f


# facets config mapping: register this as IFacetSettings utility in ZCML
FACETS = facets(
    facet(
        name=u'text',
        title=u'Text search',
        description=u'Searchable full text.',
        index=u'SearchableText',
        multiset=True,
        filters=[],
        query_vocabulary=False,
        use_vocabulary=False, ),
    facet(
        name=u'creator',
        title=u'Creator',
        description=u'Content created by',
        multiset=False,
        filters=[],
        query_vocabulary=True, ),
    facet(
        name=u'type',
        title=u'Content type',
        index=u'Type',
        description=u'Content type',
        multiset=False,
        filters=[],
        query_vocabulary=True, ),
    facet(
        name=u'categories',
        title=u'Categories',
        index=u'Subject',
        description=u'Categories/tags/subjects',
        multiset=True,
        filters=[],
        query_vocabulary=True, ),
    daterange_facet(
        name=u'Modified',
        title=u'Modification date',
        index=u'modified',
        description=u'Date item was modified.',
        multiset=True,
        ranges=RANGES,
        query_vocabulary=False, ),
)

