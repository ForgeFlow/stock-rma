# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openupgradelib import openupgrade
import logging

logger = logging.getLogger(__name__)


def assign_analytic_account(cr):
    query = """
        update rma_order_line rol
        set analytic_account_id = %s
    """ % (openupgrade.get_legacy_name('analytic_account_id'))
    openupgrade.logged_query(cr, query)


def post_init_hook(cr, registry):
    assign_analytic_account(cr)
