# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openupgradelib import openupgrade
import logging

logger = logging.getLogger(__name__)

def assign_operating_unit(cr):
    query = """
        update rma_order ro
        set operating_unit_id = %s
    """ % (openupgrade.get_legacy_name('operating_unit_id'))
    openupgrade.logged_query(cr, query)
    query = """
        update rma_order_line rol
        set operating_unit_id = ro.operating_unit_id
        from rma_order ro where ro.id = rol.rma_id
    """
    openupgrade.logged_query(cr, query)


def post_init_hook(cr, registry):
    assign_operating_unit(cr)
