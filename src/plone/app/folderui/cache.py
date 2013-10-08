from zope.interface import implements
from BTrees.IIBTree import IISet
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from persistent import Persistent

from interfaces import (
    IQueryFilter,
    IRecordSetCache, IFilterSetIdCache,
    IRecordInvalidationSet, ISetCacheTools,
)

from utils import sitemanager_for


def filter_cached_set(query, context=None):
    """given a query filter argument, return a cached set or None"""
    if not IQueryFilter.providedBy(query):
        raise ValueError('query does not provide IQueryFilter')
    if not query.uid:
        return None  # no uuid for query means we cannot lookup
    sm = sitemanager_for(context)
    set_cache = sm.queryUtility(IRecordSetCache)
    filter_setid_cache = sm.queryUtility(IFilterSetIdCache)
    if set_cache is not None and filter_set_id_cache is not None:
        setid = filter_setid_cache.get(query.uid, None)
        if setid is None:
            return None
        frozen = set_cache.get(setid, None)
        if frozen is not None:
            return frozen
    return None

# TODO: having troubles here with 32+bit keys. maybe switch to LOBTree etc.. variants?


class PersistentRecordSetCache(IOBTree):
    """
    Btree/mapping for record sets, where keys are hash of frozenset, and
    values are frozenset objects.
    """
    implements(IRecordSetCache)


class PersistentFilterSetIdCache(OIBTree):
    """
    Btree/mapping for filter uuid strings to result/record set integer ids.
    """
    implements(IFilterSetIdCache)


class PersistentRecordInvalidationSet(IISet):
    """
    Set of integer record ids.
    """
    implements(IRecordInvalidationSet)


class PersistentSetCacheTools(Persistent):
    """
    Component that acts as a persistent (local) utility providing
    filter uuid to set id cache, set id to set cache, and records to be
    invalidated.
    """

    implements(ISetCacheTools)

    def __init__(self):
        self.set_cache = PersistentRecordSetCache()
        self.filter_setid_cache = PersistentFilterSetIdCache()
        self.invalidated_records = PersistentRecordInvalidationSet()
