from odoo.tests import common


class TestRmaPutAway(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestRmaPutAway, cls).setUpClass()

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
                "name": "WH Put Away Location",
                "location_id": cls.wh.view_location_id.id,
            }
        )

        cls.route1 = cls.env["stock.route"].create(
            {
                "name": "Transfer WH1",
                "rma_selectable": True,
                "sequence": 10,
            }
        )

        cls.env["stock.rule"].create(
            {
                "name": "Transfer",
                "route_id": cls.route1.id,
                "location_src_id": cls.stock_rma_location.id,
                "location_dest_id": cls.put_away_loc.id,
                "action": "pull",
                "picking_type_id": cls.wh.int_type_id.id,
                "procure_method": "make_to_stock",
                "warehouse_id": cls.wh.id,
            }
        )

        # Create RMA group and operation:
        cls.rma_group = cls.rma_obj.create({"partner_id": cls.customer1.id})

        cls.operation_1 = cls.rma_op_obj.create(
            {
                "code": "TEST1",
                "name": "Operation 1",
                "type": "customer",
                "receipt_policy": "ordered",
                "put_away_policy": "received",
                "put_away_route_id": cls.route1.id,
                "put_away_location_id": cls.put_away_loc.id,
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )
        cls.operation_2 = cls.rma_op_obj.create(
            {
                "code": "TEST2",
                "name": "Operation 2",
                "type": "customer",
                "receipt_policy": "ordered",
                "put_away_policy": "ordered",
                "put_away_route_id": cls.route1.id,
                "put_away_location_id": cls.put_away_loc.id,
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )

    def test_01_rma_put_away_without_lot(self):
        """Generate a Sales Order from a customer RMA."""
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
                        "location_id": rma.location_id,
                        "qty_to_put_away": rma.qty_to_put_away,
                        "uom_id": rma.uom_id.id,
                    },
                ],
            }
        ).create({})
        action = wizard.action_create_put_away()
        picking = self.env["stock.picking"].browse([action["res_id"]])
        self.assertEqual(picking.location_dest_id.id, self.put_away_loc.id)
        self.assertEqual(picking.location_id.id, self.stock_rma_location.id)
        move = picking.move_ids_without_package
        self.assertEqual(move.product_id.id, self.product_1.id)
        self.assertEqual(move.product_uom_qty, 1)
        move.quantity_done = 1
        self.assertTrue(picking.action_assign())
        self.assertTrue(picking.button_validate())

    def test_02_rma_put_away_with_lot(self):
        rma = self.rma_line_obj.create(
            {
                "partner_id": self.customer1.id,
                "product_id": self.product_2.id,
                "lot_id": self.lot.id,
                "operation_id": self.operation_1.id,
                "uom_id": self.product_2.uom_id.id,
                "in_route_id": self.operation_1.in_route_id.id,
                "out_route_id": self.operation_1.out_route_id.id,
                "in_warehouse_id": self.operation_1.in_warehouse_id.id,
                "out_warehouse_id": self.operation_1.out_warehouse_id.id,
                "location_id": self.stock_rma_location.id,
            }
        )
        rma._onchange_operation_id()
        rma._onchange_lot_id()
        rma.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": rma.id,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        wizard.action_create_picking()
        res = rma.action_view_in_shipments()
        picking = self.env["stock.picking"].browse(res["res_id"])
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity_done = mv.product_uom_qty
        picking._action_done()
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
                        "lot_id": rma.lot_id.id,
                        "location_id": rma.location_id,
                        "qty_to_put_away": rma.qty_to_put_away,
                        "uom_id": rma.uom_id.id,
                    },
                ],
            }
        ).create({})
        action = wizard.action_create_put_away()
        picking = self.env["stock.picking"].browse([action["res_id"]])
        picking.action_assign()
        self.assertEqual(picking.location_dest_id.id, self.put_away_loc.id)
        self.assertEqual(picking.location_id.id, self.stock_rma_location.id)
        move = picking.move_ids_without_package
        self.assertEqual(move.product_id.id, self.product_2.id)
        self.assertEqual(move.product_uom_qty, 1)
        self.assertEqual(move.move_line_ids.lot_id.id, self.lot.id)
        move.quantity_done = 1
        move.move_line_ids.lot_id = self.lot
        self.assertTrue(picking.button_validate())
