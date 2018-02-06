# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openupgradelib import openupgrade
import logging
from openerp.api import Environment
from openerp import SUPERUSER_ID


logger = logging.getLogger(__name__)


def assign_origin(env):
    env.cr.execute("""
        select id, origin, product_id, product_qty from rma_order_line
    """)
    for rml_id, origin, product_id, product_qty in env.cr.fetchall():
        if origin and product_qty and product_id:
            try:
                table = origin.split(",")[0]
                obj_id = origin.split(",")[1]
            except:
                # it contains just the table
                continue
            if table == 'purchase.order':
                env.cr.execute(
                    """
                    select ail.id,
                    from  purchase_order_line pol
                    inner join purchase_order po on po.id = pol.order_id
                    where po.id = %s
                    and pol.product_id = %s
                    and pol.product_qty = %s
                    limit 1
                    """ % (obj_id, product_id, product_qty))
                po_line_id = env.cr.fetchall()
                env.cr.execute(
                    "UPDATE rma_order_line SET purchase_line_id=%s"
                    "WHERE id=%s" % (po_line_id, rml_id),
                )
                origin_name = env['purchase.order'].browse(
                    [int(obj_id)]).name
                env.cr.execute(
                    "UPDATE rma_order_line SET origin='%s'" % origin_name,
                )


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    assign_origin(env)
