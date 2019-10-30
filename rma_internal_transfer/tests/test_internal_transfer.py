# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaInternalTransfer(common.SavepointCase):
    """ Test the routes and the quantities """

    @classmethod
    def setUpClass(cls):
        super(TestRmaInternalTransfer, cls).setUpClass()

        cls.rma_make_picking = cls.env['rma_internal_transfer.wizard']
        cls.stockpicking = cls.env['stock.picking']
        cls.rma_add_stock_move = cls.env['rma_add_stock_move']
        cls.rma = cls.env['rma.order']
        cls.rma_line = cls.env['rma.order.line']
        cls.product_1 = cls.env.ref('product.product_product_25')
        cls.partner_id = cls.env.ref('base.res_partner_2')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        wh = cls.env.ref('stock.warehouse0')
        cls.product_uom_id = cls.env.ref('uom.product_uom_unit')
        cls.stock_rma_location = wh.lot_rma_id
        cls.customer_location = cls.env.ref(
            'stock.stock_location_customers')
        cls.supplier_location = cls.env.ref(
            'stock.stock_location_suppliers')
        # Customer RMA:
        products2move = [(cls.product_1, 3)]
        cls.rma_customer_id = cls._create_rma_from_move(
            products2move, 'customer', cls.env.ref('base.res_partner_2'),
            dropship=False)
        cls.rma_customer_id.rma_line_ids._onchange_operation_id()
        seq = cls.env['ir.sequence'].search([], limit=1)
        cls.env['stock.picking.type'].create({
            "name": "TEST INTERNAL",
            "sequence_id": seq.id,
            "default_location_src_id": cls.stock_rma_location.id,
            "default_location_dest_id": cls.stock_rma_location.id,
            "warehouse_id": wh.id,
            "code": "internal"})

    @classmethod
    def _create_picking(cls, partner):
        return cls.stockpicking.create({
            'partner_id': partner.id,
            'picking_type_id': cls.env.ref('stock.picking_type_in').id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.supplier_location.id
            })

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

    @classmethod
    def _create_rma_from_move(cls, products2move, r_type, partner, dropship,
                              supplier_address_id=None):
        picking_in = cls._create_picking(partner)

        moves = []
        for item in products2move:
            move_values = cls._prepare_move(
                item[0], item[1], cls.stock_location,
                cls.customer_location, picking_in)
            moves.append(cls.env['stock.move'].create(move_values))

        # Create the RMA from the stock_move
        rma_id = cls.rma.create(
            {
                'reference': '0001',
                'type': r_type,
                'partner_id': partner.id,
                'company_id': cls.env.ref('base.main_company').id
            })
        for move in moves:
            data = {}
            if r_type == 'customer':
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

                if move.product_id.rma_customer_operation_id:
                    move.product_id.rma_customer_operation_id.in_route_id = \
                        False
                move.product_id.categ_id.rma_customer_operation_id = False
                move.product_id.rma_customer_operation_id = False
                wizard._prepare_rma_line_from_stock_move(move)

            cls.line = cls.rma_line.create(data)
            cls.line.action_rma_to_approve()
            cls.line.action_rma_approve()
        return rma_id

    def test_0_internal_transfer(self):
        wizard = self.rma_make_picking.with_context({
            'active_ids': self.rma_customer_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'internal',
            'active_id': self.rma_customer_id.id
        }).create({})

        wizard.action_create_picking()
        res = self.rma_customer_id.rma_line_ids.action_view_in_shipments()
        self.assertTrue('res_id' in res,
                        "Incorrect number of pickings created")
