# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)


from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaAccountUnreconciled(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rma_refund_wiz = cls.env["rma.refund"]
        cls.g_account_manager = cls.env.ref("account.group_account_manager")
        cls.rma_manager_user_account = cls._create_user(
            "rma manager account",
            [cls.g_stock_manager, cls.g_rma_manager, cls.g_account_manager],
            cls.company,
        )
        for categ in cls.rma_customer_id.with_user(cls.rma_manager_user_account).mapped(
            "rma_line_ids.product_id.categ_id"
        ):
            categ.write(
                {
                    "property_valuation": "real_time",
                    "property_cost_method": "fifo",
                }
            )
            categ.property_stock_account_input_categ_id.write(
                {
                    "reconcile": True,
                }
            )
            categ.property_stock_account_output_categ_id.write(
                {
                    "reconcile": True,
                }
            )
        for product in cls.rma_customer_id.with_user(
            cls.rma_manager_user_account
        ).mapped("rma_line_ids.product_id"):
            product.write(
                {
                    "standard_price": 10.0,
                }
            )

    def test_unreconciled_moves(self):
        for rma_line in self.rma_customer_id.rma_line_ids:
            rma_line.write(
                {
                    "refund_policy": "received",
                }
            )
            rma_line.action_rma_approve()
            self.assertFalse(rma_line.unreconciled)
        self.rma_customer_id.rma_line_ids.action_rma_to_approve()
        wizard = self.rma_make_picking.with_context(
            {
                "active_ids": self.rma_customer_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
                "picking_type": "incoming",
                "active_id": 1,
            }
        ).create({})
        wizard._create_picking()
        res = self.rma_customer_id.rma_line_ids.action_view_in_shipments()
        picking = self.env["stock.picking"].browse(res["res_id"])
        picking.action_assign()
        for mv in picking.move_lines:
            mv.quantity_done = mv.product_uom_qty
        picking.button_validate()
        for rma_line in self.rma_customer_id.rma_line_ids:
            rma_line._compute_unreconciled()
            self.assertTrue(rma_line.unreconciled)
        make_refund = self.rma_refund_wiz.with_context(
            {
                "customer": True,
                "active_ids": self.rma_customer_id.rma_line_ids.ids,
                "active_model": "rma.order.line",
            }
        ).create(
            {
                "description": "Test refund",
            }
        )
        for item in make_refund.item_ids:
            item.write(
                {
                    "qty_to_refund": item.product_qty,
                }
            )
        make_refund.invoice_refund()
        self.rma_customer_id.with_user(
            self.rma_manager_user_account
        ).rma_line_ids.refund_line_ids.move_id.filtered(
            lambda x: x.state != "posted"
        ).action_post()
        for rma_line in self.rma_customer_id.rma_line_ids:
            rma_line._compute_unreconciled()
            self.assertTrue(rma_line.unreconciled)

        self.assertEqual(
            self.env["rma.order.line"].search_count(
                [
                    ("type", "=", "customer"),
                    ("unreconciled", "=", True),
                    ("rma_id", "=", self.rma_customer_id.id),
                ]
            ),
            3,
        )
        for rma_line in self.rma_customer_id.rma_line_ids:
            aml_domain = rma_line.sudo().action_view_unreconciled().get("domain")
            aml_lines = (
                aml_domain and self.env["account.move.line"].search(aml_domain) or False
            )
            if aml_lines:
                aml_lines.reconcile()
            rma_line._compute_unreconciled()
            self.assertFalse(rma_line.unreconciled)
