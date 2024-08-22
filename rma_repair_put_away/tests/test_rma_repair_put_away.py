# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import common


class TestRmaRepairPutAway(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestRmaRepairPutAway, cls).setUpClass()

        cls.rma_obj = cls.env["rma.order"]
        cls.rma_make_picking = cls.env["rma_make_picking.wizard"]
        cls.rma_line_obj = cls.env["rma.order.line"]
        cls.rma_op_obj = cls.env["rma.operation"]
        cls.rma_make_put_away_wiz = cls.env["rma_make_put_away.wizard"]
        cls.product_obj = cls.env["product.product"]
        cls.partner_obj = cls.env["res.partner"]

        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")
        cls.cust_loc = cls.env.ref("stock.stock_location_customers")

        # Create customer
        cls.customer1 = cls.partner_obj.create({"name": "Customer 1"})

        # Create products
        cls.product_1 = cls.product_obj.create(
            {"name": "Test Product 1", "type": "product", "list_price": 100.0}
        )
        cls.product_2 = cls.product_obj.create(
            {
                "name": "Test Product 2",
                "type": "product",
                "list_price": 150.0,
                "tracking": "lot",
            }
        )

        cls.lot = cls.env["stock.lot"].create(
            {
                "name": "Lot for tests",
                "product_id": cls.product_2.id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.stock_rma_location = cls.wh.lot_rma_id

        cls.put_away_loc = cls.env["stock.location"].create(
            {
                "name": "WH Repair Location",
                "location_id": cls.wh.view_location_id.id,
            }
        )
        # define the push rule for the putaway
        cls.repair_route = cls.env["stock.route"].create(
            {
                "name": "Transfer RMA to Repair",
                "rma_selectable": True,
                "sequence": 10,
            }
        )
        cls.env["stock.rule"].create(
            {
                "name": "Transfer",
                "route_id": cls.repair_route.id,
                "location_src_id": cls.stock_rma_location.id,
                "location_dest_id": cls.put_away_loc.id,
                "action": "pull",
                "picking_type_id": cls.wh.int_type_id.id,
                "warehouse_id": cls.wh.id,
                "procure_method": "make_to_stock",
            }
        )

        cls.rma_group = cls.rma_obj.create({"partner_id": cls.customer1.id})

        cls.operation_1 = cls.rma_op_obj.create(
            {
                "code": "TEST",
                "name": "Repair afer receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "repair_type": "received",
                "put_away_policy": "received",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
                "repair_location_id": cls.stock_rma_location.id,
                "repair_route_id": cls.repair_route.id,
                "put_away_route_id": cls.repair_route.id,
                "put_away_location_id": cls.put_away_loc.id,
            }
        )

    def test_01_rma_repair_put_away(self):
        """Check the putaway repair transfers are seen and counted
        in the RMA"""
        rma = self.rma_line_obj.create(
            {
                "partner_id": self.customer1.id,
                "product_id": self.product_1.id,
                "operation_id": self.operation_1.id,
                "uom_id": self.product_1.uom_id.id,
                "in_route_id": self.operation_1.in_route_id.id,
                "out_route_id": self.operation_1.out_route_id.id,
                "in_warehouse_id": self.operation_1.in_warehouse_id.id,
                "out_warehouse_id": self.operation_1.out_warehouse_id.id,
                "location_id": self.stock_rma_location.id,
            }
        )
        rma._onchange_operation_id()
        rma.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": rma.id,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        wizard._create_picking()
        wizard = self.rma_make_put_away_wiz.with_context(
            **{
                "active_ids": rma.id,
                "active_model": "rma.order.line",
                "item_ids": [
                    0,
                    0,
                    {
                        "line_id": rma.id,
                        "product_id": rma.product_id.id,
                        "product_qty": rma.product_qty,
                        "location_id": self.put_away_loc.id,
                        "qty_to_put_away": rma.qty_to_put_away,
                        "uom_id": rma.uom_id.id,
                    },
                ],
            }
        ).create({})
        action = wizard.action_create_put_away()
        picking_id = action["res_id"]
        action_view_repair = rma.action_view_repair_transfers()
        self.assertEqual(action_view_repair["res_id"], picking_id)
        self.assertEqual(rma.repair_transfer_count, 1)
