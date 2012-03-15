

from zope.component import (getUtility, adapter, IFactory, getAdapter,
                            queryUtility)
from zope.interface import implementer, implements
from zope.schema import getFieldsInOrder
from zope.schema.fieldproperty import FieldProperty
from zope.schema.vocabulary import SimpleVocabulary
from org.ausnc.rdf.interfaces import IORDF
from Products.CMFCore.utils import getToolByName
from plone.app.folderui.interfaces import (
            IFilterSpecificationFactory, ICatalogFacetSpecification,
            ISparqlFacetSpecification, IQueryFilterFactory,
    IQueryResults, IDateRange, ISparqlFilterSpecification,
    IDateRangeFactory,
    IComposedQuery, IQueryFilter)
from plone.app.folderui.defaults import (CatalogFilterSpecification,
                                         BaseFilterSpecification)
from BTrees.IIBTree import IISet, intersection
from plone.app.folderui.utils import dottedname
from plone.app.folderui.query import (date_range_filter, ComposedQuery,
                                      CatalogQueryFilter)


## Override various Factories to create correct kind of object based on input
# @provider ... the given instantiated function already provides IFactory
# @implementer ... the returned value implements this (e.g. a foctory which instances provide this)
# @adapter ... input to the adapter
@implementer(IFilterSpecificationFactory)
@adapter(ICatalogFacetSpecification)
def CatalogFilterSpecificationAdapter(facet):
    return CatalogFilterSpecification


@implementer(IFilterSpecificationFactory)
@adapter(ISparqlFacetSpecification)
def SparqlFilterSpecificationAdapter(facet):
    return SparqlFilterSpecification


# @implementer ... that's what the return value provides
# @adapter ... that's what the input needs to be
@implementer(IQueryFilterFactory)
def CatalogQueryFilterAdapter(filterspec):
    return CatalogQueryFilter


@implementer(IQueryFilterFactory)
@adapter(ISparqlFilterSpecification)
def SparqlQueryFilterAdapter(filterspec):
    return SparqlQueryFilter


class SparqlFilterSpecification(BaseFilterSpecification):

    implements(ISparqlFilterSpecification)

    def count(self, context, facet, intersect=None):
        if IQueryResults.providedBy(intersect):
            intersect = IISet(intersect.keys())

        # get query result
        tool = getUtility(IORDF)
        result = tool.getHandler().query(facet.resultquery % {'value': self.value})
        subjecturis = [unicode(x.values()[0]) for x in result]

        catalog = getToolByName(context, 'portal_catalog')
        result = catalog(subjecturi=subjecturis)
        result = [b for b in result]
        result = set([b.getRID() for b in result])
        if intersect is None:
            return len(result)
        if isinstance(intersect, IISet):
            return len(intersection(intersect, IISet(result)))
        return len(set(intersect) & result.frozen)

    def __call__(self, unique_name=None):
        """
        create a QueryFilter instance.
        """
        v = self.value
        if IDateRangeFactory.providedBy(v) or IDateRange.providedBy(v):
            qf = date_range_filter(v)
        else:
            factory = getAdapter(self, IQueryFilterFactory)
            qf = factory()
            qf.value = v
            qf.query_range = self.query_range
        if self.index:
            qf.index = self.index
        qf.negated = self.negated
        if unique_name is not None:
            qf.uid = str(unique_name)
        qf.filterspec = self
        return qf


class SparqlFacetSpecification(object):

    # name
    # vocabquery
    # resultquery
    use_vocabulary = True

    # TODO: not true yet
    implements(ISparqlFacetSpecification)

    def __init__(self, name, **kwargs):
        self.name = name
        self.description = kwargs.get('description', None)
        self.title = kwargs.get('title', None)
        self.multiset = kwargs.get('multiset', None)
        self.vocabquery = kwargs.get('vocabquery', None)
        self.resultquery = kwargs.get('resultquery', None)
        # TODO: this is probably always true
        self.use_vocabulary = kwargs.get('use_vocabulary', True)

    def __call__(self, context):
        handler = getUtility(IORDF)
        result = handler.getHandler().query(self.vocabquery)
        # TODO: result is a list of dicts with all returned values...
        #       we expect only one return column so ignore it for now
        #       we also assume here they are all literals
        result = [unicode(x.values()[0]) for x in result]
        # apply facet name to term (which should be a IFilterSpec)
        result = [SparqlFilterSpecification(name=x,
                                            title=x,
                                            token=x,
                                            value=x)
                for x in result]
        for x in result:
            x.facet = self
        return SimpleVocabulary(terms=result)


def sparqlfacet(**kwargs):
    if 'name' not in kwargs:
        raise ValueError('name argument is required')
    return SparqlFacetSpecification(**kwargs)


# multiset True .... allow selecetion of AND/OR operator of multiple values
#          False .... use default operator
# use_vocabulary True ... show selecetion af available values
#                False ... free text field ... seems like there can only be one
# multiset T, use_vocab F ... don't ever do this

PARTICIPANT_GENDER_FACET = sparqlfacet(
    name=u'foaf_gender',
    title=u'Participant Gender',
    vocabquery='select distinct ?gender where { ?o <http://xmlns.com/foaf/0.1/gender> ?gender}',
    resultquery='select distinct ?o where { ?o <http://www.language-archives.org/OLAC/1.1/speaker> ?s .'
                                           '?s <http://xmlns.com/foaf/0.1/gender> "%(value)s" }',
    # index=u'',
    description=u'Gender of participant',
    multiset=True,
    multiset_operator='AND',
    use_vocabulary=True,
    )


class SparqlQueryFilter(object):

    implements(IQueryFilter)

    for _fieldname, _field in getFieldsInOrder(IQueryFilter):
        locals()[_fieldname] = FieldProperty(_field)

    def __init__(self, index=u'', value=None, query_range=None, neg=False):
        self.index = unicode(index)
        self.value = value
        self.query_range = query_range
        self.negated = bool(neg)

    def __add__(self, other):
        default = ComposedQuery
        factory = queryUtility(IFactory, dottedname(IComposedQuery)) or default
        return factory(filters=[self, other])
