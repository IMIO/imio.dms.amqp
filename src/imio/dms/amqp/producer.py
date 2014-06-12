# encoding: utf-8

from five import grok

from collective.zamqp.producer import Producer

from imio.dms.amqp import base


class InvoiceProducer(base.DMSProducer, Producer):
    grok.name('dms.invoice.videocoding')
    connection_id = 'dms.connection'
    exchange = 'dms.invoice.videocoding'
    durable = True
    queuename = 'dms.invoice.videocoding.{0}'
    serializer = 'text'
