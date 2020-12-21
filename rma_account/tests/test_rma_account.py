# Copyright 2017-18 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields
from odoo.tests import common


class TestRmaAccount(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestRmaAccount, cls).setUpClass()

        cls.rma_obj = cls.env["rma.order"]
        cls.rma_line_obj = cls.env["rma.order.line"]
        cls.rma_op_obj = cls.env["rma.operation"]
        cls.rma_add_invoice_wiz = cls.env["rma_add_account_move"]
        cls.rma_refund_wiz = cls.env["rma.refund"]
        cls.acc_obj = cls.env["account.account"]
        cls.inv_obj = cls.env["account.move"]
        cls.invl_obj = cls.env["account.move.line"]
        cls.product_obj = cls.env["product.product"]
        customer1_obj = cls.env["res.partner"]

        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")
        receivable_type = cls.env.ref("account.data_account_type_receivable")
        cls.cust_refund_op = cls.env.ref("rma_account.rma_operation_customer_refund")
        cls.sup_refund_op = cls.env.ref("rma_account.rma_operation_supplier_refund")
        cls.company_id = cls.env.user.company_id
        # Create partners
        customer1 = customer1_obj.create({"name": "Customer 1"})
        supplier1 = customer1_obj.create({"name": "Supplier 1"})

        # Create RMA group and operation:
        cls.rma_group_customer = cls.rma_obj.create(
            {"partner_id": customer1.id, "type": "customer"}
        )
        cls.rma_group_supplier = cls.rma_obj.create(
            {"partner_id": supplier1.id, "type": "supplier"}
        )
        cls.operation_1 = cls.rma_op_obj.create(
            {
                "code": "TEST",
                "name": "Refund and receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "refund_policy": "ordered",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )

        # Create products
        cls.product_1 = cls.product_obj.create(
            {
                "name": "Test Product 1",
                "type": "product",
                "list_price": 100.0,
                "rma_customer_operation_id": cls.cust_refund_op.id,
                "rma_supplier_operation_id": cls.sup_refund_op.id,
            }
        )
        cls.product_2 = cls.product_obj.create(
            {
                "name": "Test Product 2",
                "type": "product",
                "list_price": 150.0,
                "rma_customer_operation_id": cls.operation_1.id,
                "rma_supplier_operation_id": cls.sup_refund_op.id,
            }
        )
        cls.currency_id = cls.company_id.currency_id

        # Create Invoices:
        cls.customer_account = cls.acc_obj.search(
            [("user_type_id", "=", receivable_type.id)], limit=1
        ).id

        cls.invoices = cls.env["account.move"].create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": customer1.id,
                    "invoice_date": fields.Date.from_string("2016-01-01"),
                    "currency_id": cls.currency_id.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_1.id,
                                "product_uom_id": cls.product_1.uom_id.id,
                                "quantity": 3,
                                "price_unit": 1000,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_2.id,
                                "product_uom_id": cls.product_2.uom_id.id,
                                "quantity": 2,
                                "price_unit": 3000,
                            },
                        ),
                    ],
                },
                {
                    "move_type": "in_invoice",
                    "partner_id": supplier1.id,
                    "invoice_date": fields.Date.from_string("2016-01-01"),
                    "currency_id": cls.currency_id.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_1.id,
                                "product_uom_id": cls.product_1.uom_id.id,
                                "quantity": 3,
                                "price_unit": 1000,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_2.id,
                                "product_uom_id": cls.product_2.uom_id.id,
                                "quantity": 2,
                                "price_unit": 3000,
                            },
                        ),
                    ],
                },
            ]
        )
        cls.inv_customer = cls.invoices[0]
        cls.inv_supplier = cls.invoices[1]

    def test_01_add_from_invoice_customer(self):
        """Test wizard to create RMA from a customer invoice."""
        add_inv = self.rma_add_invoice_wiz.with_context(
            {
                "customer": True,
                "active_ids": self.rma_group_customer.id,
                "active_model": "rma.order",
            }
        ).create({"line_ids": [(6, 0, self.inv_customer.invoice_line_ids.ids)]})
        add_inv.add_lines()

        self.assertEqual(len(self.rma_group_customer.rma_line_ids), 2)
        for t in self.rma_group_supplier.rma_line_ids.mapped("type"):
            self.assertEqual(t, "customer")
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1
        )
        self.assertEqual(rma_1.operation_id, self.cust_refund_op)
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        self.assertEqual(rma_2.operation_id, self.operation_1)

    def test_02_add_from_invoice_supplier(self):
        """Test wizard to create RMA from a vendor bill."""
        add_inv = self.rma_add_invoice_wiz.with_context(
            {
                "supplier": True,
                "active_ids": self.rma_group_supplier.id,
                "active_model": "rma.order",
            }
        ).create({"line_ids": [(6, 0, self.inv_supplier.line_ids.ids)]})
        add_inv.add_lines()
        self.assertEqual(len(self.rma_group_supplier.rma_line_ids), 2)
        for t in self.rma_group_supplier.rma_line_ids.mapped("type"):
            self.assertEqual(t, "supplier")

    def test_03_rma_refund_operation(self):
        """Test RMA quantities using refund operations."""
        # Received refund_policy:
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1
        )
        self.assertEqual(rma_1.refund_policy, "received")
        self.assertEqual(rma_1.qty_to_refund, 0.0)
        # TODO: receive and check qty_to_refund is 12.0
        # Ordered refund_policy:
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        rma_2._onchange_operation_id()
        self.assertEqual(rma_2.refund_policy, "ordered")
        self.assertEqual(rma_2.qty_to_refund, 2.0)

    def test_04_rma_create_refund(self):
        """Generate a Refund from a customer RMA."""
        rma = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        rma.action_rma_to_approve()
        rma.action_rma_approve()
        self.assertEqual(rma.refund_count, 0)
        self.assertEqual(rma.qty_to_refund, 2.0)
        self.assertEqual(rma.qty_refunded, 0.0)
        make_refund = self.rma_refund_wiz.with_context(
            {"customer": True, "active_ids": rma.ids, "active_model": "rma.order.line"}
        ).create({"description": "Test refund"})
        make_refund.invoice_refund()
        rma.refund_line_ids.move_id.post()
        rma._compute_refund_count()
        self.assertEqual(rma.refund_count, 1)
        self.assertEqual(rma.qty_to_refund, 0.0)
        self.assertEqual(rma.qty_refunded, 2.0)

    def test_05_fill_rma_from_inv_line(self):
        """Test filling a RMA (line) from a invoice line."""
        rma = self.rma_line_obj.new(
            {
                "partner_id": self.inv_customer.partner_id.id,
                "account_move_line_id": self.inv_supplier.line_ids.ids[0],
            }
        )
        self.assertFalse(rma.product_id)
        rma._onchange_account_move_line_id()
        self.assertEqual(rma.product_id, self.product_1)
        self.assertEqual(rma.product_qty, 3.0)
