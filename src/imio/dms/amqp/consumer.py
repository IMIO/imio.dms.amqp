# encoding: utf-8

import cPickle

from five import grok
from zope.component import getUtility
from zope.interface import Interface
from zope.globalrequest import getRequest

from Products.CMFCore.interfaces import ISiteRoot
from plone.namedfile.file import NamedBlobFile
from collective.dms.batchimport.utils import createDocument

from collective.zamqp.consumer import Consumer
from collective.zamqp.interfaces import IMessageArrivedEvent


class MessageAdapter(object):

    def __init__(self, context):
        self.context = context

    def __getattr__(self, key):
        try:
            return self.__getattribute__(key)
        except AttributeError:
            return getattr(self.context, key)


class IInvoice(Interface):
    """Marker interface for invoices"""


class InvoiceConsumer(Consumer):
    grok.name('dms.invoice.AA')
    routing_key = 'AA'
    connection_id = 'dms.connection'
    exchange = 'imiodocument'
    marker = IInvoice


class Dummy(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request


@grok.subscribe(IInvoice, IMessageArrivedEvent)
def consume_invoices(message, event):
    invoice = InvoiceAdapter(cPickle.loads(message.body))

    site = getUtility(ISiteRoot)
    folder = site.unrestrictedTraverse('incoming-mail')
    context = Dummy(folder, getRequest())
    doc = open(invoice.filepath, 'r')
    invoice_file = NamedBlobFile(doc.read(), filename=invoice.filename)
    createDocument(context, folder, 'dmsincomingmail', '',
                   invoice_file, owner=invoice.creator,
                   metadata=invoice.metadata)
    doc.close()
    message.ack()


class InvoiceAdapter(MessageAdapter):

    @property
    def metadata(self):
        return {
            'id': self.context.external_id,
            'file_title': self.context.file_metadata.get('filename'),
            'external_reference_no': self.context.external_id,
            'mail_type': 'facture',
            'scan_id': self.context.external_id,
            'pages_number': self.context.file_metadata.get('pages_number'),
            'scan_date': self.context.scan_date,
            'scan_user': self.context.file_metadata.get('user'),
            'scanner': self.context.file_metadata.get('pc'),
        }
