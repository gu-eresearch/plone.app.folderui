from zope.interface import Interface, Attribute
from zope.interface.common.mapping import IIterableMapping, IWriteMapping
from zope.schema import (Bool, Choice, Datetime, List, Object, TextLine, 
    Text, Tuple, )
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.component.interfaces import IFactory


callable_if_exists = lambda o: hasattr(o, '__call__')

mkvocab = lambda seq: SimpleVocabulary([SimpleTerm(e) for e in seq])

FACETS_ALL = 1 #used to include/exclude all facets in configuration


class IQueryFilter(Interface):
    """implementation-neutral query fragment to be applied to a single index"""
    index = TextLine(title=u'Index name or identifier', required=True)
    terms = Tuple(value_type=Object(schema=Interface), default=())
    query_range = Choice(vocabulary=mkvocab(('min','max','minmax',None)),
        default=None,
        required=False, )
    conjunction = Choice(title=u'Intraindex conjunction operator',
        description=u'Operator for (all of) multiple queries to same index.',
        vocabulary=mkvocab(('AND','OR')),
        default='OR',)
    negated = Bool(title=u'Negated?', default=False)
    
    def __add__(other):
        """
        add another IQueryFilter or an object implementing IComposedQuery
        to this, returning a combined query implementing IComposedQuery.
        """


class IComposedQuery(Interface):
    """
    Search index implementation-neutral composite search query
    Adapters may be provided to adapt IComposedQuery and contained IQueryFilter
    objects to construct a system-dependent query/queries to execute to yield
    results (adapt IComposedQuery, call returns IQueryResults).
    """
    filters = List(title=u'Query',
        value_type=Object(schema=IQueryFilter),
        )
    interindex_operator = Choice(vocabulary=mkvocab(('AND','OR')), default='AND')
    
    def __add__(other):
        """
        add an object implementing IQueryFilter or IComposedQuery
        to this, returning a combined query implementing IComposedQuery.
        """


class IQueryResults(IIterableMapping):
    """Results object should be iterable mapping of results"""


class IQueryRunner(Interface):
    """
    Runs a query implementing IComposedQuery, for a particular implementation,
    on call.  May be an interface for adapters that adapt IComposedQuery, 
    implement IQueryRunner, and return IQueryResults on __call__().
    """
    
    def __call__():
        """
        run query configured for runner (likely through adaptation);
        return IQueryResults object
        """


class IFilterSpecification(Interface):
    """
    Search filter specification for faceted search, may be persisted as
    configuration
    """
    name = TextLine(required=True)  #should be unique within facet
    title = TextLine(required=False) #link title, otherwise uses name
    description = Text(required=False)
    allow_negation = Bool(title=u'Allow negation?',
        description=u'Allow NOT operator on filter.',
        default=True)
    index = TextLine(title=u'Index name or identifier', required=True)
    terms = Tuple(value_type=Object(schema=Interface), default=())
    query_range = Choice(vocabulary=mkvocab(('min','max','minmax')), default='minmax')
    negated = Bool(title=u'Negate query?', default=False)
    
    def __call__():
        """return transient IQueryFilter for this specification"""


class IFacetSpecification(Interface):
    """facet is grouping of search filters"""
    name = TextLine(required=True) #should be unique for all facets
    title = TextLine(required=True)
    description = Text(required=False)
    multiset = Bool(title=u'Multiset?',
        description=u'Allows multiple selections / result sets for one facet.',
        default=False, )
    multiset_operator = Choice(
        title=u'Operator',
        description=u'Operator for multiple selections (AND/OR)',
        vocabulary=mkvocab(('AND','OR')),
        default='OR')
    filters = List(
        value_type=Object(schema=IFilterSpecification),
        required=False)
    
    def __call__(filters=()):
        """
        Given a tuple of names of filters, construct and return an
        IComposedQuery object.  If an individual filter is to be negated
        as part of the query, the filter name should be ('NOT %s' % name)
        """


## date range interfaces:
class IDateRange(Interface):
    start = Datetime(required=False, default=None)
    end = Datetime(required=False, default=None)


class IDateRangeFactory(IFactory):
    """
    A specification object that maps start and end functions and is callable
    as a factory for a specific date range, returning an IDateRange object 
    tied to a specific reference date (argument) on call.
    """
    start_function = Object(schema=Interface,
        constraint=callable_if_exists,
        required=False)
    end_function = Object(schema=Interface,
        constraint=callable_if_exists,
        required=False)
    
    def __call__(dt):
        """
        for datetime dt, return date range object implementing
        IDateRange with start and end values determined by 
        start_function, end_function called with dt value as a single
        argument.
        """


class ILazySequence(Interface):
    """Marker for Lazy sequence such as ZCatalog LazyMap or similar"""


class IFacetSettings(IIterableMapping, IWriteMapping):
    """
    Registry of facets by name, stores facet names to IFacetSpecification
    objects
    """


class IFacetRules(Interface):
    """
    Set of rules by some predicate/rule.
    """
    
    whitelist = Attribute('Read-only whitelist mapping property')
    blacklist = Attribute('Read-only blacklist mapping property')
    
    def include(predicate, names=()):
        """Adds names to include whitelist for predicate"""
    
    def exclude(predicate, names=()):
        """Adds names to exclude blacklist for predicate"""
    
    def reset(predicate):
        """
        Resets and removes whitelist and blacklist configuration for 
        a predicate
        """
    
    def __call__(value):
        """
        Return a list of names given a value to be evaluated against
        known predicates.
        """


class IFacetPathRules(IFacetRules):
    """
    Set of rules for path, where path is either slash-separated-string or
    tuple of names relative to the site root.  Paths should be normalized
    on include(), exclude(), reset(), and call.
    
    This provides a registry of paths for facets, and it keeps both a
    blacklist and whitelist (independent of each other, but both consulted
    on __call__()).
    
    To disable facets altogether for a path, import FACETS_ALL and pass this
    or an integer value of 1 for names to exclude() instead of a specific
    tuple.
    
    To enable facets for a path (and all contained folder not otherwise
    explicitly excluded), pass an empty tuple of names to include().  This 
    enables facets, but does not include any names, which means that a folder
    should 'acquire' included names from parent folders by consulting the 
    whitelist.
    
    __call__(path) intersects whitelist and blacklists for folder and parent
    paths left-to-right through the hierarchy, with more specific path
    predicates overriding less-specific ones.  In case of a conflict
    between a whitelist and blacklist at the same path level, the
    blacklist wins.
    """


class IFacetRoleRules(IFacetRules):
    """
    Set of rules for user role; this should allow for a role named "any"
    which is a wildcard.  Predicate is a tuple of role names mapped to 
    any set of names for inclusion/exclusion.
    
    Example use-cases:
    
    When to include: you want a facet to only appear for manager role.
    
    When to exclude: you have a specific role that should never see a facet.
    """


