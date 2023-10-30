# Copyright 2017-23 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields
from odoo.tests import Form

from odoo.addons.rma.tests import test_rma


class TestRmaAnalytic(test_rma.TestRma):
    @classmethod
    def setUpClass(cls):
        super(TestRmaAnalytic, cls).setUpClass()
        cls.rma_add_invoice_wiz = cls.env["rma_add_account_move"]
        cls.rma_refund_wiz = cls.env["rma.refund"]
        cls.rma_obj = cls.env["rma.order"]
        cls.rma_op_obj = cls.env["rma.operation"]
        cls.rma_route_cust = cls.env.ref("rma.route_rma_customer")
        cls.cust_refund_op = cls.env.ref("rma_account.rma_operation_customer_refund")
        cls.rma_group_customer = cls.rma_obj.create(
            {"partner_id": cls.partner_id.id, "type": "customer"}
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
        cls.product_1.update(
            {
                "rma_customer_operation_id": cls.operation_1.id,
                "rma_supplier_operation_id": cls.cust_refund_op.id,
            }
        )
        products2move = [
            (cls.product_1, 3),
            (cls.product_2, 5),
            (cls.product_3, 2),
        ]
        cls.rma_ana_id = cls._create_rma_from_move(
            products2move,
            "supplier",
            cls.env.ref("base.res_partner_2"),
            dropship=False,
        )
        cls.company_id = cls.env.user.company_id
        cls.anal = cls.env["account.analytic.account"].create({"name": "Name"})
        cls.inv_customer = cls.env["account.move"].create(
            {
                "partner_id": cls.partner_id.id,
                "move_type": "out_invoice",
                "invoice_date": fields.Date.from_string("2023-01-01"),
                "currency_id": cls.company_id.currency_id,
                "invoice_line_ids": [
                    (
                        0,
                        None,
                        {
                            "name": cls.partner_id.name,
                            "product_id": cls.product_1.id,
                            "product_uom_id": cls.product_1.uom_id.id,
                            "quantity": 12.0,
                            "price_unit": 100.0,
                            "analytic_account_id": cls.anal.id,
                        },
                    ),
                ],
            }
        )

    @classmethod
    def _prepare_move(cls, product, qty, src, dest, picking_in):
        res = super(TestRmaAnalytic, cls)._prepare_move(
            product, qty, src, dest, picking_in
        )
        analytic_1 = cls.env["account.analytic.account"].create(
            {"name": "Test account #1"}
        )
        res.update({"analytic_account_id": analytic_1.id})
        return res

    def test_analytic(self):
        for line in self.rma_ana_id.rma_line_ids:
            for move in line.move_ids:
                self.assertEqual(
                    line.analytic_account_id,
                    move.analytic_account_id,
                    "the analytic account is not propagated",
                )

    def test_invoice_analytic(self):
        """Test wizard to create RMA from a customer invoice."""
        rma_line_form = Form(self.env["rma.order.line"].with_context(customer=True))
        rma_line_form.partner_id = self.partner_id
        rma_line_form.product_id = self.product_1
        rma_line_form.operation_id = self.env.ref("rma.rma_operation_customer_replace")
        rma_line_form.in_route_id = self.env.ref("rma.route_rma_customer")
        rma_line_form.out_route_id = self.env.ref("rma.route_rma_customer")
        rma_line_form.in_warehouse_id = self.env.ref("stock.warehouse0")
        rma_line_form.out_warehouse_id = self.env.ref("stock.warehouse0")
        rma_line_form.location_id = self.env.ref("stock.stock_location_stock")
        rma_line_form.account_move_line_id = self.inv_customer.invoice_line_ids[0]
        rma_line_form.uom_id = self.product_1.uom_id
        rma_line = rma_line_form.save()
        self.assertEqual(
            rma_line.analytic_account_id,
            self.inv_customer.invoice_line_ids[0].analytic_account_id,
        )

    def test_invoice_analytic02(self):
        self.product_1.rma_customer_operation_id = self.env.ref(
            "rma.rma_operation_customer_replace"
        ).id
        rma_order = (
            self.env["rma.order"]
            .with_context(customer=True)
            .create(
                {
                    "name": "RMA",
                    "partner_id": self.partner_id.id,
                    "type": "customer",
                    "rma_line_ids": [],
                }
            )
        )
        add_inv = self.rma_add_invoice_wiz.with_context(
            customer=True,
            active_ids=[rma_order.id],
            active_model="rma.order",
        ).create({"line_ids": [(6, 0, self.inv_customer.invoice_line_ids.ids)]})
        add_inv.add_lines()

        self.assertEqual(
            rma_order.mapped("rma_line_ids.analytic_account_id"),
            self.inv_customer.invoice_line_ids[0].analytic_account_id,
        )

    def test_refund_analytic(self):
        add_inv = self.rma_add_invoice_wiz.with_context(
            customer=True,
            active_ids=[self.rma_group_customer.id],
            active_model="rma.order",
        ).create({"line_ids": [(6, 0, self.inv_customer.invoice_line_ids.ids)]})
        add_inv.add_lines()
        rma_line = self.rma_group_customer.rma_line_ids.filtered(
            lambda r: r.product_id == self.product_1
        )
        rma_line._onchange_account_move_line_id()
        rma_line.action_rma_to_approve()
        rma_line.action_rma_approve()
        make_refund = self.rma_refund_wiz.with_context(
            customer=True,
            active_ids=rma_line.ids,
            active_model="rma.order.line",
        ).create({"description": "Test refund"})
        make_refund.invoice_refund()
        self.assertEqual(
            rma_line.mapped("analytic_account_id"),
            rma_line.mapped("refund_line_ids.analytic_account_id"),
        )
