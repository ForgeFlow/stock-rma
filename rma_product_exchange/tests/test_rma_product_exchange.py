# Copyright 2024 Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaProductExchange(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_customer_rma_with_product_exchange(self):
        self.rma_cust_replace_op_id.product_exchange = True
        self.rma_customer_id.rma_line_ids.delivery_policy = "ordered"
        self.rma_customer_id.rma_line_ids[0].new_product_id = self.product_id
        self.rma_customer_id.rma_line_ids.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_ids": self.rma_customer_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "outgoing",
                "active_id": 1,
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_customer_id.action_view_out_shipments()
        picking = self.env["stock.picking"].browse(res["res_id"])
        self.assertEqual(picking.move_ids[0].product_id, self.product_id)
