from Products.Five import BrowserView
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from z3c.form.form import AddForm, EditForm
from z3c.form.field import Fields
from z3c.form import button
from plone.app.folderui.registry import parse_facet_settings, facet_type_vocabulary, update_facet_setting, remove_facet_setting
from zope.dottedname.resolve import resolve
from Products.statusmessages.interfaces import IStatusMessage
from zope.publisher.interfaces import IPublishTraverse
from zope.interface import implements

# TODO: make sure add works even if form fails.....
#       implement registry event listeners to clear facet settings cache
class FolderUiSettingsView(BrowserView):

    def getContent(self):
        registry = getUtility(IRegistry)
        facets = parse_facet_settings(registry)['facet'].values()
        facet_vocab = facet_type_vocabulary()
        for facet in facets:
            facet['facet_type_title'] = facet_vocab.getTermByToken(facet['interfaceName']).title
        return sorted(facets, key=lambda item: item.get('order', 1000))

    def facet_types(self):
        return facet_type_vocabulary()


class AddFacetForm(AddForm):

    def update(self):
        ifc = resolve(self.facettype)
        self.fields = Fields(ifc)
        super(AddFacetForm, self).update()

    # create and add return obj on success
    def create(self, data):
        #not much to do here
        return data

    def add(self, object):
        # check if name exists:
        prefix = "plone.app.folderui.facet.%s" % object['name']
        registry = getUtility(IRegistry)
        if not prefix in registry.records:
            ifc = resolve(self.facettype)
            registry.registerInterface(ifc, prefix=prefix)
            # FIXME: renaming not supported, and setting name is ignored in update_facet_settings.
            #        either enable renaming, or make name addable, but non editable
            registry.records[prefix + '.name'].value = object['name']
            update_facet_setting(registry, object)
            return object
        # TODO: duplicate key... raise error?
        return None

    def nextURL(self):
        return self.context.absolute_url() + "/folderui_control_panel"

    def publishTraverse(self, request, name):
        # do some paramater checks ....
        # check that name exists in facet_vocabluary ... etc...
        self.facettype = name
        return self


class EditFacetForm(EditForm):

    def update(self):
        registry = getUtility(IRegistry)
        self.facet_config = parse_facet_settings(registry)['facet'][self.facetname]
        ifc = resolve(self.facet_config['interfaceName'])
        self.fields = Fields(ifc)
        super(EditFacetForm, self).update()

    def updateActions(self):
        super(EditFacetForm, self).updateActions()
        self.actions['save'].addClass("context")
        self.actions['cancel'].addClass("standalone")

    def getContent(self):
        return self.facet_config

    def applyChanges(self, data):
        changes = super(EditFacetForm, self).applyChanges(data)
        registry = getUtility(IRegistry)
        update_facet_setting(registry, data)
        return changes

    def publishTraverse(self, request, name):
        # TODO: check parameters
        self.facetname = name
        # collect name as parameters
        return self

    @button.buttonAndHandler(u"Save", name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = self.applyChanges(data)
        if changes:
            IStatusMessage(self.request).addStatusMessage(u"Changes saved.", "info")
        else:
            IStatusMessage(self.request).addStatusMessage(u"No Changes applied.", "info")
        self.request.response.redirect(self.context.absolute_url() + "/folderui_control_panel")

    @button.buttonAndHandler(u"Cancel", name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(u"Edit cancelled.", "info")
        self.request.response.redirect(self.context.absolute_url() + "/folderui_control_panel")


class ActionFacetView(BrowserView):

    implements(IPublishTraverse)

    params = None

    def __call__(self):
        if self.params[0] not in ('up', 'down', 'remove'):
            return None  # TODO: raise exception or maybe do it already in pub traverse
        registry = getUtility(IRegistry)
        facet_config = parse_facet_settings(registry)['facet'][self.params[1]]
        getattr(self, self.params[0])(registry, facet_config)
        self.request.response.redirect(self.context.absolute_url() + "/folderui_control_panel")

    def up(self, registry, facet_config):
        facet_config['order'] -= 1
        update_facet_setting(registry, facet_config)
        IStatusMessage(self.request).addStatusMessage(u"Facet %s moved to %d." % (facet_config['title'], facet_config['order']), "info")

    def down(self, registry, facet_config):
        facet_config['order'] += 1
        update_facet_setting(registry, facet_config)
        IStatusMessage(self.request).addStatusMessage(u"Facet %s moved to %d." % (facet_config['title'], facet_config['order']), "info")

    def remove(self, registry, facet_config):
        remove_facet_setting(registry, facet_config)
        IStatusMessage(self.request).addStatusMessage(u"Facet %s removed." % (facet_config['title'],), "info")

    def publishTraverse(self, request, name):
        # this method should rais NotFound in case of troubles.. (see zope.publisher docu)
        # TODO: check parameters
        if not self.params:
            self.params = []
        self.params.append(name)
        return self
