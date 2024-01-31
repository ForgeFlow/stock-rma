from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaSaleTracking(TestRma):
    @classmethod
    def setUpClass(cls):
        super(TestRmaSaleTracking, cls).setUpClass()
        cls.rma_obj = cls.env["rma.order"]
        cls.rma_line_obj = cls.env["rma.order.line"]
        cls.rma_op_obj = cls.env["rma.operation"]
        cls.rma_add_sale_wiz = cls.env["rma_add_sale"]
        cls.rma_make_sale_wiz = cls.env["rma.order.line.make.sale.order"]
        cls.so_obj = cls.env["sale.order"]
        cls.sol_obj = cls.env["sale.order.line"]
        cls.product_obj = cls.env["product.product"]
        cls.partner_obj = cls.env["res.partner"]
        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")
        cls.customer1 = cls.partner_obj.create({"name": "Customer 1"})
        cls.product_lot_2 = cls._create_product("PT2 Lot", "lot")
        cls.product_serial_2 = cls._create_product("PT2 Serial", "serial")

        cls.so = cls.so_obj.create(
            {
                "partner_id": cls.customer1.id,
                "partner_invoice_id": cls.customer1.id,
                "partner_shipping_id": cls.customer1.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": cls.product_serial_2.name,
                            "product_id": cls.product_serial_2.id,
                            "product_uom_qty": 1.0,
                            "product_uom": cls.product_serial_2.uom_id.id,
                            "price_unit": cls.product_serial_2.list_price,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": cls.product_lot_2.name,
                            "product_id": cls.product_lot_2.id,
                            "product_uom_qty": 18.0,
                            "product_uom": cls.product_lot_2.uom_id.id,
                            "price_unit": cls.product_lot_2.list_price,
                        },
                    ),
                ],
                "pricelist_id": cls.env.ref("product.list0").id,
            }
        )
        cls.so.action_confirm()

        cls.serial = cls.lot_obj.create(
            {
                "product_id": cls.product_serial_2.id,
            }
        )
        cls.lot = cls.lot_obj.create(
            {
                "product_id": cls.product_lot_2.id,
            }
        )

        cls.package_1 = cls.package_obj.create({})
        cls.package_2 = cls.package_obj.create({})
        cls.package_3 = cls.package_obj.create({})
        cls.package_4 = cls.package_obj.create({})

        cls._create_inventory(
            cls.product_serial_2, 1, cls.stock_location, cls.serial.id, cls.package_1.id
        )

        cls._create_inventory(
            cls.product_lot_2, 1, cls.stock_location, cls.lot.id, cls.package_3.id
        )

        picking = cls.so.picking_ids

        picking.action_assign()

        for move in picking.move_lines:
            if move.product_id.id == cls.product_serial_2.id:
                move.move_line_ids.write({"result_package_id": cls.package_2.id})
            if move.product_id.id == cls.product_lot_2.id:
                move.move_line_ids.write({"result_package_id": cls.package_4.id})

        cls._do_picking(picking)

        # Create RMA group and operation:
        cls.rma_group = cls.rma_obj.create({"partner_id": cls.customer1.id})
        cls.operation_1 = cls.rma_op_obj.create(
            {
                "code": "TEST",
                "name": "Sale afer receive",
                "type": "customer",
                "receipt_policy": "ordered",
                "sale_policy": "received",
                "in_route_id": cls.rma_route_cust.id,
                "out_route_id": cls.rma_route_cust.id,
            }
        )

        add_sale = cls.rma_add_sale_wiz.with_context(
            {
                "customer": True,
                "active_ids": cls.rma_group.id,
                "active_model": "rma.order",
            }
        ).create(
            {"sale_id": cls.so.id, "sale_line_ids": [(6, 0, cls.so.order_line.ids)]}
        )
        add_sale.add_lines()

    def test_01_customer_rma_tracking(self):
        rma_serial = self.rma_group.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_serial_2
        )
        rma_lot = self.rma_group.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_lot_2
        )
        for rma in rma_serial + rma_lot:
            wizard = self.rma_make_picking.with_context(
                {
                    "active_ids": rma.ids,
                    "active_model": "rma.order.line",
                    "picking_type": "incoming",
                    "active_id": rma.ids[0],
                }
            ).create({})
            wizard.action_create_picking()
            res = rma.action_view_in_shipments()
            self.assertTrue("res_id" in res, "Incorrect number of pickings" "created")
            picking = self.env["stock.picking"].browse(res["res_id"])
            self.assertEqual(len(picking), 1, "Incorrect number of pickings created")
            moves = picking.move_lines
            self.asserTrue(
                bool(moves.mapped("move_line_ids.package_id")),
                "Should have same package assigned",
            )
            self.assertFalse(
                bool(moves.mapped("move_line_ids.result_package_id")),
                "Destination package should not be assigned",
            )
            picking.action_assign()
            for mv in picking.move_lines:
                mv.quantity_done = mv.product_uom_qty
            picking._action_done()
            self.assertEqual(
                picking.state, "done", "Final picking should has done state"
            )
