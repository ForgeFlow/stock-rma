# Copyright (C) 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.rma_account.tests.test_account_move_line_rma_order_line import (
    TestAccountMoveLineRmaOrderLine,
)


class TestRmaStockAccountSale(TestAccountMoveLineRmaOrderLine):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.operation_receive_refund = cls.env.ref(
            "rma_account.rma_operation_customer_refund"
        )
        cls.product_test_refund = cls.env["product.product"].create(
            {"name": "Test Refund"}
        )
        cls.refund_reason = cls.env["account.move.refund.reason"].create(
            {"name": "Rma Refund"}
        )

    def test_rma_refund_reason(self):
        products2move = [
            (self.product_test_refund, 1),
        ]
        rma = self._create_rma(products2move, self.partner1)
        rma_line = rma.rma_line_ids
        rma_line.operation_id = self.operation_receive_refund
        rma_line.refund_reason_id = self.refund_reason
        for rma in rma_line:
            if rma.price_unit == 0:
                rma.price_unit = 100.0
        rma_line.action_rma_approve()
        wizard = self.rma_make_picking.with_context(
            **{
                "active_id": 1,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
            }
        ).create({})
        operation = self.env["rma.operation"].search(
            [("type", "=", "customer"), ("refund_policy", "=", "received")], limit=1
        )
        rma_line.write({"operation_id": operation.id})
        rma_line.write({"refund_policy": "received"})

        wizard._create_picking()
        res = rma_line.action_view_in_shipments()
        if "res_id" in res:
            picking = self.env["stock.picking"].browse(res["res_id"])
        else:
            picking_ids = self.env["stock.picking"].search(res["domain"])
            picking = self.env["stock.picking"].browse(picking_ids)
        picking.button_validate()
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
            }
        ).create({})
        self.assertEqual(make_refund.refund_reason_id, self.refund_reason)
        for item in make_refund.item_ids:
            item.write(
                {
                    "qty_to_refund": 1.0,
                }
            )
        make_refund.invoice_refund()
        refund_invoice = rma_line.mapped("refund_line_ids.move_id")
        self.assertEqual(refund_invoice.reason_id, self.refund_reason)
