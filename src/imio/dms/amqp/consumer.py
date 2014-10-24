# encoding: utf-8

from requests.auth import HTTPBasicAuth
import cPickle
import hashlib
import requests

from five import grok
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest

from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.namedfile.file import NamedBlobFile
from collective.dms.batchimport.utils import createDocument
from collective.dms.batchimport.utils import log
import plone.api

from collective.zamqp.consumer import Consumer
from collective.zamqp.interfaces import IMessageArrivedEvent
# from collective.zamqp.interfaces import IProducer

from imio.dms.amqp import base
from imio.dms.amqp import interfaces


class InvoiceConsumer(base.DMSConsumer, Consumer):
    grok.name('dms.invoice')
    connection_id = 'dms.connection'
    exchange = 'dms.invoice'
    marker = interfaces.IInvoice
    queuename = 'dms.invoice.{0}'


@grok.subscribe(interfaces.IInvoice, IMessageArrivedEvent)
def consume_invoices(message, event):
    doc = Document('incoming-mail', 'dmsincomingmail', message)
    doc.create_or_update()
    # producer = getUtility(IProducer, 'dms.invoice.videocoding')
    # producer._register()
    # producer.publish(message.body)
    message.ack()


class IncomingMailConsumer(base.DMSConsumer, Consumer):
    grok.name('dms.incomingmail')
    connection_id = 'dms.connection'
    exchange = 'dms.incomingmail'
    marker = interfaces.IIncomingMail
    queuename = 'dms.incomingmail.{0}'


@grok.subscribe(interfaces.IIncomingMail, IMessageArrivedEvent)
def consume_incoming_mails(message, event):
    doc = Document('incoming-mail', 'dmsincomingmail', message)
    doc.create_or_update()
    message.ack()


class Dummy(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request


class Document(object):

    def __init__(self, folder, document_type, message):
        self.folder = self.site.unrestrictedTraverse(folder)
        self.document_type = document_type
        self.obj = base.MessageAdapter(cPickle.loads(message.body))
        self.context = Dummy(self.folder, getRequest())

    @property
    def site(self):
        return getSite()

    @property
    def existing_document(self):
        folder_path = '/'.join(self.folder.getPhysicalPath())
        id_normalizer = queryUtility(IIDNormalizer)
        obj_id = id_normalizer.normalize(self.obj.metadata.get('id'))
        result = self.folder.portal_catalog(
            portal_type=self.document_type,
            path={'query': folder_path, 'depth': 1},
            id=obj_id,
        )
        if result:
            return result[0].getObject()

    @property
    def file_content(self):
        url = '%s/file/%s/%s' % (base.get_config('ws_url'),
                                 self.obj.client_id,
                                 self.obj.external_id)
        r = requests.get(url, auth=self.http_auth)
        if r.status_code != 200:
            raise ValueError('HTTP error : %s' % r.status_code)
        if hashlib.md5(r.content).hexdigest() != self.obj.file_md5:
            raise ValueError("MD5 doesn't match")
        return r.content

    @property
    def http_auth(self):
        return HTTPBasicAuth(base.get_config('ws_login'),
                             base.get_config('ws_password'))

    def create_or_update(self):
        obj_file = NamedBlobFile(self.file_content, filename=self.obj.filename)
        document = self.existing_document
        if document:
            self.update(document, obj_file)
        else:
            self.create(obj_file)

    def update(self, document, obj_file):
        files = document.listFolderContents(contentFilter={'portal_type': 'dmsmainfile', 'title': document.file_title})
        if files:
            plone.api.content.delete(obj=files[-1])
        # dont modify id !
        del self.obj.metadata['id']
        for key, value in self.obj.metadata.items():
            setattr(document, key, value)
        createContentInContainer(
            document,
            'dmsmainfile',
            title=self.obj.metadata.get('file_title'),
            file=obj_file,
        )
        log.info('document has been updated (id: {0})'.format(document.id))

    def create(self, obj_file):
        createDocument(
            self.context,
            self.folder,
            self.document_type,
            '',
            obj_file,
            owner=self.obj.creator,
            metadata=self.obj.metadata)
