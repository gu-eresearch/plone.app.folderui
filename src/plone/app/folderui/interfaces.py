from zope.interface import Interface, Attribute
from zope.interface.common.mapping import IIterableMapping, IWriteMapping
from zope.interface.common.sequence import (ISequence,
    IUniqueMemberWriteSequence, IReadSequence,)
from zope.schema import (Bool, Choice, Datetime, List, Object, TextLine, 
    Text, Tuple, BytesLine, )
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import ITitledTokenizedTerm, IVocabularyFactory
from zope.component.interfaces import IFactory


callable_if_exists = lambda o: hasattr(o, '__call__')

mkvocab = lambda seq: SimpleVocabulary([SimpleTerm(e) for e in seq])

FACETS_ALL = 1 #used to include/exclude all facets in configuration


class IQueryFilter(Interface):
    """implementation-neutral query fragment to be applied to a single index"""
    uid = BytesLine(title=u'Unique id',
        description=\
            u"""
            String id unique to site; may be dotted name of filter plus facet
            or a (RFC 4122) UUID.
            """,
        required=False,)
    index = TextLine(title=u'Index name or identifier', required=True)
    value = Object(title=u'Search value(s)', schema=Interface, required=False)
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
    """
    Results object should be iterable mapping of results, where key is some
    record id for object, and value is a brain-like object containing metadata
    attributes.
    
    Optionally, if the component providing this interface wraps a
    lazy-evaluated seqence, values() may return that lazy sequence.
    """
    
    frozen = Attribute('Read-only frozenset of result record ids')
    setid = Attribute('Read-only integer set id property', 
        """
        A read-only property for some determinate integer id for the
        record id set based completely on the composition of the member
        set.  Should be similar in behavior to performing:
        
            hash(frozenset(self.keys())).
        
        The resulting setid for any set should be identical for the same
        set of member elements regardless of element order, and across
        threads or machines of the same architecture (a hash on 64-bit box
        need not be the same for hash on a 32-bit box, this is an accepted
        limitation).
        
        Having a determinate way to identify a set based on the member
        elements contained within the set -- the whole is based on the 
        parts -- is potentially useful for indexing set values and set
        relationships.
        """)


class IQueryRunner(Interface):
    """
    Callable query runner takes a query object, and returns an iterable
    mapping of results implementing IQueryResults.
    """
    
    def __call__(composed):
        """
        Run query specified in composed, which is an object providing either
        IQueryFilter or IComposedQuery.  Should return mapping object
        providing IQueryResults.  Optionally may cache information about
        the result for future queries.
        
        Query runner may run in a context -- for example, that of a specific
        folder path, and this may modify the eventual query making results.
        """


class IFilterSpecification(ITitledTokenizedTerm):
    """
    Search filter specification for faceted search, may be persisted as
    configuration.
    """
    token = Attribute('Token',
        '7-bit read-only str for self.name or self.value')
    
    name = TextLine(title=u'Filter name',
        required=True)  #should be unique within facet
    title = TextLine(title=u'Display title',
        required=False) #link title, otherwise uses name
    description = Text(title=u'Description of filter', required=False)
    allow_negation = Bool(title=u'Allow negation?',
        description=u'Allow NOT operator on filter.',
        default=True)
    index = TextLine(title=u'Index name or identifier', required=True)
    value = Object(title=u'Search value(s)', schema=Interface, required=False)
    query_range = Choice(title=u'Query range',
        vocabulary=mkvocab(('min','max','minmax',None)),
        default=None)
    negated = Bool(title=u'Negate query?', default=False)
    
    def __call__():
        """return transient IQueryFilter for this specification"""
    
    def count(context, facet, intersect=None):
        """
        return a count of items for this filter in a given context, and 
        a main search result 'intersect' to perform intersection with.
        """


class IFacetSpecification(IVocabularyFactory):
    """facet is grouping of search filters"""
    name = TextLine(required=True) #should be unique for all facets
    title = TextLine(required=True)
    index = TextLine(required=False,
        default=None) #if None, use name as index name
    description = Text(required=False)
    multiset = Bool(title=u'Multiset?',
        description=u'Allows multiple selections / result sets for one facet.',
        default=False, )
    multiset_operator = Choice(
        title=u'Operator',
        description=u'Operator for multiple selections (AND/OR)',
        vocabulary=mkvocab(('AND','OR')),
        default='OR')
    query_vocabulary = Bool(
        title=u'Query vocabulary?',
        description=u'Query vocabulary factory for additional filters?',
        default=False,
        )
    use_vocabulary = Bool(
        title=u'Use vocabulary?',
        description=u'Use controlled vocabulary, via filters or lookup?',
        default=True, #if False, search value is query value, not filter name
        )
    filters = List(
        value_type=Object(schema=IFilterSpecification),
        required=False)
    
    def __call__(context):
        """
        Return a vocabulary object implemening IVocabularyTokenized that 
        contains terms implementing IFilterSpecification.  Implementations
        may choose to delegate this activity to another IVocabularyFactory
        component such as a named utility if de-coupling vocabulary 
        generation from facet specification is desired.  May include items
        from static vocabulary (from self.filters), dynamic vocabulary, or
        some hybrid.
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


is_daterange = lambda v: (IDateRange.providedBy(v) or 
    IDateRangeFactory.providedBy(v))


class ILazySequence(Interface):
    """Marker for Lazy sequence such as ZCatalog LazyMap or similar"""


class IFacetedListing(Interface):
    """
    Component that controls facets and listings for an adapted folderish
    context object and some optional query.
    """
    
    result = Object(
        title=u'Query result',
        description=u'Folder listing via query result, iterable mapping.',
        schema=IQueryResults,
        readonly=True, )
    
    facets = Object(
        title=u'Facet list',
        description=u'IFacetSpecification objects for the folder context.',
        schema=IReadSequence,
        readonly=True, )
    
    counts = Object(
        title=u'Filter counts',
        description=\
            u"""
            Mapping of set counts intersected with self.result; keys should
            match IQueryFilter uid value for filter generated from
            IFilterSpecification; values should be integer counts of
            intersected hits.
            """,
        schema=IIterableMapping,
        readonly=True, )



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


class ITitleLookup(Interface):
    """
    Callable function or object that returns a title given a token/value
    and an optional context.
    """
    def __call__(token, context=None):
        """
        return unicode title for token, possibly using context for 
        placeful lookup, if needed.
        """


class IRecordInvalidationSet(IUniqueMemberWriteSequence, ISequence):
    """
    set of integer record ids that should be considered stale for
    purposes of search results; if a search result includes one of these
    documents, then filter counts for the facets intersected with that
    search should be re-generated from query, not reported from cache.
    """
    def insert(key):
        """add an integer value (key) to the set"""
    
    def remove(key):
        """remove an integer value (key) from the set"""


class IRecordSetCache(IIterableMapping):
    """
    Iterable mapping of integer keys to values of frozenset objects containing
    integer record ids of cataloged objects in a result set.  Keys should be
    deterministic based on set membership, as hash(frozenset()) is.
    """


class IFilterSetIdCache(IIterableMapping):
    """
    Iterable mapping of uuid string keys to integer set ids.  This is used
    in conjuntion with IRecordSetCache components to form the other half
    of a lookup from filters to result sets.
    """


class ISetCacheTools(Interface):
    """
    Set of tools related to caching and invalidation of result sets of record
    ids, query filter uuids to sets.
    """
    set_cache = Object(schema=IRecordSetCache)
    filter_setid_cache = Object(schema=IFilterSetIdCache)
    invalidated_records = Object(schema=IRecordInvalidationSet)


