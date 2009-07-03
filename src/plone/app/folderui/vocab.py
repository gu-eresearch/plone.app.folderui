from zope.interface import implements, alsoProvides
from zope.component import getGlobalSiteManager, queryUtility, IFactory
from zope.schema.interfaces import IVocabularyTokenized, IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm, VocabularyRegistry
from zope.schema import getFieldsInOrder
from zope.schema.fieldproperty import FieldProperty
from Products.CMFCore.utils import getToolByName
from interfaces import ITitleLookup, IFilterSpecification
from utils import dottedname


titlecase = lambda v: v.title()

alsoProvides(titlecase, ITitleLookup)


def member_fullname(value, context):
    mtool = getToolByName(context, 'portal_membership')
    info = mtool.getMemberInfo(value)
    v = info.get('fullname',None)
    if v: return v
    return value

alsoProvides(member_fullname, ITitleLookup)


class UniqueValuesFactory(object):
    
    implements(IVocabularyFactory)
    
    def __init__(self, index, titlefn=None):
        self.index = str(index)
        if titlefn and not ITitleLookup.providedBy(titlefn):
            raise ValueError('title callable must provide ITitleLookup')
        self.titlefn = titlefn #should be 
    
    def _mkterm(self, value, title=None):
        term_factory = queryUtility(IFactory, dottedname(IFilterSpecification))
        if term_factory is None:
            if title:
                return SimpleTerm(value=value, title=title)
            return SimpleTerm(t)
        t = term_factory()
        t.name = value
        if title:
            t.title = title
        t.values = (value,)
        return t
    
    def __call__(self, context):
        terms = []
        cat = getToolByName(context, 'portal_catalog')
        values = cat.uniqueValuesFor(self.index)
        for v in values:
            title = None
            if self.titlefn is not None:
                title = self.titlefn(v, context)
            terms.append(self._mkterm(v,title))
        return SimpleVocabulary(terms)


#some factories for indexes:
all_creators_vfactory = UniqueValuesFactory('Creator', titlefn=member_fullname)


gsm = getGlobalSiteManager()
gsm.registerUtility(all_creators_vfactory, IVocabularyFactory, name='creator')

