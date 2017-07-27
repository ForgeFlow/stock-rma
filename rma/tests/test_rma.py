# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp.tests import common


class TestRma(common.TransactionCase):

    """ Test the routes and the quantities """

    def setUp(self):
        super(TestRma, self).setUp()

        self.rma_make_picking = self.env['rma_make_picking.wizard']
        self.rma_add_invoice = self.env['rma_add_invoice']
        self.stockpicking = self.env['stock.picking']
        self.rma = self.env['rma.order']
        self.rma_line = self.env['rma.order.line']
        self.rma_op = self.env['rma.operation']
        self.rma_op_id = self.env.ref('rma.rma_operation_customer_replace')
        self.product_id = self.env.ref('product.product_product_4')
        self.product_1 = self.env.ref('product.product_product_25')
        self.product_2 = self.env.ref('product.product_product_30')
        self.product_3 = self.env.ref('product.product_product_33')
        self.uom_unit = self.env.ref('product.product_uom_unit')
        # assign an operation
        self.product_1.write({'rma_operation_id': self.rma_op_id.id})
        self.product_2.write({'rma_operation_id': self.rma_op_id.id})
        self.product_3.write({'rma_operation_id': self.rma_op_id.id})
        self.partner_id = self.env.ref('base.res_partner_12')

        self.customer_location_id = self.env.ref(
            'stock.stock_location_customers'
        )
        uom_unit = self.env.ref('product.product_uom_unit')
        sale_values = self._prepare_sale()
        self.sale_order = self.env['sale.order'].create(sale_values)
        invoice_id = self.sale_order.action_invoice_create()[0]
        self.invoice = self.env['account.invoice'].browse(invoice_id)
        # Create the RMA from the invoice
        self.rma_id = self.rma.create(
            {
                'reference': '0001',
                'type': 'customer',
                'partner_id': self.env.ref('base.res_partner_2').id
            })

        for line in self.invoice.invoice_line_ids:
            data = self.rma_add_invoice.with_context(
                {'invoice_id': self.invoice.id}
            )._prepare_rma_line_from_inv_line(line)
            data.update(rma_id=self.rma_id.id)
            self.rma_line.create(data)
        #approve the RMA
        self.rma_id.action_rma_to_approve()
        self.rma_id.action_rma_approve()

    def _prepare_sale(self):
        values = {
            'state': 'done',
            'partner_id': self.env.ref('base.res_partner_2').id,
            'pricelist_id': self.env.ref('product.list0').id,
            'warehouse_id': self.env.ref('stock.warehouse0').id,
            'partner_invoice_id': self.env.ref('base.res_partner_2').id,
            'partner_shipping_id': self.env.ref('base.res_partner_2').id,
            'picking_policy': 'direct',
            'order_line': [
                (0, False, {
                    'name': product.name,
                    'product_id': product.id,
                    'product_uom_qty': qty,
                    'qty_delivered': qty,
                    'product_uom': self.uom_unit.id,
                    'price_unit': product.list_price

                }) for product, qty in [
                    (self.product_1, 3),
                    (self.product_2, 5),
                    (self.product_3, 2),
                ]
            ]
        }
        return values

    def test_00_receive_items(self):
        wizard = self.rma_make_picking.with_context({
            'active_ids': self.rma_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
            'active_id': 1
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = "[('group_id','in',[" + ','.join(
            map(str, list(group_ids))) + "])]"
        picking = self.stockpicking.search(domain)
        self.assertEquals(len(picking), 1,
                          "Incorrect number of pickings created")
        moves = picking.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_id.rma_line_ids:
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty received")
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            self.assertEquals(line.qty_to_refund, 0,
                              "Wrong qty to refund")
            self.assertEquals(line.qty_to_refunded, 0,
                              "Wrong qty refunded")
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
        pickings.action_assign()
        pickings.do_transfer()
        for line in self.rma_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to_receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            self.assertEquals(line.qty_to_refund, 0,
                              "Wrong qty to refund")
            self.assertEquals(line.qty_to_refunded, 0,
                              "Wrong qty refunded")
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
            'active_ids': self.rma_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'outgoing',
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = "[('group_id','in',[" + ','.join(
            map(str, list(group_ids))) + "])]"
        picking = self.stockpicking.search(domain)
        self.assertEquals(len(picking), 1,
                          "Incorrect number of pickings created")
        moves = picking.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            self.assertEquals(line.qty_to_refund, 0,
                              "Wrong qty to refund")
            self.assertEquals(line.qty_to_refunded, 0,
                              "Wrong qty refunded")
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
        pickings.action_assign()
        pickings.do_transfer()
        for line in self.rma_id.rma_line_ids:
            self.assertEquals(line.qty_to_receive, 0,
                              "Wrong qty to receive")
            self.assertEquals(line.qty_incoming, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_to_refund, 0,
                              "Wrong qty to refund")
            self.assertEquals(line.qty_to_refunded, 0,
                              "Wrong qty refunded")
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
        self.rma_id.action_rma_done()
