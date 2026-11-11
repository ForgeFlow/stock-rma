# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import Form, tagged

from odoo.addons.rma.tests.test_rma import TestRma


@tagged("post_install", "-at_install")
class TestRmaStockAccount(TestRma):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account_model = cls.env["account.account"]
        cls.g_account_user = cls.env.ref("account.group_account_user")
        cls.rma_refund_wiz = cls.env["rma.refund"]
        cls.customer = cls.env["res.partner"].create({"name": "RMA test customer"})
        # we create new products to ensure previous layers do not affect when
        # running FIFO
        cls.product_fifo_1 = cls._create_product("product_fifo1")
        cls.product_fifo_2 = cls._create_product("product_fifo2")
        cls.product_fifo_3 = cls._create_product("product_fifo3")
        # Refs
        cls.rma_operation_customer_refund_id = cls.env.ref(
            "rma_account.rma_operation_customer_refund"
        )
        cls.rma_basic_user.write({"group_ids": [(4, cls.g_account_user.id)]})
        cls.customer_route = cls.env.ref("rma.route_rma_customer")
        cls.input_location = cls.env.ref("stock.stock_location_company")
        cls.output_location = cls.env.ref("stock.stock_location_output")
        # The product category created in the base module is not automated valuation
        # we have to create a new category here
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(
            "asset_current", name, code, cls.company, False
        )
        product_ctg = cls.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_valuation": "real_time",
                "rma_approval_policy": "one_step",
                "rma_customer_operation_id": cls.rma_operation_customer_refund_id.id,
                "rma_supplier_operation_id": cls.rma_sup_replace_op_id.id,
                "property_cost_method": "fifo",
            }
        )
        cls.product_fifo_1.categ_id = product_ctg
        cls.product_fifo_2.categ_id = product_ctg
        cls.product_fifo_3.categ_id = product_ctg

    @classmethod
    def _create_account(cls, acc_type, name, code, company, reconcile):
        return cls.account_model.create(
            {
                "name": name,
                "code": code,
                "account_type": acc_type,
                "company_ids": [(4, company.id)],
                "reconcile": reconcile,
            }
        )

    def _refund_rma_line(self, rma_line, qty):
        make_refund = self.rma_refund_wiz.with_context(
            **{
                "customer": True,
                "active_ids": rma_line.ids,
                "active_model": "rma.order.line",
            }
        ).create({"description": "Test refund"})
        make_refund.item_ids.qty_to_refund = qty
        make_refund.invoice_refund()
        refund = rma_line.refund_line_ids.move_id.filtered(lambda m: m.state == "draft")
        refund.action_post()
        return refund

    def test_01_cost_from_standard(self):
        """
        Test the value of the received move is taken from the standard cost when
        there is no reference
        """
        self.product_fifo_1.standard_price = 15
        rma_line = Form(self.rma_line.with_user(self.rma_basic_user))
        rma_line.partner_id = self.partner_id
        rma_line.product_id = self.product_fifo_1
        rma_line.price_unit = 1234
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._receive_rma(rma_line)
        self.assertEqual(picking.move_ids.value, 15.0)

    def test_02_cost_from_move(self):
        """
        Test the value of the received move is taken from the original delivery
        move when the reference is the stock move, even if the cost changed after
        """
        self.product_fifo_1.standard_price = 10
        self.product_fifo_2.standard_price = 20
        self.product_fifo_3.standard_price = 30
        self._create_inventory(
            self.product_fifo_1, 20.0, self.env.ref("stock.stock_location_customers")
        )
        products2move = [
            (self.product_fifo_1, 3),
            (self.product_fifo_2, 5),
            (self.product_fifo_3, 2),
        ]
        rma_customer_id = self._create_rma_from_move(
            products2move,
            "customer",
            self.customer,
            dropship=False,
        )
        rma_lines = rma_customer_id.rma_line_ids
        original_values = {
            line.product_id: line.reference_move_id.value for line in rma_lines
        }
        self.product_fifo_1.standard_price = 99
        self.product_fifo_2.standard_price = 99
        self.product_fifo_3.standard_price = 99
        rma_lines.price_unit = 999
        rma_lines.action_rma_to_approve()
        picking = self._receive_rma(rma_lines)
        for rma_line in rma_lines:
            move = picking.move_ids.filtered(
                lambda m, rma_line=rma_line: m.product_id == rma_line.product_id
            )
            self.assertEqual(move.value, original_values[rma_line.product_id])
            self.assertAlmostEqual(
                rma_line._get_price_unit(), move.value / move.quantity
            )

    def test_03_refund_cogs(self):
        """
        Test the customer refund created from the RMA reverses the COGS at the
        cost of the original delivery
        """
        self.company.anglo_saxon_accounting = True
        self.product_fifo_1.standard_price = 10
        self._create_inventory(
            self.product_fifo_1, 20.0, self.env.ref("stock.stock_location_customers")
        )
        rma_customer_id = self._create_rma_from_move(
            [(self.product_fifo_1, 3)],
            "customer",
            self.customer,
            dropship=False,
        )
        rma = rma_customer_id.rma_line_ids
        rma.action_rma_to_approve()
        self._receive_rma(rma)
        refund = self._refund_rma_line(rma, 2)
        cogs_lines = refund.line_ids.filtered(lambda line: line.display_type == "cogs")
        self.assertTrue(cogs_lines)
        self.assertEqual(cogs_lines.rma_line_id, rma)
        self.assertAlmostEqual(sum(cogs_lines.mapped("balance")), 0.0)
        self.assertAlmostEqual(
            sum(cogs_lines.filtered(lambda line: line.balance > 0).mapped("balance")),
            20.0,
        )

    def test_04_automated_refund(self):
        """
        Test receiving a customer RMA with an automated refund operation posts a
        refund at zero price reversing the COGS
        """
        self.company.anglo_saxon_accounting = True
        self.product_fifo_1.standard_price = 10
        self._create_inventory(
            self.product_fifo_1, 20.0, self.env.ref("stock.stock_location_customers")
        )
        rma_customer_id = self._create_rma_from_move(
            [(self.product_fifo_1, 3)],
            "customer",
            self.customer,
            dropship=False,
        )
        rma = rma_customer_id.rma_line_ids
        rma.operation_id.sudo().write(
            {"automated_refund": True, "refund_free_of_charge": True}
        )
        rma.action_rma_to_approve()
        self._receive_rma(rma)
        refund = rma.refund_line_ids.move_id
        self.assertEqual(len(refund), 1)
        self.assertEqual(refund.state, "posted")
        self.assertEqual(refund.amount_total, 0.0)
        self.assertEqual(rma.qty_refunded, rma.qty_received)
        cogs_lines = refund.line_ids.filtered(lambda line: line.display_type == "cogs")
        self.assertAlmostEqual(
            sum(cogs_lines.filtered(lambda line: line.balance > 0).mapped("balance")),
            30.0,
        )

    def test_05_valuation_entry_rma_line(self):
        """
        Test the journal items generated from the received RMA move are linked
        to the RMA line
        """
        customers = self.env.ref("stock.stock_location_customers")
        customers.valuation_account_id = self.env["account.account"].search(
            [("account_type", "=", "expense")], limit=1
        )
        self.product_fifo_1.standard_price = 10
        self._create_inventory(self.product_fifo_1, 20.0, customers)
        rma_customer_id = self._create_rma_from_move(
            [(self.product_fifo_1, 3)],
            "customer",
            self.customer,
            dropship=False,
        )
        rma = rma_customer_id.rma_line_ids
        rma.action_rma_to_approve()
        picking = self._receive_rma(rma)
        self.assertTrue(picking.move_ids.account_move_id)
        self.assertEqual(picking.move_ids.account_move_id.line_ids.rma_line_id, rma)
