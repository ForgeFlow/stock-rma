# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openupgradelib import openupgrade
from openerp.api import Environment
from openerp import SUPERUSER_ID


_table_renames = [
    ('crm_claim', 'rma_order'),
    ('claim_line', 'rma_order_line'),
]

column_renames = {
    'crm_claim': [('description', 'comment'),
                  ('date', 'date_rma'),
                  ],
    'claim_line': [
        ('state', 'status'),
        ('product_returned_quantity', 'product_qty'),
        ('status', 'state'),
        ('claim_id', 'rma_id'),
        ('unit_sale_price', 'price_unit'),
    ]}

column_copies = {
    'claim_line': [
        ('move_in_id', None, None),
        ('move_out_id', None, None),
        ('refund_line_id', None, None),
        ('invoice_line_id', None, None),
        ('state', None, None),
        ('claim_id', None, None),
        ('claim_descr', None, None),
    ],
    'crm_claim': [('warehouse_id', None, None),
                  ('name', None, None),
                  ('claim_type', None, None),
                  ('number', None, None),
                  ('state', None, None),
                  ('code', None, None),
                  ('ref', None, None),
                  ('invoice_id', None, None),
                  ],
    'account_invoice': [('claim_id', None, None)]
}


def assign_status(cr):
    state_list = [('approved', 'pending'),
                  ('approved', 'open'),
                  ('done', 'settled'),
                  ('done', 'cancel'),
                  ]
    for states in state_list:
        query = """UPDATE rma_order set state = '%s'
                   where state = '%s'
                   """ % (states[0], states[1])
        cr.execute(query)
    for states in state_list:
        query = """UPDATE rma_order_line set state = '%s'
                   where state = '%s'
                   """ % (states[0], states[1])
        cr.execute(query)


def set_default_values(cr):
    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='rma_order_line' AND
    column_name='in_warehouse_id'""")
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE rma_order_line
            ADD COLUMN in_warehouse_id
            integer;
            """)
    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='rma_order_line' AND
    column_name='out_warehouse_id'""")
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE rma_order_line
            ADD COLUMN out_warehouse_id
            integer;
            """)
    cr.execute("""SELECT column_name
    FROM information_schema.columns
    WHERE table_name='rma_order_line' AND
    column_name='delivery_address_id'""")
    if not cr.fetchone():
        cr.execute(
            """
            ALTER TABLE rma_order_line
            ADD COLUMN delivery_address_id
            integer;
            """)
    cr.execute("""
        update rma_order_line set in_warehouse_id = 1;
        update rma_order_line set out_warehouse_id = 1;
        update rma_order_line set delivery_address_id = 1;
    """)


def drop_indexes(cr):
    cr.execute("""
     SELECT indexname FROM pg_indexes WHERE tablename like '%claim%'
    """)
    for index in cr.fetchall():
        cr.execute("""
        drop index %s
        """ % index)


def pre_init_hook(cr):
    env = Environment(cr, SUPERUSER_ID, {})
    openupgrade.copy_columns(env.cr, column_copies)
    openupgrade.rename_columns(env.cr, column_renames)
    openupgrade.rename_tables(env.cr, _table_renames)
    assign_status(env.cr)
    set_default_values(env.cr)
