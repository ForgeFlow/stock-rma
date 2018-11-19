# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common
from odoo.exceptions import ValidationError


class TestRma(common.SavepointCase):
    """ Test the routes and the quantities """

    @classmethod
    def setUpClass(cls):
        super(TestRma, cls).setUpClass()

        cls.rma_make_picking = cls.env['rma_make_picking.wizard']
        cls.make_supplier_rma = cls.env["rma.order.line.make.supplier.rma"]
        cls.rma_add_stock_move = cls.env['rma_add_stock_move']
        cls.stockpicking = cls.env['stock.picking']
        cls.rma = cls.env['rma.order']
        cls.rma_line = cls.env['rma.order.line']
        cls.rma_op = cls.env['rma.operation']
        cls.rma_cust_replace_op_id = cls.env.ref(
            'rma.rma_operation_customer_replace')
        cls.rma_sup_replace_op_id = cls.env.ref(
            'rma.rma_operation_supplier_replace')
        cls.rma_ds_replace_op_id = cls.env.ref(
            'rma.rma_operation_ds_replace')
        cls.product_id = cls.env.ref('product.product_product_4')
        cls.product_1 = cls.env.ref('product.product_product_25')
        cls.product_2 = cls.env.ref('product.product_product_22')
        cls.product_3 = cls.env.ref('product.product_product_20')
        cls.uom_unit = cls.env.ref('uom.product_uom_unit')
        # assign an operation
        cls.product_1.write(
            {'rma_customer_operation_id': cls.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': cls.rma_sup_replace_op_id.id})
        cls.product_2.write(
            {'rma_customer_operation_id': cls.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': cls.rma_sup_replace_op_id.id})
        cls.product_3.write(
            {'rma_customer_operation_id': cls.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': cls.rma_sup_replace_op_id.id})
        cls.partner_id = cls.env.ref('base.res_partner_2')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        wh = cls.env.ref('stock.warehouse0')
        cls.stock_rma_location = wh.lot_rma_id
        cls.customer_location = cls.env.ref(
            'stock.stock_location_customers')
        cls.supplier_location = cls.env.ref(
            'stock.stock_location_suppliers')
        cls.product_uom_id = cls.env.ref('uom.product_uom_unit')
        # Customer RMA:
        products2move = [(cls.product_1, 3), (cls.product_2, 5),
                         (cls.product_3, 2)]
        cls.rma_customer_id = cls._create_rma_from_move(
            products2move, 'customer', cls.env.ref('base.res_partner_2'),
            dropship=False)
        # Dropship:
        cls.rma_droship_id = cls._create_rma_from_move(
            products2move, 'customer', cls.env.ref('base.res_partner_2'),
            dropship=True,
            supplier_address_id=cls.env.ref('base.res_partner_3'))
        # Supplier RMA:
        cls.rma_supplier_id = cls._create_rma_from_move(
            products2move, 'supplier', cls.env.ref('base.res_partner_2'),
            dropship=False)

    @classmethod
    def _create_picking(cls, partner):
        return cls.stockpicking.create({
            'partner_id': partner.id,
            'picking_type_id': cls.env.ref('stock.picking_type_in').id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.supplier_location.id
            })

    @classmethod
    def _create_rma_from_move(cls, products2move, type, partner, dropship,
                              supplier_address_id=None):
        picking_in = cls._create_picking(partner)

        moves = []
        if type == 'customer':
            for item in products2move:
                move_values = cls._prepare_move(
                    item[0], item[1], cls.stock_location,
                    cls.customer_location, picking_in)
                moves.append(cls.env['stock.move'].create(move_values))
        else:
            for item in products2move:
                move_values = cls._prepare_move(
                    item[0], item[1], cls.supplier_location,
                    cls.stock_rma_location, picking_in)
                moves.append(cls.env['stock.move'].create(move_values))
        # Create the RMA from the stock_move
        rma_id = cls.rma.create(
            {
                'reference': '0001',
                'type': type,
                'partner_id': partner.id,
                'company_id': cls.env.ref('base.main_company').id
            })
        for move in moves:
            if type == 'customer':
                wizard = cls.rma_add_stock_move.new(
                    {'stock_move_id': move.id, 'customer': True,
                     'active_ids': rma_id.id,
                     'rma_id': rma_id.id,
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
                                str(cls.partner_id.id)])
                data = wizard.with_context(customer=1).\
                    _prepare_rma_line_from_stock_move(move)
                wizard.add_lines()

                for operation in move.product_id.rma_customer_operation_id:
                    operation.in_route_id = False
                move.product_id.categ_id.rma_customer_operation_id = False
                move.product_id.rma_customer_operation_id = False
                wizard._prepare_rma_line_from_stock_move(move)

            else:
                wizard = cls.rma_add_stock_move.new(
                    {'stock_move_id': move.id, 'supplier': True,
                     'active_ids': rma_id.id,
                     'rma_id': rma_id.id,
                     'partner_id': move.partner_id.id,
                     'active_model': 'rma.order',
                     }
                )
                wizard.with_context({
                    'stock_move_id': move.id, 'supplier': True,
                    'active_ids': rma_id.id,
                    'partner_id': move.partner_id.id,
                    'active_model': 'rma.order',
                }).default_get([str(move.id),
                                str(cls.partner_id.id)])
                data = wizard.with_context(customer=1).\
                    _prepare_rma_line_from_stock_move(move)
                wizard.add_lines()

                for operation in move.product_id.rma_customer_operation_id:
                    operation.in_route_id = False
                move.product_id.categ_id.rma_supplier_operation_id = False
                move.product_id.rma_supplier_operation_id = False
                wizard._prepare_rma_line_from_stock_move(move)

            if dropship:
                data.update(customer_to_supplier=dropship,
                            operation_id=cls.rma_ds_replace_op_id.id,
                            supplier_address_id=supplier_address_id.id)
            cls.line = cls.rma_line.create(data)
            cls.line.action_rma_to_approve()
            cls.line.action_rma_approve()
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
        return rma_id

    @classmethod
    def _prepare_move(cls, product, qty, src, dest, picking_in):
        res = {
            'partner_id': cls.partner_id.id,
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': cls.product_uom_id.id or product.uom_id.id,
            'product_uom_qty': qty,
            'origin': 'Test RMA',
            'location_id': src.id,
            'location_dest_id': dest.id,
            'picking_id': picking_in.id
        }
        return res

    def test_01_rma_order_line(cls):
        for line in cls.rma_customer_id.rma_line_ids:
            line.with_context({'default_rma_id': line.rma_id.id
                               })._default_warehouse_id()
            line._default_location_id()
            line.with_context({'partner_id': line.rma_id.partner_id.id
                               })._default_delivery_address()
            line._compute_in_shipment_count()
            line._compute_out_shipment_count()

            data = {'reference_move_id': line.reference_move_id.id}
            new_line = cls.rma_line.new(data)
            new_line._onchange_reference_move_id()

            # check assert if call reference_move_id onchange
            cls.assertEquals(new_line.product_id,
                             line.reference_move_id.product_id)
            cls.assertEquals(new_line.product_qty,
                             line.reference_move_id.product_uom_qty)
            cls.assertEquals(new_line.location_id.location_id,
                             line.reference_move_id.location_id)
            cls.assertEquals(new_line.origin,
                             line.reference_move_id.picking_id.name)
            cls.assertEquals(new_line.delivery_address_id,
                             line.reference_move_id.picking_partner_id)
            cls.assertEquals(new_line.qty_to_receive,
                             line.reference_move_id.product_uom_qty)

            line.action_rma_to_approve()
            line.action_rma_draft()
            line.action_rma_done()

            data = {'product_id': line.product_id.id}
            new_line = cls.rma_line.new(data)
            new_line._onchange_product_id()

            data = {'operation_id': line.operation_id.id}
            new_line = cls.rma_line.new(data)
            new_line._onchange_operation_id()

            # check assert if call operation_id onchange
            cls.assertEquals(new_line.operation_id.receipt_policy,
                             line.receipt_policy)

            data = {'customer_to_supplier': line.customer_to_supplier}
            new_line = cls.rma_line.new(data)
            new_line._onchange_receipt_policy()

            data = {'lot_id': line.lot_id.id}
            new_line = cls.rma_line.new(data)
            new_line._onchange_lot_id()

            line.action_view_in_shipments()
            line.action_view_out_shipments()
            cls.rma_customer_id.action_view_supplier_lines()
            with cls.assertRaises(ValidationError):
                line.rma_id.partner_id = cls.partner_id.id
                cls.rma_customer_id.rma_line_ids[0].\
                    partner_id = cls.env.ref('base.res_partner_3').id
        cls.rma_customer_id.action_view_supplier_lines()

    def test_02_customer_rma(cls):
        wizard = cls.rma_make_picking.with_context({
            'active_ids': cls.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
            'active_id': 1
        }).create({})
        wizard._create_picking()
        res = cls.rma_customer_id.rma_line_ids.action_view_in_shipments()
        cls.assertTrue('res_id' in res,
                       "Incorrect number of pickings created")
        picking = cls.env['stock.picking'].browse(res['res_id'])
        cls.assertEquals(len(picking), 1,
                         "Incorrect number of pickings created")
        moves = picking.move_lines
        cls.assertEquals(len(moves), 3,
                         "Incorrect number of moves created")
        for line in cls.rma_customer_id.rma_line_ids:
            # common qtys for all products
            cls.assertEquals(line.qty_received, 0,
                             "Wrong qty received")
            cls.assertEquals(line.qty_to_deliver, 0,
                             "Wrong qty to deliver")
            cls.assertEquals(line.qty_outgoing, 0,
                             "Wrong qty outgoing")
            cls.assertEquals(line.qty_delivered, 0,
                             "Wrong qty delivered")
            # product specific
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_to_receive, 3,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_incoming, 3,
                                 "Wrong qty incoming")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_to_receive, 5,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_incoming, 5,
                                 "Wrong qty incoming")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_to_receive, 2,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_incoming, 2,
                                 "Wrong qty incoming")
        picking.action_assign()
        for mv in picking.move_lines:
            mv.quantity_done = mv.product_uom_qty
        picking.action_done()
        for line in cls.rma_customer_id.rma_line_ids:
            cls.assertEquals(line.qty_to_receive, 0,
                             "Wrong qty to_receive")
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_outgoing, 0,
                             "Wrong qty outgoing")
            cls.assertEquals(line.qty_delivered, 0,
                             "Wrong qty delivered")
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_received, 3,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_to_deliver, 3,
                                 "Wrong qty to_deliver")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_received, 5,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_to_deliver, 5,
                                 "Wrong qty to_deliver")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_received, 2,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_to_deliver, 2,
                                 "Wrong qty to_deliver")

        wizard = cls.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': cls.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'outgoing',
        }).create({})
        wizard._create_picking()
        res = cls.rma_customer_id.rma_line_ids.action_view_out_shipments()
        cls.assertTrue('res_id' in res,
                       "Incorrect number of pickings created")
        picking = cls.env['stock.picking'].browse(res['res_id'])
        moves = picking.move_lines
        cls.assertEquals(len(moves), 3,
                         "Incorrect number of moves created")
        for line in cls.rma_customer_id.rma_line_ids:
            cls.assertEquals(line.qty_to_receive, 0,
                             "Wrong qty to receive")
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_delivered, 0,
                             "Wrong qty delivered")
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_to_deliver, 3,
                                 "Wrong qty to deliver")
                cls.assertEquals(line.qty_outgoing, 3,
                                 "Wrong qty outgoing")
                cls.assertEquals(line.qty_received, 3,
                                 "Wrong qty received")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_received, 5,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_to_deliver, 5,
                                 "Wrong qty to deliver")
                cls.assertEquals(line.qty_outgoing, 5,
                                 "Wrong qty outgoing")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_received, 2,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_to_deliver, 2,
                                 "Wrong qty to deliver")
                cls.assertEquals(line.qty_outgoing, 2,
                                 "Wrong qty outgoing")
        picking.action_assign()
        for mv in picking.move_lines:
            mv.quantity_done = mv.product_uom_qty
        picking.action_done()
        for line in cls.rma_customer_id.rma_line_ids:
            cls.assertEquals(line.qty_to_receive, 0,
                             "Wrong qty to receive")
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_to_deliver, 0,
                             "Wrong qty to deliver")
            cls.assertEquals(line.qty_outgoing, 0,
                             "Wrong qty outgoing")
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_received, 3,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_delivered, 3,
                                 "Wrong qty delivered")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_received, 5,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_delivered, 5,
                                 "Wrong qty delivered")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_received, 2,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_delivered, 2,
                                 "Wrong qty delivered")
            cls.line.action_rma_done()
            cls.assertEquals(cls.line.state, 'done',
                             "Wrong State")
        cls.rma_customer_id.action_view_in_shipments()
        cls.rma_customer_id.action_view_out_shipments()
        cls.rma_customer_id.action_view_lines()

    # DROPSHIP
    def test_03_dropship(cls):
        for line in cls.rma_droship_id.rma_line_ids:
            line.action_rma_to_approve()
            line.action_rma_approve()
            line._onchange_operation_id()
        wizard = cls.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': cls.rma_droship_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
        }).create({})
        wizard._create_picking()
        res = cls.rma_droship_id.rma_line_ids.action_view_in_shipments()
        cls.assertTrue('res_id' in res,
                       "Incorrect number of pickings created")
        picking = cls.env['stock.picking'].browse(res['res_id'])
        cls.assertEquals(len(picking), 1,
                         "Incorrect number of pickings created")
        moves = picking.move_lines
        cls.assertEquals(len(moves), 3,
                         "Incorrect number of moves created")
        wizard = cls.make_supplier_rma.with_context({
            'active_ids': cls.rma_droship_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'active_id': 1
        }).create({})
        res = wizard.make_supplier_rma()
        supplier_rma = cls.rma.browse(res['res_id'])
        for line in supplier_rma.rma_line_ids:
            # common qtys for all products
            cls.assertEquals(line.qty_received, 0,
                             "Wrong qty received")
            cls.assertEquals(line.qty_outgoing, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_delivered, 0,
                             "Wrong qty delivered")
            # product specific
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_to_deliver, 3,
                                 "Wrong qty to deliver")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_to_deliver, 5,
                                 "Wrong qty to deliver")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_to_deliver, 2,
                                 "Wrong qty to deliver")

        for line in cls.rma_droship_id.rma_line_ids:
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_to_supplier_rma, 0,
                                 "Wrong qty to supplier rma")
                cls.assertEquals(line.qty_in_supplier_rma, 3,
                                 "Wrong qty in supplier rma")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_to_supplier_rma, 0,
                                 "Wrong qty to supplier rma")
                cls.assertEquals(line.qty_in_supplier_rma, 5,
                                 "Wrong qty in supplier rma")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_to_supplier_rma, 0,
                                 "Wrong qty to supplier rma")
                cls.assertEquals(line.qty_in_supplier_rma, 2,
                                 "Wrong qty in supplier rma")
        for line in cls.rma_droship_id.rma_line_ids:
            line.action_rma_done()
            cls.assertEquals(line.state, 'done',
                             "Wrong State")

    # Supplier RMA
    def test_04_supplier_rma(cls):
        wizard = cls.rma_make_picking.with_context({
            'active_ids': cls.rma_supplier_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'outgoing',
            'active_id': 1
        }).create({})
        wizard._create_picking()
        res = cls.rma_supplier_id.rma_line_ids.action_view_out_shipments()
        cls.assertTrue('res_id' in res,
                       "Incorrect number of pickings created")
        picking = cls.env['stock.picking'].browse(res['res_id'])
        moves = picking.move_lines
        cls.assertEquals(len(moves), 3,
                         "Incorrect number of moves created")
        for line in cls.rma_supplier_id.rma_line_ids:
            # common qtys for all products
            cls.assertEquals(line.qty_received, 0,
                             "Wrong qty received")
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_delivered, 0,
                             "Wrong qty delivered")
            # product specific
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_to_receive, 3,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_to_deliver, 3,
                                 "Wrong qty to deliver")
                cls.assertEquals(line.qty_outgoing, 3,
                                 "Wrong qty outgoing")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_to_receive, 5,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_to_deliver, 5,
                                 "Wrong qty to deliver")
                cls.assertEquals(line.qty_outgoing, 5,
                                 "Wrong qty outgoing")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_to_receive, 2,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_to_deliver, 2,
                                 "Wrong qty to deliver")
                cls.assertEquals(line.qty_outgoing, 2,
                                 "Wrong qty outgoing")

        picking.action_assign()
        for mv in picking.move_lines:
            mv.quantity_done = mv.product_uom_qty
        picking.action_done()
        for line in cls.rma_supplier_id.rma_line_ids:
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_received, 0,
                             "Wrong qty received")
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_delivered, 3,
                                 "Wrong qty delivered")
                cls.assertEquals(line.qty_to_receive, 3,
                                 "Wrong qty to receive")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_delivered, 5,
                                 "Wrong qty delivered")
                cls.assertEquals(line.qty_to_receive, 5,
                                 "Wrong qty to receive")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_delivered, 2,
                                 "Wrong qty delivered")
                cls.assertEquals(line.qty_to_receive, 2,
                                 "Wrong qty to receive")
        wizard = cls.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': cls.rma_supplier_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
        }).create({})
        wizard._create_picking()
        res = cls.rma_supplier_id.rma_line_ids.action_view_in_shipments()
        cls.assertTrue('res_id' in res,
                       "Incorrect number of pickings created")
        pickings = cls.env['stock.picking'].browse(res['res_id'])
        cls.assertEquals(len(pickings), 1,
                         "Incorrect number of pickings created")
        picking_out = pickings[0]
        moves = picking_out.move_lines
        cls.assertEquals(len(moves), 3,
                         "Incorrect number of moves created")
        for line in cls.rma_supplier_id.rma_line_ids:
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_received, 0,
                             "Wrong qty received")
            cls.assertEquals(line.qty_to_deliver, 0,
                             "Wrong qty to deliver")
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_to_receive, 3,
                                 "Wrong qty to receive")
                cls.assertEquals(line.qty_incoming, 0,
                                 "Wrong qty incoming")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_to_receive, 5,
                                 "Wrong qty to receive")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_to_receive, 2,
                                 "Wrong qty to receive")
        picking_out.action_assign()
        for mv in picking.move_lines:
            mv.quantity_done = mv.product_uom_qty
        picking_out.action_done()
        for line in cls.rma_supplier_id.rma_line_ids[0]:
            cls.assertEquals(line.qty_to_receive, 3,
                             "Wrong qty to receive")
            cls.assertEquals(line.qty_incoming, 0,
                             "Wrong qty incoming")
            cls.assertEquals(line.qty_to_deliver, 0,
                             "Wrong qty to deliver")
            cls.assertEquals(line.qty_outgoing, 3,
                             "Wrong qty outgoing")
            if line.product_id == cls.product_1:
                cls.assertEquals(line.qty_received, 0,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_delivered, 3,
                                 "Wrong qty delivered")
            if line.product_id == cls.product_2:
                cls.assertEquals(line.qty_received, 0,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_delivered, 5,
                                 "Wrong qty delivered")
            if line.product_id == cls.product_3:
                cls.assertEquals(line.qty_received, 2,
                                 "Wrong qty received")
                cls.assertEquals(line.qty_delivered, 2,
                                 "Wrong qty delivered")
        for line in cls.rma_supplier_id.rma_line_ids:
            line.action_rma_done()
            cls.assertEquals(line.state, 'done',
                             "Wrong State")
