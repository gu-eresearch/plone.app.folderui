"""
catalog.py: ZCatalog+AdvancedQuery query runner implementation for folderui
faceted searching.
"""

from zope.interface import implements
from zope.component import adapter
from Products.AdvancedQuery import AdvancedQuery
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr

from interfaces import IQueryFilter, IComposedQuery, IQueryRunner, ICatalogQueryFilter
from result import IterableCatalogResults


@adapter(IQueryFilter)  # returns AdvancedQuery query object
def aquery_filter(qf, filter=False):
    """
    given qf object providing IQueryFilter, generate, return AdavancedQuery
    object; if filter=True assuming incremental filtering.
    """
    if type(qf.value) in (list, set, tuple):
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
        elif len(terms) >= 2:
            q = AdvancedQuery.Between(index,
                terms[0],  # low
                terms[1],
                filter=filter)
        else:
            raise RuntimeError('unable to create range query')
    else:
        #no range: Eq query, use first term in qf.terms, ignore others
        q = AdvancedQuery.Eq(index, terms[0], filter=filter)
    if qf.negated:
        return ~q  # negated == q.__invert__()
    return q


def optimize_query_order(queries):
    """
    reorder sequence of incremental AdvancedQuery query objects as needed
    (ad-hoc query plan)
    """
    pass  # TODO later when/as needed, now returns queries as-is
    return queries


@adapter(IComposedQuery)  # returns AdvancedQuery composite query object
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
        # skip all non catalog queries
        if not ICatalogQueryFilter.providedBy(qf):
            continue
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
    for index in [k for k, v in queries.items() if isinstance(v, list)]:
        intraindex_conjunction = conjunctions[index]
        queries[index] = intraindex_conjunction(*queries[index])  # list->And/Or
    if extra is not None:
        if isinstance(extra, AdvancedQuery._BaseQuery):
            extra = [extra]
        extra = list(extra)
        for q in extra:
            somekey = 'extra%s' % extra.index(q)  # unused, but must be unique
            queries[somekey] = q  # add query value for use
    return conjunction(*optimize_query_order(queries.values()))


from zope.component import getUtility
from gu.z3cform.rdf.interfaces import IORDF


def mkqueryfromsparql(composed):
    """
    query sparql endpoint, and turn list of returned uri's into
    an AdvancedQuery Object to be added to the standard catalog query
    """
    # composed can be a IQueryFilter or q IComposedQuery .....
    #
    # TODO: what to do if it is a IQueryFilter? why is it just a filter at all?
    # (probably the same so we do, but just on filter if at all; will be solved
    # by detailed refactoring)
    queries = {}

    if IComposedQuery.providedBy(composed):
        for qf in composed.filters:
            if hasattr(qf, 'filterspec'):
                filterspec = qf.filterspec
                facet = filterspec.facet
                tool = getUtility(IORDF)
                result = tool.getHandler().query(
                    facet.resultquery % {'value': qf.value})  # filterspec.value
                # TODO: do a lazymap here?
                subjecturis = [unicode(x[0]) for x in result]
                query = AdvancedQuery.In('subjecturi', subjecturis)
                if facet.name in queries:
                    if isinstance(queries[facet.name],
                                  AdvancedQuery._CompositeQuery):
                        queries[facet.name].addSubquery(query)
                    else:
                        # need conjunction of results
                        conj = {'AND': AdvancedQuery.And,
                                'OR': AdvancedQuery.Or}[qf.conjunction]
                        queries[facet.name] = conj(queries[facet.name], query)
                else:
                    queries[facet.name] = query
    if queries:
        return AdvancedQuery.And(*queries.values())
    return None


class AdvancedQueryRunner(object):
    implements(IQueryRunner)

    def __init__(self, context):
        self.context = context

    def _get_catalog(self):
        catalog = getToolByName(self.context, 'portal_catalog')
        assert base_hasattr(catalog, 'evalAdvancedQuery')
        return catalog

    def __call__(self, composed, include_subfolders=False):
        # TODO: fails in here to query gender index ....
        #       need some better query processing here
        #  e.g. run all catalog queries against AdvancedQuery
        #       run all sparql queries against sparql query runner
        #       merge results
        # TODO: check query definition format, might be suitable for
        # Collections too?
        if not (IComposedQuery.providedBy(composed) or
            IQueryFilter.providedBy(composed)):
            raise ValueError('query must provide proper interface')
        catalog = self._get_catalog()
        if IQueryFilter.providedBy(composed):
            # if we get IQueryFilter, just query catalog globally for just
            # this one filter/index, without regard to path.
            # the major use for this is filter-link-counts, assuming that
            # set intersections will be computed from caches/indexes outside
            # the catalog.
            query = aquery_filter(composed)
        else:
            # restrict query to context/folder path:
            if u'path' not in [f.index for f in composed.filters]:
                path = '/'.join(self.context.getPhysicalPath())
                if include_subfolders:
                    pathq = AdvancedQuery.And(
                        AdvancedQuery.Generic('path',
                            {'query': path, 'depth':-1}),  # all within hierarchy
                        AdvancedQuery.Not(
                            AdvancedQuery.Generic('path',
                            {'query': path, 'depth':0}))  # not folder itself
                        )
                else:
                    pathq = AdvancedQuery.Generic('path',
                        {'query': path, 'depth': 1})
            else:
                # path was specified in query either to include subfolder
                # contents or to use a different folder path from current
                # context.
                pathq = None
            # build query, pass path
            query = mkaquery(composed, extra=pathq)

        sparqlquery = mkqueryfromsparql(composed)
        if sparqlquery is not None:
            query.addSubquery(sparqlquery)

        res = catalog.evalAdvancedQuery(query)

        return IterableCatalogResults(res, catalog)
