# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaDelivery(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_delivery_normal = cls.env["product.product"].create(
            {
                "name": "Normal Delivery Charges",
                "type": "service",
                "list_price": 10.0,
                "categ_id": cls.env.ref("delivery.product_category_deliveries").id,
            }
        )
        cls.carrier_id = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "fixed_price": 10,
                "delivery_type": "fixed",
                "product_id": cls.product_delivery_normal.id,
            }
        )
        cls.rma_cust_replace_op_id.write(
            {
                "default_carrier_id": cls.carrier_id.id,
            }
        )

    def test_rma_delivery(self):
        self.rma_customer_id.rma_line_ids.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            active_ids=self.rma_customer_id.rma_line_ids.ids,
            active_model="rma.order.line",
            picking_type="incoming",
            active_id=self.rma_customer_id.rma_line_ids.ids[0],
        ).create({})
        wizard._create_picking()
        res = self.rma_customer_id.rma_line_ids.action_view_in_shipments()
        picking = self.env["stock.picking"].browse(res["res_id"])
        picking.action_assign()
        for mv in picking.move_ids:
            mv.quantity_done = mv.product_uom_qty
        picking._action_done()
        wizard = self.rma_make_picking.with_context(
            active_id=self.rma_customer_id.rma_line_ids.ids[0],
            active_ids=self.rma_customer_id.rma_line_ids.ids,
            active_model="rma.order.line",
            picking_type="outgoing",
        ).create({})
        wizard._create_picking()
        res = self.rma_customer_id.rma_line_ids.action_view_out_shipments()
        picking = self.env["stock.picking"].browse(res["res_id"])
        self.assertEqual(self.carrier_id.ids, picking.carrier_id.ids)
