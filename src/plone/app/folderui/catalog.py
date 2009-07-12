"""
catalog.py: ZCatalog+AdvancedQuery query runner implementation for folderui
faceted searching.
"""

from zope.interface import implements
from zope.component import adapts, adapter
from Products.AdvancedQuery import AdvancedQuery
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.ZCatalog.Lazy import Lazy, LazyMap, LazyCat

from interfaces import IQueryFilter, IComposedQuery, IQueryRunner
from zope2 import datetime_to_zopedt as z2date
from result import IterableCatalogResults


@adapter(IQueryFilter) #returns AdvancedQuery query object
def aquery_filter(qf, filter=False):
    """
    given qf object providing IQueryFilter, generate, return AdavancedQuery
    object; if filter=True assuming incremental filtering.
    """
    if type(qf.value) in (list,set,tuple):
        terms = qf.value
    else:
        terms = (qf.value,)
    q = None
    if not IQueryFilter.providedBy(qf):
        raise ValueError('abstract query must provide IQueryFilter interface')
    index = str(qf.index)
    if qf.query_range is not None:
        #Le, Ge, or Between query
        if qf.query_range == 'min':
            q = AdvancedQuery.Ge(index, terms[0], filter=filter)
        if qf.query_range == 'max':
            q = AdvancedQuery.Le(index, terms[0], filter=filter)
        elif len(terms)>=2:
            q = AdvancedQuery.Between(index,
                terms[0], #low
                terms[1], #
                filter=filter)
        else:
            raise RuntimeError('unable to create range query')
    else:
        #no range: Eq query, use first term in qf.terms, ignore others
        q = AdvancedQuery.Eq(index, terms[0], filter=filter)
    if qf.negated:
        return ~q #negated == q.__invert__()
    return q


def optimize_query_order(queries):
    """
    reorder sequence of incremental AdvancedQuery query objects as needed
    (ad-hoc query plan)
    """
    pass #TODO later when/as needed, now returns queries as-is
    return queries


@adapter(IComposedQuery) #returns AdvancedQuery composite query object
def mkaquery(composed, extra=None):
    """
    given an object providing IComposedQuery, make an AdvancedQuery
    representing that query and all contained IQueryFilter objects.
    """
    if not IComposedQuery.providedBy(composed):
        raise ValueError('query must provide IComposedQuery interface')
    conjunction = {'AND': AdvancedQuery.And,
        'OR': AdvancedQuery.Or}[composed.interindex_operator]
    queries = {}
    conjunctions = {}
    for qf in composed.filters:
        if qf.index in queries:
            #more than one query to same index
            query = queries[qf.index]
            if isinstance(query, list):
                query.append(aquery_filter(qf))
            else:
                queries[qf.index] = [query, aquery_filter(qf)]
                conjunctions[qf.index] = {'AND': AdvancedQuery.And,
                    'OR': AdvancedQuery.Or}[qf.conjunction]
        else:
            queries[qf.index] = aquery_filter(qf)
    for index in [k for k,v in queries.items() if isinstance(v,list)]:
        intraindex_conjunction = conjunctions[index]
        queries[index] = intraindex_conjunctions(*queries[index]) #list->And/Or
    if extra is not None:
        if isinstance(extra, AdvancedQuery._BaseQuery):
            extra = [extra]
        extra = list(extra)
        for q in extra:
            somekey = 'extra%s' % extra.index(q) #unused, but must be unique
            queries[somekey] = q #add query value for use
    return conjunction(*optimize_query_order(queries.values()))


class AdvancedQueryRunner(object):
    implements(IQueryRunner)
    
    def __init__(self, context):
        self.context = context
    
    def _get_catalog(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        assert base_hasattr(catalog, 'evalAdvancedQuery')
        return catalog
    
    def __call__(self, composed):
        if not IComposedQuery.providedBy(composed):
            raise ValueError('query must provide IComposedQuery interface')
        catalog = self._get_catalog()
        # restrict query to context/folder path:
        if u'path' not in [f.index for f in composed.filters]:
            path = '/'.join(self.context.getPhysicalPath())
            pathq = AdvancedQuery.Generic('path', {'query': path, 'depth':1})
        else:
            # path was specified in query either to include subfolder contents
            # or to use a different folder path from current context.
            pathq = None
        # build query, pass path
        query = mkaquery(composed, extra=pathq)
        res = catalog.evalAdvancedQuery(query)
        #TODO: support sorting!
        return IterableCatalogResults(res, catalog)


