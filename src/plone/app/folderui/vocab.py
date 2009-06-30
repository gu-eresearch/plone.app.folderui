from zope.interface import implements, alsoProvides
from zope.schema.interfaces import IVocabularyTokenized, IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm, VocabularyRegistry
from zope.schema import getFieldsInOrder
from zope.schema.fieldproperty import FieldProperty
from Products.CMFCore.utils import getToolByName
from plone.app.folderui.interfaces import ITitleLookup


titlecase = lambda v: v.title()
alsoProvides(titlecase, ITitleLookup)

class UniqueValuesFactory(object):
    
    def __init__(self, index, titlefn=None):
        self.index = str(index)
        if titlefn and not ITitleLookup.providedBy(titlefn):
            raise ValueError('title callable must provide ITitleLookup')
        self.titlefn = titlefn #should be 
    
    def __call__(self, context):
        terms = []
        cat = getToolByName(context, 'portal_catalog')
        values = cat.uniqueValuesFor(self.index)
        for v in values:
            title = None
            if self.titlefn is not None:
                title = self.titlefn(t)
            if title:
                t = SimpleTerm(value=t, title=title)
            else:
                t = SimpleTerm(t)
            terms.append(t)
        return SimpleVocabulary(t)


#some factories for indexes:
all_owners_vfactory = UniqueValuesFactory('owner')
#TODO TODO TODO: owner name lookup from member properties as ITitleLookup fn
