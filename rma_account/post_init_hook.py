# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openupgradelib import openupgrade
import logging
from openerp.api import Environment
from openerp import SUPERUSER_ID


logger = logging.getLogger(__name__)


def set_policies(cr):
    query = """
        update rma_order_line rml
        set refund_policy = 'ordered'
        from rma_order ro
        where refund_line_id is not null
        and rml.%s = ro.id
    """ % (openupgrade.get_legacy_name('claim_id'))
    openupgrade.logged_query(cr, query)

    query = """
        update rma_order_line rml
        set refund_policy = 'no'
        from rma_order ro
        where refund_line_id is null
        and rml.%s = ro.id
    """ % (openupgrade.get_legacy_name('claim_id'))
    openupgrade.logged_query(cr, query)


def link_refunds(cr):
    query = """
        update account_invoice_line
        set rma_line_id = rol.id
        from rma_order_line rol
        inner join rma_order on rol.%s = rma_order.id
        inner join account_invoice_line ail on rol.%s = ail.id
    """ % (openupgrade.get_legacy_name('claim_id'),
           openupgrade.get_legacy_name('refund_line_id'))
    openupgrade.logged_query(cr, query)


def migrate(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    set_policies(cr)
    link_refunds(cr)
