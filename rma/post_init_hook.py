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
        select rol.id, ro.%s, rol.product_id, rol.product_qty
        from rma_order_line rol
        inner join rma_order ro on ro.id = rol.%s
    """ % (openupgrade.get_legacy_name('ref'),
           openupgrade.get_legacy_name('claim_id')))
    for rml_id, origin, product_id, product_qty in env.cr.fetchall():
        if origin and product_qty and product_id:
            table = origin.split(",")[0]
            obj_id = origin.split(",")[1]
            if table == 'account.invoice':
                env.cr.execute(
                    """
                    select ail.id
                    from  account_invoice_line ail
                    inner join account_invoice ai on ai.id = ail.invoice_id
                    where ai.id = %s
                    and ail.product_id = %s
                    and ail.quantity = %s
                    limit 1
                    """ % (obj_id, product_id, product_qty))
                inv_line_id = env.cr.fetchone()
                if inv_line_id:
                    env.cr.execute(
                        """UPDATE rma_order_line SET invoice_line_id=%s
                        WHERE id=%s""" % (inv_line_id[0], rml_id),
                    )
                    origin_name = env['account.invoice'].browse(
                        [int(obj_id)]).name
                    env.cr.execute(
                        "UPDATE rma_order_line SET origin='%s'" % origin_name,
                    )


def map_crm_claim_warehouse_id(cr):
    query = """
        update rma_order_line rol
        set in_warehouse_id = ro.%s, out_warehouse_id = ro.%s
        from rma_order ro where ro.id = rol.%s
    """ % (openupgrade.get_legacy_name('warehouse_id'),
           openupgrade.get_legacy_name('warehouse_id'),
           openupgrade.get_legacy_name('claim_id'))
    openupgrade.logged_query(cr, query)


def set_policies(cr):
    query = """
        update rma_order_line rml
        set receipt_policy = 'ordered'
        from rma_order ro
        where %s is not null
    """ % (openupgrade.get_legacy_name('move_in_id'))
    openupgrade.logged_query(cr, query)
    query = """
        update rma_order_line rml
        set receipt_policy = 'no'
        from rma_order ro
        where %s is null
    """ % (openupgrade.get_legacy_name('move_in_id'))
    openupgrade.logged_query(cr, query)

    query = """
        update rma_order_line rml
        set delivery_policy = 'ordered'
        from rma_order ro
        where %s is not null
    """ % (openupgrade.get_legacy_name('move_out_id'))
    openupgrade.logged_query(cr, query)
    query = """
        update rma_order_line rml
        set delivery_policy = 'no'
        from rma_order ro
        where %s is null
    """ % (openupgrade.get_legacy_name('move_out_id'))
    openupgrade.logged_query(cr, query)


def link_moves(cr):
    query = """
        update stock_move stm
        set rma_line_id = rol.id
        from rma_order_line rol
        inner join rma_order on rol.%s = rma_order.id
        where rol.%s = stm.id
    """ % (openupgrade.get_legacy_name('claim_id'),
           openupgrade.get_legacy_name('move_out_id'))
    openupgrade.logged_query(cr, query)
    query = """
        update stock_move stm
        set rma_line_id = rol.id
        from rma_order_line rol
        inner join rma_order on rol.%s = rma_order.id
        where rol.%s = stm.id
    """ % (openupgrade.get_legacy_name('claim_id'),
           openupgrade.get_legacy_name('move_in_id'))
    openupgrade.logged_query(cr, query)


def link_refunds(cr):
    query = """
        update account_invoice_line ail
        set rma_line_id = rma_order_line.id
        from rma_order ro on rma_order_line.%s = ro.id
        where rma_order_line.refund_line_id = ail.id
    """ % (openupgrade.get_legacy_name('claim_id'))
    openupgrade.logged_query(cr, query)


def set_type(cr):
    query = """
        update rma_order
        set type = 'customer'
        where %s = 1
    """ % (openupgrade.get_legacy_name('claim_type'))
    openupgrade.logged_query(cr, query)
    query = """
        update rma_order
        set type = 'supplier'
        where %s = 2
    """ % (openupgrade.get_legacy_name('claim_type'))
    openupgrade.logged_query(cr, query)
    query = """
        update rma_order_line rml set type = ro.type
        from rma_order ro
        where ro.id = rml.rma_id
    """
    openupgrade.logged_query(cr, query)


def force_recompute(env):
    lines = env['rma.order.line'].search([])
    lines._compute_in_shipment_count()
    lines._compute_out_shipment_count()
    lines._compute_qty_to_deliver()
    lines._compute_qty_incoming()
    lines._compute_qty_received()
    lines._compute_qty_outgoing()
    lines._compute_qty_delivered()
    lines._compute_qty_supplier_rma()
    lines._compute_procurement_count()


def assign_name(cr):
    cr.execute("""
        update rma_order set name = %s
    """ % openupgrade.get_legacy_name('number'))
    cr.execute("""
        update rma_order set reference = %s
    """ % openupgrade.get_legacy_name('code'))


def assign_partner(cr):
    cr.execute("""
        update rma_order_line set partner_id = ro.partner_id
        from rma_order_line rol inner join rma_order ro on rol.rma_id = ro.id
        where ro.partner_id is not null
    """)


def assign_messages(cr):
    cr.execute("""
    update mail_message set model = 'rma.order'
    where model = 'crm.claim'
    """)


def drop_columns(cr):
    print("""Drop columns that we want the system to recompute""")
    columns = ['procurement_count',
               'in_shipment_count',
               'out_shipment_count',
               'qty_to_receive',
               'qty_incoming',
               'qty_received',
               'qty_to_deliver',
               'qty_outgoing',
               'qty_delivered',
               'qty_to_supplier_rma',
               'qty_in_supplier_rma',
               'qty_to_refund',
               'qty_refunded']
    for column in columns:
        cr.execute("""SELECT column_name
            FROM information_schema.columns
            WHERE table_name='rma_order_line' AND
            column_name='%s'""" % column)
        if cr.fetchone():
            cr.execute(
                """
                ALTER TABLE rma_order_line
                DROP COLUMN %s CASCADE;
                """ % column)
            cr.execute(
                """
                ALTER TABLE rma_order_line
                ADD COLUMN %s float;
                """ % column)
    columns = ['in_shipment_count',
               'out_shipment_count',
               'line_count',
               'supplier_line_count',
               'invoice_refund_count',
               'invoice_count']
    for column in columns:
        cr.execute("""SELECT column_name
            FROM information_schema.columns
            WHERE table_name='rma_order' AND
            column_name='%s'""" % column)
        if cr.fetchone():
            cr.execute(
                """
                ALTER TABLE rma_order
                DROP COLUMN %s CASCADE;
                """ % column)
            cr.execute(
                """
                ALTER TABLE rma_order
                ADD COLUMN %s float;
                """ % column)


def post_init_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    assign_origin(env)
    assign_partner(env.cr)
    assign_messages(env.cr)
    map_crm_claim_warehouse_id(env.cr)
    assign_name(cr)
    set_policies(env.cr)
    set_type(env.cr)
    link_moves(env.cr)
    drop_columns(env.cr)
    force_recompute(env)
