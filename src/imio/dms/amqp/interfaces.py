# encoding: utf-8

from zope.interface import Interface


class IInvoice(Interface):
    """Marker interface for invoices"""


class IIncomingMail(Interface):
    """Marker interface for incoming mails"""


class IOutgoingMail(Interface):
    """Marker interface for outgoing mails"""
