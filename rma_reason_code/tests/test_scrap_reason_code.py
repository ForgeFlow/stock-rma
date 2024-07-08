# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api
from odoo.exceptions import ValidationError
from odoo.tests import common


class RMAOrderLine(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(RMAOrderLine, cls).setUpClass()
        cls.user_admin = cls.env.ref("base.user_admin")
        cls.env = api.Environment(cls.cr, cls.user_admin.id, {})
        cls.user_admin.tz = False  # Make sure there's no timezone in user
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.location = cls.env.ref("rma.location_rma")
        cls.cust_location = cls.env.ref("stock.stock_location_customers")
        cls.vend_location = cls.env.ref("stock.stock_location_suppliers")
        cls.product = cls.env["product.product"].create(
            {
                "name": "TEST Product",
                "type": "product",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})

        cls.route = cls.env.ref("rma.route_rma_customer")

        cls.operation1 = cls.env["rma.operation"].create(
            {
                "code": "TEST1",
                "name": "Replace after receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "delivery_policy": "received",
                "in_route_id": cls.route.id,
                "out_route_id": cls.route.id,
                "location_id": cls.location.id,
                "in_warehouse_id": cls.warehouse.id,
                "out_warehouse_id": cls.warehouse.id,
            }
        )

        cls.operation2 = cls.env["rma.operation"].create(
            {
                "code": "TEST2",
                "name": "Refund after receive",
                "type": "supplier",
                "receipt_policy": "ordered",
                "delivery_policy": "no",
                "in_route_id": cls.route.id,
                "out_route_id": cls.route.id,
                "location_id": cls.location.id,
                "in_warehouse_id": cls.warehouse.id,
                "out_warehouse_id": cls.warehouse.id,
            }
        )

        cls.rma_line_1 = cls.env["rma.order.line"].create(
            {
                "partner_id": cls.partner.id,
                "requested_by": False,
                "assigned_to": False,
                "type": "customer",
                "product_id": cls.product.id,
                "uom_id": cls.product.uom_id.id,
                "product_qty": 1,
                "price_unit": 10,
                "operation_id": cls.operation1.id,
                "delivery_address_id": cls.partner.id,
                "receipt_policy": cls.operation1.receipt_policy,
                "delivery_policy": cls.operation1.delivery_policy,
                "in_warehouse_id": cls.operation1.in_warehouse_id.id,
                "out_warehouse_id": cls.operation1.out_warehouse_id.id,
                "in_route_id": cls.operation1.in_route_id.id,
                "out_route_id": cls.operation1.out_route_id.id,
                "location_id": cls.operation1.location_id.id,
            }
        )

        cls.rma_line_2 = cls.env["rma.order.line"].create(
            {
                "partner_id": cls.partner.id,
                "requested_by": False,
                "assigned_to": False,
                "type": "supplier",
                "product_id": cls.product.id,
                "uom_id": cls.product.uom_id.id,
                "product_qty": 1,
                "price_unit": 10,
                "operation_id": cls.operation2.id,
                "delivery_address_id": cls.partner.id,
                "receipt_policy": cls.operation2.receipt_policy,
                "delivery_policy": cls.operation2.delivery_policy,
                "in_warehouse_id": cls.operation2.in_warehouse_id.id,
                "out_warehouse_id": cls.operation2.out_warehouse_id.id,
                "in_route_id": cls.operation2.in_route_id.id,
                "out_route_id": cls.operation2.out_route_id.id,
                "location_id": cls.operation2.location_id.id,
            }
        )
        cls.env["rma.reason.code"].search([]).unlink()
        cls.reason_code_both = cls.env["rma.reason.code"].create(
            {
                "name": "Test Code 1",
                "description": "Test description",
                "type": "both",
            }
        )
        cls.reason_code_customer = cls.env["rma.reason.code"].create(
            {
                "name": "Test Code 2",
                "description": "Test description",
                "type": "customer",
            }
        )
        cls.reason_code_supplier = cls.env["rma.reason.code"].create(
            {
                "name": "Test Code 3",
                "description": "Test description",
                "type": "supplier",
            }
        )

    def test_01_reason_code_customer(self):
        self.rma_line_1.action_rma_to_approve()
        self.assertEqual(
            self.rma_line_1.allowed_reason_code_ids.ids,
            [self.reason_code_both.id, self.reason_code_customer.id],
        )
        with self.assertRaises(ValidationError):
            self.rma_line_1.write(
                {
                    "reason_code_ids": [self.reason_code_supplier.id],
                }
            )
        self.rma_line_1.write(
            {
                "reason_code_ids": [self.reason_code_customer.id],
            }
        )

    def test_02_reason_code_supplier(self):
        self.rma_line_2.action_rma_to_approve()
        self.assertEqual(
            self.rma_line_2.allowed_reason_code_ids.ids,
            [self.reason_code_both.id, self.reason_code_supplier.id],
        )
        with self.assertRaises(ValidationError):
            self.rma_line_2.write(
                {
                    "reason_code_ids": [self.reason_code_customer.id],
                }
            )
        self.rma_line_2.write(
            {
                "reason_code_ids": [self.reason_code_supplier.id],
            }
        )
