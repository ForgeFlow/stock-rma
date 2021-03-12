# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields
from odoo.tests import common


class TestRmaRepair(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestRmaRepair, cls).setUpClass()

        cls.rma_obj = cls.env["rma.order"]
        cls.rma_line_obj = cls.env["rma.order.line"]
        cls.rma_op = cls.env["rma.operation"]
        cls.rma_add_invoice_wiz = cls.env["rma_add_account_move"]
        cls.rma_make_repair_wiz = cls.env["rma.order.line.make.repair"]
        cls.repair_line_obj = cls.env["repair.line"]
        cls.acc_obj = cls.env["account.account"]
        cls.inv_obj = cls.env["account.move"]
        cls.invl_obj = cls.env["account.move.line"]
        cls.product_obj = cls.env["product.product"]
        cls.partner_obj = cls.env["res.partner"]
        cls.acc_bank_stmt_model = cls.env["account.bank.statement"]
        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")

        # Create partners
        cls.customer1 = cls.partner_obj.create({"name": "Customer 1"})

        # Create RMA group and operation:
        cls.rma_group_customer = cls.rma_obj.create(
            {"partner_id": cls.customer1.id, "type": "customer"}
        )
        cls.operation_1 = cls.rma_op.create(
            {
                "code": "TEST",
                "name": "Repair afer receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "repair_type": "received",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )
        cls.operation_2 = cls.rma_op.create(
            {
                "code": "TEST",
                "name": "Repair on order",
                "type": "customer",
                "receipt_policy": "ordered",
                "repair_type": "ordered",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )
        cls.operation_3 = cls.rma_op.create(
            {
                "code": "TEST",
                "name": "Deliver after repair",
                "type": "customer",
                "receipt_policy": "ordered",
                "repair_type": "ordered",
                "delivery_policy": "repair",
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
                "rma_customer_operation_id": cls.operation_1.id,
            }
        )
        cls.product_2 = cls.product_obj.create(
            {
                "name": "Test Product 2",
                "type": "product",
                "list_price": 150.0,
                "rma_customer_operation_id": cls.operation_2.id,
            }
        )
        cls.product_3 = cls.product_obj.create(
            {
                "name": "Test Product 3",
                "type": "product",
                "list_price": 1.0,
                "rma_customer_operation_id": cls.operation_3.id,
            }
        )
        # Create Invoices:

        cls.company_id = cls.env.user.company_id
        cls.currency_id = cls.company_id.currency_id

        cls.inv_customer = cls.env["account.move"].create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": cls.customer1.id,
                    "invoice_date": fields.Date.from_string("2016-01-01"),
                    "currency_id": cls.currency_id.id,
                    "invoice_line_ids": [
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_1.id,
                                "product_uom_id": cls.product_1.uom_id.id,
                                "quantity": 12,
                                "price_unit": 1000,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_2.id,
                                "product_uom_id": cls.product_2.uom_id.id,
                                "quantity": 15.0,
                                "price_unit": 150.0,
                            },
                        ),
                        (
                            0,
                            None,
                            {
                                "product_id": cls.product_3.id,
                                "product_uom_id": cls.product_3.uom_id.id,
                                "quantity": 1,
                                "price_unit": 1000,
                            },
                        ),
                    ],
                }
            ]
        )

        cls.inv_line_1 = cls.inv_customer.invoice_line_ids[0]
        cls.inv_line_2 = cls.inv_customer.invoice_line_ids[1]
        cls.inv_line_3 = cls.inv_customer.invoice_line_ids[2]

        cls.rma_group_customer_2 = cls.rma_obj.create(
            {"partner_id": cls.customer1.id, "type": "customer"}
        )
        cls.bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        cls.material = cls.product_obj.create({"name": "Materials", "type": "product"})

        cls.material.product_tmpl_id.standard_price = 10
        cls.stock_location = cls.env.ref("stock.stock_location_stock")

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
        self.assertEqual(len(self.rma_group_customer.rma_line_ids), 3)
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1
        )
        rma_1.repair_type = self.operation_1.repair_type
        self.assertEquals(
            rma_1.operation_id, self.operation_1, "Operation should be operation_1"
        )
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        rma_2.repair_type = self.operation_2.repair_type
        self.assertEquals(
            rma_2.operation_id, self.operation_2, "Operation should be operation_2"
        )

    def test_02_rma_repair_operation(self):
        """Test RMA quantities using repair operations."""
        # Received repair_type:
        rma_1 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1
        )
        self.assertEquals(
            rma_1.operation_id.repair_type, "received", "Incorrect Repair operation"
        )
        self.assertEquals(rma_1.qty_to_repair, 0.0, "Quantity to repair should be 0.0")
        # Ordered repair_type:
        rma_2 = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        self.assertEquals(
            rma_2.operation_id.repair_type, "ordered", "Incorrect Repair operation"
        )
        self.assertEqual(rma_2.qty_to_repair, 15.0)

    def test_03_create_repair_order(self):
        """Generate a Repair Order from a customer RMA."""
        rma = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_2
        )
        rma.action_rma_to_approve()
        rma.action_rma_approve()
        self.assertEqual(rma.repair_count, 0)
        self.assertEqual(rma.qty_to_repair, 15.0)
        self.assertEqual(rma.qty_repaired, 0.0)
        make_repair = self.rma_make_repair_wiz.with_context(
            {"customer": True, "active_ids": rma.ids, "active_model": "rma.order.line"}
        ).new()
        make_repair.make_repair_order()
        rma.repair_ids.action_repair_confirm()
        self.assertEqual(rma.repair_count, 1)
        self.assertEqual(rma.qty_to_repair, 0.0)
        self.assertEqual(rma.qty_repaired, 0.0)
        self.assertEqual(rma.qty_under_repair, 15.0)

    def test_04_deliver_after_repair(self):
        """Only deliver after repair"""
        add_inv = self.rma_add_invoice_wiz.with_context(
            {
                "customer": True,
                "active_ids": self.rma_group_customer_2.id,
                "active_model": "rma.order",
            }
        ).create({"line_ids": [(6, 0, self.inv_customer.invoice_line_ids.ids)]})
        add_inv.add_lines()
        rma = self.rma_group_customer_2.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_3
        )
        rma.operation_id = self.operation_3.id
        rma._onchange_operation_id()
        rma.action_rma_to_approve()
        rma.action_rma_approve()
        self.assertEqual(rma.qty_to_deliver, 0.0)
        make_repair = self.rma_make_repair_wiz.with_context(
            {"customer": True, "active_ids": rma.ids, "active_model": "rma.order.line"}
        ).new()
        make_repair.make_repair_order()
        repair = rma.repair_ids
        line = self.repair_line_obj.create(
            {
                "name": "consume stuff to repair",
                "repair_id": repair.id,
                "type": "add",
                "product_id": self.material.id,
                "product_uom": self.material.uom_id.id,
                "product_uom_qty": 1.0,
                "location_id": self.stock_location.id,
                "location_dest_id": self.stock_location.id,
                "price_unit": 10.0,
            }
        )
        line.onchange_product_id()
        repair.invoice_method = "after_repair"
        repair.action_repair_confirm()
        repair.action_repair_start()
        repair.action_repair_end()
        repair.action_repair_invoice_create()
        self.assertEqual(rma.qty_repaired, 1.0)
        self.assertEqual(rma.qty_to_deliver, 1.0)
        repair.invoice_id.post()
        repair.invoice_id.action_register_payment()
        self.assertEqual(repair.invoice_status, "posted")
        self.assertEqual(rma.qty_to_pay, 0.0)
        self.assertEqual(rma.qty_repaired, 1.0)
        self.assertEqual(rma.delivery_policy, "repair")
        self.assertEqual(rma.qty_delivered, 0.0)
