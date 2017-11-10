# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp.tests import common
from openerp import fields


class TestRma(common.TransactionCase):

    """ Test the routes and the quantities """

    def setUp(self):
        super(TestRma, self).setUp()

        self.rma_make_picking = self.env['rma_make_picking.wizard']
        self.make_supplier_rma = self.env["rma.order.line.make.supplier.rma"]
        self.rma_add_stock_move = self.env['rma_add_stock_move']
        self.stockpicking = self.env['stock.picking']
        self.rma = self.env['rma.order']
        self.rma_line = self.env['rma.order.line']
        self.rma_op = self.env['rma.operation']
        self.rma_cust_replace_op_id = self.env.ref(
            'rma.rma_operation_customer_replace')
        self.rma_sup_replace_op_id = self.env.ref(
            'rma.rma_operation_supplier_replace')
        self.product_id = self.env.ref('product.product_product_4')
        self.product_id.product_tmpl_id.categ_id.\
            property_stock_account_input_categ_id =\
            self.env.ref('account.data_account_type_receivable').id
        self.product_id.product_tmpl_id.categ_id.\
            property_stock_account_output_categ_id =\
            self.env.ref('account.data_account_type_expenses').id
        self.product_1 = self.env.ref('product.product_product_25')
        self.product_2 = self.env.ref('product.product_product_30')
        self.product_3 = self.env.ref('product.product_product_33')
        self.uom_unit = self.env.ref('product.product_uom_unit')
        # assign an operation
        self.product_1.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        self.product_2.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        self.product_3.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        self.partner_id = self.env.ref('base.res_partner_12')
        self.stock_location = self.env.ref('stock.stock_location_stock')
        self.stock_rma_location = self.env.ref('rma.location_rma')
        self.customer_location = self.env.ref(
            'stock.stock_location_customers')
        self.supplier_location = self.env.ref(
            'stock.stock_location_suppliers')
        self.product_uom_id = self.env.ref('product.product_uom_unit')
        products2move = [(self.product_1, 3), (self.product_2, 5),
                         (self.product_3, 2)]
        self.rma_customer_id = self._create_rma_from_move(
            products2move, 'customer', self.env.ref('base.res_partner_2'),
            dropship=False)

    def _create_picking(self, partner):
        return self.stockpicking.create({
            'partner_id': partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_in').id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.supplier_location.id
            })

    def _create_rma_from_move(self, products2move, type, partner, dropship,
                              supplier_address_id=None):
        picking_in = self._create_picking(partner)

        moves = []
        if type == 'customer':
            for item in products2move:
                move_values = self._prepare_move(
                    item[0], item[1], self.stock_location,
                    self.customer_location, picking_in)
                moves.append(self.env['stock.move'].create(move_values))
        else:
            for item in products2move:
                move_values = self._prepare_move(
                    item[0], item[1], self.supplier_location,
                    self.stock_rma_location, picking_in)
                moves.append(self.env['stock.move'].create(move_values))
        # Create the RMA from the stock_move
        rma_id = self.rma.create(
            {
                'reference': '0001',
                'type': type,
                'partner_id': partner.id,
                'company_id': self.env.ref('base.main_company').id
            })
        rma_id._compute_invoice_refund_count()
        rma_id._compute_invoice_count()

        data = {'add_invoice_id': self._create_invoice().id}
        new_line = self.rma.new(data)
        new_line.on_change_invoice()

        rma_id.action_view_invoice_refund()
        rma_id.action_view_invoice()

        for move in moves:
            if type == 'customer':
                wizard = self.rma_add_stock_move.with_context(
                    {'stock_move_id': move.id, 'customer': True,
                     'active_ids': rma_id.id,
                     'active_model': 'rma.order',
                     }
                ).create({})
                data = wizard._prepare_rma_line_from_stock_move(move)
            else:
                wizard = self.rma_add_stock_move.with_context(
                    {'stock_move_id': move.id, 'supplier': True,
                     'active_ids': rma_id.id,
                     'active_model': 'rma.order',
                     }
                ).create({})
                data = wizard._prepare_rma_line_from_stock_move(move)
            if dropship:
                data.update(customer_to_supplier=dropship,
                            supplier_address_id=supplier_address_id.id)
            self.line = self.rma_line.create(data)
            # approve the RMA Line
            self.rma_line.action_rma_to_approve()

            self.line.action_rma_approve()
            self.line.action_view_invoice()
            self.line.action_view_refunds()

        # approve the RMA
