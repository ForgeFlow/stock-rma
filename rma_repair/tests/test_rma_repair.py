# -*- coding: utf-8 -*-
# Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp.tests import common


class TestRmaSale(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaSale, cls).setUpClass()

        cls.rma_obj = cls.env['rma.order']
        cls.rma_line_obj = cls.env['rma.order.line']
        cls.rma_op_obj = cls.env['rma.operation']
        cls.rma_make_sale_wiz = cls.env['rma.order.line.make.repair']
        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']

        cls.rma_route_cust = cls.env.ref('rma.route_rma_customer')

        # Create customer
        cls.customer1 = cls.partner_obj.create({'name': 'Customer 1'})

        # Create products
        cls.product_1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
            'list_price': 100.0,
        })
        cls.product_2 = cls.product_obj.create({
            'name': 'Test Product 2',
            'type': 'product',
            'list_price': 150.0,
        })

        # Create operations:
        cls.operation_1 = cls.rma_op_obj.create({
            'code': 'TEST',
            'name': 'Sale afer receive',
            'type': 'customer',
            'receipt_policy': 'ordered',
            'repair_policy': 'received',
            'in_route_id': cls.rma_route_cust.id,
            'out_route_id': cls.rma_route_cust.id,
        })
        cls.operation_2 = cls.rma_op_obj.create({
            'code': 'TEST',
            'name': 'Receive and Sale',
            'type': 'customer',
            'receipt_policy': 'ordered',
            'repair_policy': 'ordered',
            'in_route_id': cls.rma_route_cust.id,
            'out_route_id': cls.rma_route_cust.id,
        })

    def _convert_new_to_values(self, record):
        values = dict(record._cache)
        for key in values.keys():
            if '_id' in key:
                values[key] = values.get(key).id
        return values

    def test_01_rma_repair_operation_received(self):
        """Test RMA quantities using a repair operation with policy based on
        received quantities."""
        new_rma = self.rma_line_obj.new({
            'partner_id': self.customer1.id,
            'type': 'customer',
            'product_id': self.product_1.id,
            'product_qty': 10.0,
            'uom_id': self.product_1.uom_id.id,
            'operation_id': self.operation_1.id,
        })
        new_rma._onchange_operation_id()
        values = self._convert_new_to_values(new_rma)
        rma = self.rma_line_obj.create(values)
        self.assertEqual(rma.qty_to_repair, 0.0)
        # TODO: receive and check qty_to_repair is 10.0

    def test_02_rma_repair_operation_ordered(self):
        """Test RMA quantities using repair operations with policy based on
        ordered quantities."""
        new_rma = self.rma_line_obj.new({
            'partner_id': self.customer1.id,
            'type': 'customer',
            'product_id': self.product_2.id,
            'product_qty': 10.0,
            'uom_id': self.product_2.uom_id.id,
            'operation_id': self.operation_2.id,
        })
        new_rma._onchange_operation_id()
        values = self._convert_new_to_values(new_rma)
        rma = self.rma_line_obj.create(values)
        self.assertEqual(rma.qty_to_repair, 10.0)
        # create repair order:
        add_repair = self.rma_make_sale_wiz.with_context({
            'active_ids': rma.ids,
            'active_model': 'rma.order.line',
        }).create({})
        add_repair.make_repair_order()
        self.assertEqual(rma.qty_to_repair, 0.0)
        self.assertEqual(rma.qty_repaired, 10.0)
