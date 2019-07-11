# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaRepair(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaRepair, cls).setUpClass()

        cls.rma_obj = cls.env['rma.order']
        cls.rma_line_obj = cls.env['rma.order.line']
        cls.rma_op = cls.env['rma.operation']
        cls.rma_add_invoice_wiz = cls.env['rma_add_invoice']
        cls.rma_make_repair_wiz = cls.env['rma.order.line.make.repair']
        cls.acc_obj = cls.env['account.account']
        cls.inv_obj = cls.env['account.invoice']
        cls.invl_obj = cls.env['account.invoice.line']
        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']

        cls.rma_route_cust = cls.env.ref('rma.route_rma_customer')
        receivable_type = cls.env.ref('account.data_account_type_receivable')

        # Create partners
        customer1 = cls.partner_obj.create({'name': 'Customer 1'})

        # Create RMA group and operation:
        cls.rma_group_customer = cls.rma_obj.create({
            'partner_id': customer1.id,
            'type': 'customer',
        })
        cls.operation_1 = cls.rma_op.create({
            'code': 'TEST',
            'name': 'Repair afer receive',
            'type': 'customer',
            'receipt_policy': 'ordered',
            'repair_type': 'received',
            'in_route_id': cls.rma_route_cust.id,
            'out_route_id': cls.rma_route_cust.id,
        })
        cls.operation_2 = cls.rma_op.create({
            'code': 'TEST',
            'name': 'Repair on order',
            'type': 'customer',
            'receipt_policy': 'ordered',
            'repair_type': 'ordered',
            'in_route_id': cls.rma_route_cust.id,
            'out_route_id': cls.rma_route_cust.id,
        })
        cls.operation_3 = cls.rma_op.create({
            'code': 'TEST',
            'name': 'Deliver after repair',
            'type': 'customer',
            'receipt_policy': 'ordered',
            'repair_type': 'ordered',
            'delivery_policy': 'repair',
            'in_route_id': cls.rma_route_cust.id,
            'out_route_id': cls.rma_route_cust.id,
        })
        # Create products
        cls.product_1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
            'list_price': 100.0,
            'rma_customer_operation_id': cls.operation_1.id,
        })
        cls.product_2 = cls.product_obj.create({
            'name': 'Test Product 2',
            'type': 'product',
            'list_price': 150.0,
            'rma_customer_operation_id': cls.operation_2.id,
        })
        cls.product_3 = cls.product_obj.create({
            'name': 'Test Product 3',
            'type': 'product',
            'list_price': 1.0,
            'rma_customer_operation_id': cls.operation_3.id,
        })
        # Create Invoices:
        customer_account = cls.acc_obj.search(
            [('user_type_id', '=', receivable_type.id)], limit=1).id
        cls.inv_customer = cls.inv_obj.create({
            'partner_id': customer1.id,
            'account_id': customer_account,
            'type': 'out_invoice',
        })
        cls.inv_line_1 = cls.invl_obj.create({
            'name': cls.product_1.name,
            'product_id': cls.product_1.id,
            'quantity': 12.0,
            'price_unit': 100.0,
            'invoice_id': cls.inv_customer.id,
            'uom_id': cls.product_1.uom_id.id,
            'account_id': customer_account,
        })
        cls.inv_line_2 = cls.invl_obj.create({
            'name': cls.product_2.name,
            'product_id': cls.product_2.id,
            'quantity': 15.0,
            'price_unit': 150.0,
            'invoice_id': cls.inv_customer.id,
            'uom_id': cls.product_2.uom_id.id,
            'account_id': customer_account,
        })
        cls.inv_customer2 = cls.inv_obj.create({
            'partner_id': customer1.id,
            'account_id': customer_account,
            'type': 'out_invoice',
        })
        cls.inv_line_3 = cls.invl_obj.create({
            'name': cls.product_3.name,
            'product_id': cls.product_3.id,
            'quantity': 1.0,
            'price_unit': 1000.0,
            'invoice_id': cls.inv_customer2.id,
            'uom_id': cls.product_3.uom_id.id,
            'account_id': customer_account,
        })
        cls.rma_group_customer_2 = cls.rma_obj.create({
            'partner_id': customer1.id,
            'type': 'customer',
        })

    def test_01_add_from_invoice_customer(self):
        """Test wizard to create RMA from a customer invoice."""
        add_inv = self.rma_add_invoice_wiz.with_context({
            'customer': True,
            'active_ids': self.rma_group_customer.id,
            'active_model': 'rma.order',
        }).create({
            'invoice_line_ids':
                [(6, 0, self.inv_customer.invoice_line_ids.ids)],
        })
        add_inv.add_lines()
        self.assertEqual(len(self.rma_group_customer.rma_line_ids), 2)
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1)
        rma_1.repair_type = self.operation_1.repair_type
        self.assertEquals(rma_1.operation_id, self.operation_1,
                          "Operation should be operation_1")
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2)
        rma_2.repair_type = self.operation_2.repair_type
        self.assertEquals(rma_2.operation_id, self.operation_2,
                          "Operation should be operation_2")

    def test_02_rma_repair_operation(self):
        """Test RMA quantities using repair operations."""
        # Received repair_type:
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1)
        self.assertEquals(rma_1.operation_id.repair_type, 'received',
                          "Incorrect Repair operation")
        self.assertEquals(rma_1.qty_to_repair, 0.0,
                          "Quantity to repair should be 0.0")
        # Ordered repair_type:
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2)
        self.assertEquals(rma_2.operation_id.repair_type, 'ordered',
                          "Incorrect Repair operation")
        self.assertEqual(rma_2.qty_to_repair, 15.0)

    def test_03_create_repair_order(self):
        """Generate a Repair Order from a customer RMA."""
        rma = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2)
        rma.action_rma_to_approve()
        rma.action_rma_approve()
        self.assertEqual(rma.repair_count, 0)
        self.assertEqual(rma.qty_to_repair, 15.0)
        self.assertEqual(rma.qty_repaired, 0.0)
        make_repair = self.rma_make_repair_wiz.with_context({
            'customer': True,
            'active_ids': rma.ids,
            'active_model': 'rma.order.line',
        }).create({
            'description': 'Test refund',
        })
        make_repair.make_repair_order()
        rma.repair_ids.action_repair_confirm()
        self.assertEqual(rma.repair_count, 1)
        self.assertEqual(rma.qty_to_repair, 0.0)
        self.assertEqual(rma.qty_repaired, 15.0)

    def test_04_deliver_after_repair(self):
        """Only deliver after repair"""
        add_inv = self.rma_add_invoice_wiz.with_context({
            'customer': True,
            'active_ids': self.rma_group_customer_2.id,
            'active_model': 'rma.order',
        }).create({
            'invoice_line_ids':
                [(6, 0, self.inv_customer2.invoice_line_ids.ids)],
        })
        add_inv.add_lines()
        rma = self.rma_group_customer_2.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_3)
        rma.operation_id = self.operation_3.id
        rma._onchange_operation_id()
        rma.action_rma_to_approve()
        rma.action_rma_approve()
        self.assertEqual(rma.qty_to_deliver, 0.0)
        make_repair = self.rma_make_repair_wiz.with_context({
            'customer': True,
            'active_ids': rma.ids,
            'active_model': 'rma.order.line',
        }).create({
            'description': 'Test deliver',
        })
        make_repair.make_repair_order()
        rma.repair_ids.action_repair_confirm()
        self.assertEqual(rma.qty_to_deliver, 1.0)