#        rma_id.action_rma_to_approve()
#        rma_id.action_rma_approve()
        return rma_id

    def _prepare_move(self, product, qty, src, dest, picking_in):
        res = {
            'partner_id': self.partner_id.id,
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': self.product_uom_id.id or product.uom_id.id,
            'product_uom_qty': qty,
            'origin': 'Test RMA',
            'location_id': src.id,
            'location_dest_id': dest.id,
            'picking_id': picking_in.id
        }
        return res

    def test_rma_refund(self):

        self.rma_refund_item = self.env['rma.refund.item']
        self.rma_refund = self.env['rma.refund']

        self.product_id.income =\
            self.env.ref('account.data_account_type_receivable').id
        self.product_id.expense =\
            self.env.ref('account.data_account_type_expenses').id

        for line in self.rma_customer_id.rma_line_ids:
            line.refund_policy = 'ordered'

        refund = self.rma_refund.with_context({
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'active_id': 1
        }).create({'description': 'Test Reason',
                   'date_invoice': fields.datetime.now()
                   })
        self.rma_refund_item.create({
            'line_id': self.rma_customer_id.rma_line_ids[0].id,
            'rma_id': self.rma_customer_id.id,
            'product_id': self.product_id.id,
            'name': 'Test RMA Refund',
            'product_qty': self.rma_customer_id.rma_line_ids[0].product_qty,
            'wiz_id': refund.id
        })
        refund.invoice_refund()

    def test_rma_add_invoice_wizard(self):

        wizard = self.env['rma_add_invoice'].with_context({
            'active_ids': self.rma_customer_id.ids,
            'active_model': 'rma.order',
            'active_id': self.rma_customer_id.id
        }).create({'partner_id': self.partner_id.id,
                   'rma_id': self.rma_customer_id.id,
                   'invoice_line_ids':
                   [(6, 0, [self._create_invoice().invoice_line_ids.id])],
                   })
        wizard.add_lines()

    def _create_invoice(self):
        self.Account = self.env['account.account']
        self.AccountInvoice = self.env['account.invoice']
        self.AccountInvoiceLine = self.env['account.invoice.line']

        self.account_receivable =\
            self.env.ref('account.data_account_type_receivable')
        self.account_expenses =\
            self.env.ref('account.data_account_type_expenses')
        invoice_account = self.Account.\
            search([('user_type_id', '=', self.account_receivable.id)], limit=1
                   ).id
        invoice_line_account = self.Account.\
            search([('user_type_id', '=', self.account_expenses.id)], limit=1
                   ).id

        invoice = self.AccountInvoice.create({
            'partner_id': self.partner_id.id,
            'account_id': invoice_account,
            'type': 'in_invoice',
        })

        invoice_line = self.AccountInvoiceLine.create({
            'product_id': self.product_1.id,
            'quantity': 1.0,
            'price_unit': 100.0,
            'invoice_id': invoice.id,
            'uom_id': 1,
            'name': 'product that cost 100',
            'account_id': invoice_line_account,
        })
        invoice._compute_rma_count()
        invoice_line._compute_rma_count()
        invoice.action_view_rma_customer()
        invoice.action_view_rma_supplier()
        return invoice

    def test_rma_make_picking(self):

        wizard = self.rma_make_picking.with_context({
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
            'active_id': 1
        }).create({})

        wizard.action_create_picking()
        data = {'purchase_order_line_id':
                self._create_purchase_order().order_line.id}
        new_line = self.rma_line.new(data)
        new_line._onchange_purchase_order_line_id()

        self.rma_customer_id._compute_po_count()
        self.rma_customer_id._compute_origin_po_count()

        self.rma_customer_id.action_view_purchase_order()
        self.rma_customer_id.action_view_origin_purchase_order()

        self.rma_customer_id.rma_line_ids[0]._compute_purchase_count()
        self.rma_customer_id.rma_line_ids[0]._compute_purchase_order_lines()
        self.rma_customer_id.rma_line_ids[0].action_view_purchase_order()
        self.rma_customer_id.rma_line_ids[0]._get_rma_purchased_qty()

    def test_rma_add_purchase_wizard(self):
        wizard = self.env['rma_add_purchase'].with_context({
            'active_ids': self.rma_customer_id.ids,
            'active_model': 'rma.order',
            'active_id': self.rma_customer_id.id
        }).create({'partner_id': self.partner_id.id,
                   'rma_id': self.rma_customer_id.id,
                   'purchase_id': self._create_purchase_order().id,
                   'purchase_line_ids':
                   [(6, 0, [self._create_purchase_order().order_line.id])],
                   })
        wizard.default_get([str(self._create_purchase_order().id),
                            str(self._create_purchase_order().order_line.id),
                            str(self.partner_id.id)])
        wizard.add_lines()

    def _create_purchase_order(self):
        purchase_order_id = self.env["purchase.order"].create({
            "partner_id": self.partner_id.id,
            "order_line": [
                (0, 0, {
                    "product_id": self.product_id.id,
                    "name": self.product_id.name,
                    "product_qty": 5,
                    "price_unit": 100,
                    "product_uom": self.product_id.uom_id.id,
                    "date_planned": fields.datetime.now(),
                }),
            ],
        })
        self.env["purchase.order.line"].\
            name_search(name=self.product_id.name, operator='ilike',
                        args=[('id', 'in', purchase_order_id.order_line.ids)])
        self.env["purchase.order.line"].\
            _name_search(name=self.product_id.name, operator='ilike',
                         args=[('id', 'in', purchase_order_id.order_line.ids)])
        return purchase_order_id

    def test_customer_rma(self):
        wizard = self.rma_make_picking.with_context({
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
            'active_id': 1
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = [('group_id', 'in', list(group_ids))]
        picking = self.stockpicking.search(domain)
        self.assertEquals(len(picking), 1,
                          "Incorrect number of pickings created")
        moves = picking.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_customer_id.rma_line_ids:
            # common qtys for all products
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty received")
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            # product specific
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 3,
                                  "Wrong qty incoming")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 5,
                                  "Wrong qty incoming")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 2,
                                  "Wrong qty incoming")
        picking.action_assign()
        picking.do_transfer()
        for line in self.rma_customer_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to_receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_received, 3,
                                  "Wrong qty received")
                self.assertEquals(line.qty_to_deliver, 3,
                                  "Wrong qty to_deliver")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_received, 5,
                                  "Wrong qty received")
                self.assertEquals(line.qty_to_deliver, 5,
                                  "Wrong qty to_deliver")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_received, 2,
                                  "Wrong qty received")
                self.assertEquals(line.qty_to_deliver, 2,
                                  "Wrong qty to_deliver")

        wizard = self.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'outgoing',
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = [('group_id', 'in', list(group_ids))]
        pickings = self.stockpicking.search(domain)
        self.assertEquals(len(pickings), 2,
                          "Incorrect number of pickings created")
        picking_out = pickings[1]
        moves = picking_out.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_customer_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_deliver, 3,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 3,
                                  "Wrong qty outgoing")
                self.assertEquals(line.qty_received, 3,
                                  "Wrong qty received")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_received, 5,
                                  "Wrong qty received")
                self.assertEquals(line.qty_to_deliver, 5,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 5,
                                  "Wrong qty outgoing")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_received, 2,
                                  "Wrong qty received")
                self.assertEquals(line.qty_to_deliver, 2,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 2,
                                  "Wrong qty outgoing")
        picking_out.action_assign()
        picking_out.do_transfer()
        for line in self.rma_customer_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_received, 3,
                                  "Wrong qty received")
                self.assertEquals(line.qty_delivered, 3,
                                  "Wrong qty delivered")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_received, 5,
                                  "Wrong qty received")
                self.assertEquals(line.qty_delivered, 5,
                                  "Wrong qty delivered")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_received, 2,
                                  "Wrong qty received")
                self.assertEquals(line.qty_delivered, 2,
                                  "Wrong qty delivered")
            self.line.action_rma_done()
            self.assertEquals(self.line.state, 'done',
                              "Wrong State")
