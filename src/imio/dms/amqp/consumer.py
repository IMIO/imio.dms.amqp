# encoding: utf-8

import cPickle

from five import grok
from zope.component import getUtility
from zope.component import queryUtility
from zope.globalrequest import getRequest

from Products.CMFCore.interfaces import ISiteRoot
from plone.dexterity.utils import createContentInContainer
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.namedfile.file import NamedBlobFile
from collective.dms.batchimport.utils import createDocument
from collective.dms.batchimport.utils import log
import plone.api

from collective.zamqp.consumer import Consumer
from collective.zamqp.interfaces import IMessageArrivedEvent
from collective.zamqp.interfaces import IProducer

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
    create_content('incoming-mail', 'dmsincomingmail', message)
    producer = getUtility(IProducer, 'dms.invoice.videocoding')
    producer._register()
    producer.publish(message.body)
    message.ack()


class IncomingMailConsumer(base.DMSConsumer, Consumer):
    grok.name('dms.incomingmail')
    connection_id = 'dms.connection'
    exchange = 'dms.incomingmail'
    marker = interfaces.IIncomingMail
    queuename = 'dms.incomingmail.{0}'


@grok.subscribe(interfaces.IIncomingMail, IMessageArrivedEvent)
def consume_incoming_mails(message, event):
    create_content('incoming-mail', 'dmsincomingmail', message)
    message.ack()


class Dummy(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request


def create_content(folder, document_type, message):
    obj = base.MessageAdapter(cPickle.loads(message.body))

    site = getUtility(ISiteRoot)
    folder = site.unrestrictedTraverse(folder)
    context = Dummy(folder, getRequest())
    doc = open(obj.filepath, 'r')
    obj_file = NamedBlobFile(doc.read(), filename=obj.filename)

    document = get_existing_document(folder, document_type, obj)
    if document:
        update_document(document, obj, obj_file)
    else:
        createDocument(context, folder, document_type, '', obj_file,
                       owner=obj.creator, metadata=obj.metadata)
    doc.close()


def get_existing_document(folder, document_type, obj):
    folder_path = '/'.join(folder.getPhysicalPath())
    id_normalizer = queryUtility(IIDNormalizer)
    obj_id = id_normalizer.normalize(obj.metadata.get('id'))
    result = folder.portal_catalog(portal_type=document_type,
                                   path={'query': folder_path, 'depth': 1},
                                   id=obj_id)
    if result:
        return result[0].getObject()


def update_document(document, obj, obj_file):
    plone.api.content.delete(obj=document[document.file_title])
    for key, value in obj.metadata.items():
        setattr(document, key, value)
    user = plone.api.user.get(obj.creator)
    document.changeOwnership(user)
    createContentInContainer(document, 'dmsmainfile',
                             title=obj.metadata.get('file_title'),
                             file=obj_file)
    log.info('document has been updated (id: {0})'.format(document.id))
