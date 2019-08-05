# Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaAccount(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaAccount, cls).setUpClass()

        cls.rma_obj = cls.env['rma.order']
        cls.rma_line_obj = cls.env['rma.order.line']
        cls.rma_op_obj = cls.env['rma.operation']
        cls.rma_add_invoice_wiz = cls.env['rma_add_invoice']
        cls.rma_refund_wiz = cls.env['rma.refund']
        cls.acc_obj = cls.env['account.account']
        cls.inv_obj = cls.env['account.invoice']
        cls.invl_obj = cls.env['account.invoice.line']
        cls.product_obj = cls.env['product.product']
        cls.partner_obj = cls.env['res.partner']

        cls.rma_route_cust = cls.env.ref('rma.route_rma_customer')
        receivable_type = cls.env.ref('account.data_account_type_receivable')
        payable_type = cls.env.ref('account.data_account_type_payable')
        cls.cust_refund_op = cls.env.ref(
            'rma_account.rma_operation_customer_refund')

        # Create partners
        customer1 = cls.partner_obj.create({'name': 'Customer 1'})
        supplier1 = cls.partner_obj.create({'name': 'Supplier 1'})

        # Create RMA group and operation:
        cls.rma_group_customer = cls.rma_obj.create({
            'partner_id': customer1.id,
            'type': 'customer',
        })
        cls.rma_group_supplier = cls.rma_obj.create({
            'partner_id': supplier1.id,
            'type': 'supplier',
        })
        cls.operation_1 = cls.rma_op_obj.create({
            'code': 'TEST',
            'name': 'Refund and receive',
            'type': 'customer',
            'receipt_policy': 'ordered',
            'refund_policy': 'ordered',
            'in_route_id': cls.rma_route_cust.id,
            'out_route_id': cls.rma_route_cust.id,
        })

        # Create products
        cls.product_1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
            'list_price': 100.0,
            'rma_customer_operation_id': cls.cust_refund_op.id,
        })
        cls.product_2 = cls.product_obj.create({
            'name': 'Test Product 2',
            'type': 'product',
            'list_price': 150.0,
            'rma_customer_operation_id': cls.operation_1.id,
        })
        cls.product_3 = cls.product_obj.create({
            'name': 'Test Product 3',
            'type': 'product',
        })
        cls.product_4 = cls.product_obj.create({
            'name': 'Test Product 4',
            'type': 'product',
        })

        # Create Invoices:
        customer_account = cls.acc_obj. search(
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

        supplier_account = cls.acc_obj.search(
            [('user_type_id', '=', payable_type.id)], limit=1).id
        cls.inv_supplier = cls.inv_obj.create({
            'partner_id': supplier1.id,
            'account_id': supplier_account,
            'type': 'in_invoice',
        })
        cls.inv_line_3 = cls.invl_obj.create({
            'name': cls.product_3.name,
            'product_id': cls.product_3.id,
            'quantity': 17.0,
            'price_unit': 250.0,
            'invoice_id': cls.inv_supplier.id,
            'uom_id': cls.product_3.uom_id.id,
            'account_id': supplier_account,
        })
        cls.inv_line_4 = cls.invl_obj.create({
            'name': cls.product_4.name,
            'product_id': cls.product_4.id,
            'quantity': 9.0,
            'price_unit': 300.0,
            'invoice_id': cls.inv_supplier.id,
            'uom_id': cls.product_4.uom_id.id,
            'account_id': supplier_account,
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
        for t in self.rma_group_supplier.rma_line_ids.mapped('type'):
            self.assertEqual(t, 'customer')
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1)
        self.assertEqual(rma_1.operation_id, self.cust_refund_op)
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2)
        self.assertEqual(rma_2.operation_id, self.operation_1)

    def test_02_add_from_invoice_supplier(self):
        """Test wizard to create RMA from a vendor bill."""
        add_inv = self.rma_add_invoice_wiz.with_context({
            'supplier': True,
            'active_ids': self.rma_group_supplier.id,
            'active_model': 'rma.order',
        }).create({
            'invoice_line_ids':
                [(6, 0, self.inv_supplier.invoice_line_ids.ids)],
        })
        add_inv.add_lines()
        self.assertEqual(len(self.rma_group_supplier.rma_line_ids), 2)
        for t in self.rma_group_supplier.rma_line_ids.mapped('type'):
            self.assertEqual(t, 'supplier')

    def test_03_rma_refund_operation(self):
        """Test RMA quantities using refund operations."""
        # Received refund_policy:
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1)
        self.assertEqual(rma_1.refund_policy, 'received')
        self.assertEqual(rma_1.qty_to_refund, 0.0)
        # TODO: receive and check qty_to_refund is 12.0
        # Ordered refund_policy:
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2)
        rma_2._onchange_operation_id()
        self.assertEqual(rma_2.refund_policy, 'ordered')
        self.assertEqual(rma_2.qty_to_refund, 15.0)

    def test_04_rma_create_refund(self):
        """Generate a Refund from a customer RMA."""
        rma = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2)
        rma.action_rma_to_approve()
        rma.action_rma_approve()
        self.assertEqual(rma.refund_count, 0)
        self.assertEqual(rma.qty_to_refund, 15.0)
        self.assertEqual(rma.qty_refunded, 0.0)
        make_refund = self.rma_refund_wiz.with_context({
            'customer': True,
            'active_ids': rma.ids,
            'active_model': 'rma.order.line',
        }).create({
            'description': 'Test refund',
        })
        make_refund.invoice_refund()
        rma.refund_line_ids.invoice_id.action_invoice_open()
        rma._compute_refund_count()
        self.assertEqual(rma.refund_count, 1)
        self.assertEqual(rma.qty_to_refund, 0.0)
        self.assertEqual(rma.qty_refunded, 15.0)

    def test_05_fill_rma_from_inv_line(self):
        """Test filling a RMA (line) from a invoice line."""
        rma = self.rma_line_obj.new({
            'partner_id': self.inv_customer.partner_id.id,
            'invoice_line_id': self.inv_line_1.id,
        })
        self.assertFalse(rma.product_id)
        rma._onchange_invoice_line_id()
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_qty, 12.0)
