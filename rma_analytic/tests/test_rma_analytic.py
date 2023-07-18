# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.addons.rma.tests import test_rma


class TestRmaAnalytic(test_rma.TestRma):
    @classmethod
    def setUpClass(cls):
        super(TestRmaAnalytic, cls).setUpClass()
        cls.rma_add_invoice_wiz = cls.env["rma_add_invoice"]
        cls.rma_refund_wiz = cls.env["rma.refund"]
        products2move = [
            (cls.product_1, 3),
            (cls.product_2, 5),
            (cls.product_3, 2),
        ]
        cls.rma_add_invoice_wiz = cls.env["rma_add_invoice"]
        cls.rma_ana_id = cls._create_rma_from_move(
            products2move,
            "supplier",
            cls.env.ref("base.res_partner_2"),
            dropship=False,
        )
        receivable_type = cls.env.ref("account.data_account_type_receivable")
        # Create Invoices:
        customer_account = (
            cls.env["account.account"]
            .search([("user_type_id", "=", receivable_type.id)], limit=1)
            .id
        )
        cls.inv_customer = cls.env["account.invoice"].create(
            {
                "partner_id": cls.partner_id.id,
                "account_id": customer_account,
                "type": "out_invoice",
            }
        )
        cls.anal = cls.env["account.analytic.account"].create({"name": "Name"})
        cls.inv_line_1 = cls.env["account.invoice.line"].create(
            {
                "name": cls.partner_id.name,
                "product_id": cls.product_1.id,
                "quantity": 12.0,
                "price_unit": 100.0,
                "account_analytic_id": cls.anal.id,
                "invoice_id": cls.inv_customer.id,
                "uom_id": cls.product_1.uom_id.id,
                "account_id": customer_account,
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

    @classmethod
    def _create_rma_analytic(cls, products2move, partner):
        picking_in = cls._create_picking(partner)
        moves = []
        for item in products2move:
            move_values = cls._prepare_anal_move(
                item[0],
                item[1],
                cls.stock_location,
                cls.customer_location,
                picking_in,
                cls.analytic_1,
            )
            moves.append(cls.env["stock.move"].create(move_values))

        rma_id = cls.rma_model.create(
            {
                "reference": "0001",
                "type": "customer",
                "partner_id": partner.id,
                "company_id": cls.env.ref("base.main_company").id,
            }
        )
        for move in moves:
            wizard = cls.rma_add_stock_move.with_context(
                {
                    "stock_move_id": move.id,
                    "customer": True,
                    "active_ids": rma_id.id,
                    "active_model": "rma.order",
                }
            ).create({})
            data = wizard._prepare_rma_line_from_stock_move(move)
            wizard.add_lines()

            if move.product_id.rma_customer_operation_id:
                move.product_id.rma_customer_operation_id.in_route_id = False
            move.product_id.categ_id.rma_customer_operation_id = False
            move.product_id.rma_customer_operation_id = False
            wizard._prepare_rma_line_from_stock_move(move)
            cls.line = cls.rma_line_model.create(data)
        return rma_id

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
        rma_line = (
            self.env["rma.order.line"]
            .with_context(customer=True)
            .new(
                {
                    "partner_id": self.partner_id.id,
                    "product_id": self.product_1.id,
                    "operation_id": self.env.ref(
                        "rma.rma_operation_customer_replace"
                    ).id,
                    "in_route_id": self.env.ref("rma.route_rma_customer"),
                    "out_route_id": self.env.ref("rma.route_rma_customer"),
                    "in_warehouse_id": self.env.ref("stock.warehouse0"),
                    "out_warehouse_id": self.env.ref("stock.warehouse0"),
                    "location_id": self.env.ref("stock.stock_location_stock"),
                    "type": "customer",
                    "invoice_line_id": self.inv_line_1.id,
                    "uom_id": self.product_1.uom_id.id,
                }
            )
        )
        rma_line._onchange_invoice_line_id()
        self.assertEqual(
            rma_line.analytic_account_id,
            self.inv_line_1.account_analytic_id,
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
            {
                "customer": True,
                "active_ids": [rma_order.id],
                "active_model": "rma.order",
            }
        ).create({"invoice_line_ids": [(6, 0, self.inv_customer.invoice_line_ids.ids)]})
        add_inv.add_lines()

        self.assertEqual(
            rma_order.mapped("rma_line_ids.analytic_account_id"),
            self.inv_line_1.account_analytic_id,
        )

    def test_refund_analytic(self):
        self.product_1.rma_customer_operation_id = self.env.ref(
            "rma_account.rma_operation_customer_refund"
        ).id
        rma_line = (
            self.env["rma.order.line"]
            .with_context(customer=True)
            .create(
                {
                    "partner_id": self.partner_id.id,
                    "product_id": self.product_1.id,
                    "operation_id": self.env.ref(
                        "rma_account.rma_operation_customer_refund"
                    ).id,
                    "in_route_id": self.env.ref("rma.route_rma_customer").id,
                    "out_route_id": self.env.ref("rma.route_rma_customer").id,
                    "in_warehouse_id": self.env.ref("stock.warehouse0").id,
                    "out_warehouse_id": self.env.ref("stock.warehouse0").id,
                    "location_id": self.env.ref("stock.stock_location_stock").id,
                    "type": "customer",
                    "invoice_line_id": self.inv_line_1.id,
                    "delivery_policy": "no",
                    "receipt_policy": "ordered",
                    "uom_id": self.product_1.uom_id.id,
                }
            )
        )
        rma_line._onchange_invoice_line_id()
        rma_line.action_rma_to_approve()
        rma_line.action_rma_approve()
        make_refund = self.rma_refund_wiz.with_context(
            {
                "customer": True,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
            }
        ).create({"description": "Test refund"})
        make_refund.invoice_refund()
        self.assertEqual(
            rma_line.mapped("analytic_account_id"),
            rma_line.mapped("refund_line_ids.account_analytic_id"),
        )
