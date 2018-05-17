# Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp.tests import common
from openerp.fields import Datetime


class TestRmaPurchase(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaPurchase, cls).setUpClass()

        cls.rma_obj = cls.env['rma.order']
        cls.rma_line_obj = cls.env['rma.order.line']
        cls.rma_op_obj = cls.env['rma.operation']
        cls.rma_add_purchase_wiz = cls.env['rma_add_purchase']
        cls.po_obj = cls.env['purchase.order']
        cls.pol_obj = cls.env['purchase.order.line']
        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']

        cls.rma_route_cust = cls.env.ref('rma.route_rma_customer')

        # Create supplier
        supplier1 = cls.partner_obj.create({'name': 'Supplier 1'})

        # Create products
        cls.product_1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
        })
        cls.product_2 = cls.product_obj.create({
            'name': 'Test Product 2',
            'type': 'product',
        })

        # Create PO:
        cls.po = cls.po_obj.create({
            'partner_id': supplier1.id,
        })
        cls.pol_1 = cls.pol_obj.create({
            'name': cls.product_1.name,
            'order_id': cls.po.id,
            'product_id': cls.product_1.id,
            'product_qty': 20.0,
            'product_uom': cls.product_1.uom_id.id,
            'price_unit': 100.0,
            'date_planned': Datetime.now(),
        })
        cls.pol_2 = cls.pol_obj.create({
            'name': cls.product_2.name,
            'order_id': cls.po.id,
            'product_id': cls.product_2.id,
            'product_qty': 18.0,
            'product_uom': cls.product_2.uom_id.id,
            'price_unit': 150.0,
            'date_planned': Datetime.now(),
        })

        # Create RMA group:
        cls.rma_group = cls.rma_obj.create({
            'partner_id': supplier1.id,
            'type': 'supplier',
        })

    def test_01_add_from_purchase_order(self):
        """Test wizard to create supplier RMA from Purchase Orders."""
        self.assertEqual(self.rma_group.origin_po_count, 0)
        add_purchase = self.rma_add_purchase_wiz.with_context({
            'supplier': True,
            'active_ids': self.rma_group.id,
            'active_model': 'rma.order',
        }).create({
            'purchase_id': self.po.id,
            'purchase_line_ids': [(6, 0, self.po.order_line.ids)],
        })
        add_purchase.add_lines()
        self.assertEqual(len(self.rma_group.rma_line_ids), 2)
        for t in self.rma_group.rma_line_ids.mapped('type'):
            self.assertEqual(t, 'supplier')
        self.assertEqual(self.rma_group.origin_po_count, 1)

    def test_02_fill_rma_from_po_line(self):
        """Test filling a RMA (line) from a Purchase Order line."""
        rma = self.rma_line_obj.new({
            'partner_id': self.po.partner_id.id,
            'purchase_order_line_id': self.pol_1.id,
            'type': 'supplier',
        })
        self.assertFalse(rma.product_id)
        rma._onchange_purchase_order_line_id()
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_qty, 20.0)
