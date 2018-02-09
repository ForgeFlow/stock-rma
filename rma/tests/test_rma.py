# Copyright (C) 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common
from odoo.exceptions import ValidationError


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
        self.product_1 = self.env.ref('product.product_product_25')
        self.product_2 = self.env.ref('product.product_product_7')
        self.product_3 = self.env.ref('product.product_product_11')
        self.uom_unit = self.env.ref('product.product_uom_unit')
        # assign an operation
        self.product_id.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
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
            products2move, 'customer', self.partner_id,
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
        for move in moves:
            if type == 'customer':
                wizard = self.rma_add_stock_move.new(
                    {'stock_move_id': move.id, 'customer': True,
                     'active_ids': rma_id.id,
                     'partner_id': move.partner_id.id,
                     'active_model': 'rma.order',
                     }
                )
                wizard.with_context({
                    'stock_move_id': move.id, 'customer': True,
                    'active_ids': rma_id.id,
                    'partner_id': move.partner_id.id,
                    'active_model': 'rma.order',
                }).default_get([str(move.id),
                                str(self.partner_id.id)])
                data = wizard.with_context(customer=1).\
                    _prepare_rma_line_from_stock_move(move)
                wizard.add_lines()
                data['partner_id'] = move.partner_id.id
                for operation in move.product_id.rma_customer_operation_id:
                    operation.in_route_id = False
                move.product_id.categ_id.rma_customer_operation_id = False
                move.product_id.rma_customer_operation_id = False
                wizard._prepare_rma_line_from_stock_move(move)

            else:
                wizard = self.rma_add_stock_move.new(
                    {'stock_move_id': move.id, 'supplier': True,
                     'active_ids': rma_id.id,
                     'partner_id': move.partner_id.id,
                     'active_model': 'rma.order',
                     }
                )
                wizard.with_context(
                    {'stock_move_id': move.id, 'supplier': True,
                     'active_ids': rma_id.id,
                     'partner_id': move.partner_id.id,
                     'active_model': 'rma.order',
                     }).default_get([str(move.id),
                                     str(self.partner_id.id)])
                wizard._prepare_rma_line_from_stock_move(move)
                wizard.add_lines()

                wizard = self.rma_add_stock_move.new(
                    {'stock_move_id': move.id, 'supplier': True,
                     'active_ids': [],
                     'partner_id': move.partner_id.id,
                     'active_model': 'rma.order',
                     }
                )
                wizard.add_lines()

                wizard = self.rma_add_stock_move.new(
                    {'stock_move_id': move.id, 'supplier': True,
                     'active_ids': rma_id.id,
                     'partner_id': move.partner_id.id,
                     'active_model': 'rma.order',
                     }
                )
                data = wizard._prepare_rma_line_from_stock_move(move)
                data['partner_id'] = move.partner_id.id
                for operation in move.product_id.rma_customer_operation_id:
                    operation.in_route_id = False
                move.product_id.rma_customer_operation_id = False
                wizard.add_lines()

            if dropship:
                data.update(customer_to_supplier=dropship,
                            supplier_address_id=supplier_address_id.id)
                data['partner_id'] = move.partner_id.id
            data['rma_id'] = rma_id.id
            self.line = self.rma_line.create(data)
            # approve the RMA Line
            self.rma_line.action_rma_to_approve()
            self.line.action_rma_approve()
        rma_id._get_default_type()
        rma_id._compute_in_shipment_count()
        rma_id._compute_out_shipment_count()
        rma_id._compute_supplier_line_count()
        rma_id._compute_line_count()
        rma_id.action_view_in_shipments()
        rma_id.action_view_out_shipments()
        rma_id.action_view_lines()

        rma_id.partner_id.action_open_partner_rma()
        rma_id.partner_id._compute_rma_line_count()
        # approve the RMA
        for line in rma_id.rma_line_ids:
            line.action_rma_to_approve()
            line.action_rma_approve()
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

    def test_rma_order_line(self):
        partner2 = self.env.ref('base.res_partner_2')
        picking_in = self._create_picking(partner2)
        moves_1 = []
        move_values = self._prepare_move(self.product_1, 3,
                                         self.stock_location,
                                         self.customer_location, picking_in)
        moves_1.append(self.env['stock.move'].create(move_values))
        wizard_1 = self.rma_add_stock_move.new(
            {'supplier': True,
             'stock_move_id': [(6, 0, [m.id for m in moves_1])],
             'active_ids': self.rma_customer_id.id,
             'active_model': 'rma.order',
             'partner_id': self.partner_id.id,
             'move_ids': [(6, 0, [m.id for m in moves_1])]
             }
        )
        wizard_1.add_lines()

        for line in self.rma_customer_id.rma_line_ids:
            line.with_context({'default_rma_id': line.rma_id.id
                               })._default_warehouse_id()
            line._default_location_id()
            line.with_context({'partner_id': line.rma_id.partner_id.id
                               })._default_delivery_address()
            line._compute_in_shipment_count()
            line._compute_out_shipment_count()

            data = {'reference_move_id': line.reference_move_id.id}
            new_line = self.rma_line.new(data)
            new_line._onchange_reference_move_id()

            line.action_rma_to_approve()
            line.action_rma_draft()
            line.action_rma_done()

            data = {'product_id': line.product_id.id}
            new_line = self.rma_line.new(data)
            new_line._onchange_product_id()

            data = {'operation_id': line.operation_id.id}
            new_line = self.rma_line.new(data)
            new_line._onchange_operation_id()

            data = {'customer_to_supplier': line.customer_to_supplier}
            new_line = self.rma_line.new(data)
            new_line._onchange_receipt_policy()

            data = {'lot_id': line.lot_id.id}
            new_line = self.rma_line.new(data)
            new_line._onchange_lot_id()

            line.action_view_in_shipments()
            line.action_view_out_shipments()
            self.rma_customer_id.action_view_supplier_lines()
            with self.assertRaises(ValidationError):
                line.rma_id.partner_id = partner2.id
                self.rma_customer_id.rma_line_ids[0].\
                    partner_id = partner2.id
        self.rma_customer_id.action_view_supplier_lines()

    def test_customer_rma(self):
        wizard = self.rma_make_picking.with_context({
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
            'active_id': 1
        }).create({'rma_id': self.rma_customer_id.id})
        wizard.with_context({
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
            'active_id': 1
        }).default_get({})
        procurements = wizard._create_picking()
        domain = [('origin', '=', procurements)]
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
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            # product specific
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_deliver, 0,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 3,
                                  "Wrong qty incoming")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_deliver, 0,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 5,
                                  "Wrong qty incoming")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_deliver, 0,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_incoming, 2,
                                  "Wrong qty incoming")
        picking.action_assign()
        picking.force_assign()
        picking.do_new_transfer()
        for line in self.rma_customer_id.rma_line_ids:
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty to_receive")
#            self.assertEquals(line.qty_incoming, 5,
#                              "Wrong qty incoming")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to received")
                self.assertEquals(line.qty_incoming, 3,
                                  "Wrong qty incoming")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to received")
                self.assertEquals(line.qty_incoming, 5,
                                  "Wrong qty incoming")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to received")
                self.assertEquals(line.qty_incoming, 2,
                                  "Wrong qty incoming")

        wizard = self.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'outgoing',
        }).create({})
        procurements = wizard._create_picking()
        domain = [('origin', '=', procurements)]
        pickings = self.stockpicking.search(domain)
        self.assertEquals(len(pickings), 2,
                          "Incorrect number of pickings created")
        picking_out = pickings[0]
        moves = picking_out.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in self.rma_customer_id.rma_line_ids:
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty receive")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_deliver, 0,
                                  "Wrong qty to deliver")
                self.assertEquals(line.qty_outgoing, 0,
                                  "Wrong qty outgoing")
                self.assertEquals(line.qty_received, 0,
                                  "Wrong qty received")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to received")
                self.assertEquals(line.qty_incoming, 5,
                                  "Wrong qty incoming")
                self.assertEquals(line.qty_outgoing, 0,
                                  "Wrong qty outgoing")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to received")
                self.assertEquals(line.qty_incoming, 2,
                                  "Wrong qty incoming")
                self.assertEquals(line.qty_outgoing, 0,
                                  "Wrong qty outgoing")
        picking_out.action_assign()
        picking_out.do_new_transfer()
        for line in self.rma_customer_id.rma_line_ids[0]:
            self.assertEquals(line.qty_to_receive, 3,
                              "Wrong qty to receive")
            self.assertEquals(line.qty_incoming, 3,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_to_deliver, 0,
                              "Wrong qty to deliver")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty outgoing")
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to received")
                self.assertEquals(line.qty_to_deliver, 0,
                                  "Wrong qty to delivered")
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
        self.rma_customer_id.action_view_in_shipments()
        self.rma_customer_id.action_view_out_shipments()
        self.rma_customer_id.action_view_lines()
