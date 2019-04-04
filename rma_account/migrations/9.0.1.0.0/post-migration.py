# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openupgradelib import openupgrade
import logging


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
    update account_invoice_line ail set rma_line_id = null;
    """
    openupgrade.logged_query(cr, query)
    query = """
        update account_invoice_line ail
        set rma_line_id = rol.id
        from rma_order ro
        inner join rma_order_line rol on rol.rma_id = ro.id
        where rol.%s = ro.id
        and rol.%s = ail.id
    """ % (openupgrade.get_legacy_name('claim_id'),
           openupgrade.get_legacy_name('refund_line_id'))
    openupgrade.logged_query(cr, query)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    set_policies(env.cr)
    link_refunds(env.cr)
