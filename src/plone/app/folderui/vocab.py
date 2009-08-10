from zope.interface import implements, alsoProvides
from zope.component import ( getGlobalSiteManager, queryUtility, IFactory, 
    ComponentLookupError, )
from zope.schema.interfaces import IVocabularyTokenized, IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm, VocabularyRegistry
from zope.schema import getFieldsInOrder
from zope.schema.fieldproperty import FieldProperty
from Products.CMFCore.utils import getToolByName
from interfaces import ITitleLookup, IFilterSpecification
from utils import dottedname


titlecase = lambda v,context: v.title()
capitalize = lambda v,context: v.capitalize()

alsoProvides(titlecase, ITitleLookup)
alsoProvides(capitalize, ITitleLookup)


def member_fullname(value, context):
    mtool = getToolByName(context, 'portal_membership')
    info = mtool.getMemberInfo(value)
    v = info.get('fullname',None)
    if v: return unicode(v)
    return unicode(value)

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
            raise ComponentLookupError('cannot find factory for filter term')
        t = term_factory()
        t.name = unicode(value)
        if title:
            if isinstance(title, str):
                title = title.decode('utf-8')
            t.title = title
        t.value = value
        t.index = unicode(self.index)
        return t
    
    def __call__(self, context):
        terms = []
        cat = getToolByName(context, 'portal_catalog')
        values = cat.uniqueValuesFor(self.index)
        for v in values:
            title = v
            if self.titlefn is not None:
                title = unicode(self.titlefn(v, context))
            terms.append(self._mkterm(v,title))
        return SimpleVocabulary(terms)


#some factories for indexes (register these in ZCML):
all_creators_vfactory = UniqueValuesFactory('Creator', titlefn=member_fullname)
all_categories_vfactory = UniqueValuesFactory('Subject', titlefn=capitalize)
all_types_vfactory = UniqueValuesFactory('Type')

