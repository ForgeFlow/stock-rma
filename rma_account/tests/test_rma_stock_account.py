# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import Form

# pylint: disable=odoo-addons-relative-import
from odoo.addons.rma.tests.test_rma import TestRma


class TestRmaStockAccount(TestRma):
    @classmethod
    def setUpClass(cls):
        super(TestRmaStockAccount, cls).setUpClass()
        cls.acc_type_model = cls.env["account.account.type"]
        cls.account_model = cls.env["account.account"]
        cls.g_account_user = cls.env.ref("account.group_account_user")
        # we create new products to ensure previous layers do not affect when
        # running FIFO
        cls.product_fifo_1 = cls._create_product("product_fifo1")
        cls.product_fifo_2 = cls._create_product("product_fifo2")
        cls.product_fifo_3 = cls._create_product("product_fifo3")
        cls.rma_basic_user.write({"groups_id": [(4, cls.g_account_user.id)]})
        # The product category created in the base module is not automated valuation
        # we have to create a new category here
        # Create account for Goods Received Not Invoiced
        acc_type = cls._create_account_type("equity", "other")
        name = "Goods Received Not Invoiced"
        code = "grni"
        cls.account_grni = cls._create_account(acc_type, name, code, cls.company, True)
        # Create account for Cost of Goods Sold
        acc_type = cls._create_account_type("expense", "other")
        name = "Cost of Goods Sold"
        code = "cogs"
        cls.account_cogs = cls._create_account(acc_type, name, code, cls.company, False)
        # Create account for Inventory
        acc_type = cls._create_account_type("asset", "other")
        name = "Inventory"
        code = "inventory"
        cls.account_inventory = cls._create_account(
            acc_type, name, code, cls.company, False
        )
        product_ctg = cls.product_ctg_model.create(
            {
                "name": "test_product_ctg",
                "property_stock_valuation_account_id": cls.account_inventory.id,
                "property_valuation": "real_time",
                "property_stock_account_input_categ_id": cls.account_grni.id,
                "property_stock_account_output_categ_id": cls.account_cogs.id,
                "rma_approval_policy": "one_step",
                "rma_customer_operation_id": cls.rma_cust_replace_op_id.id,
                "rma_supplier_operation_id": cls.rma_sup_replace_op_id.id,
                "property_cost_method": "fifo",
            }
        )
        # We use FIFO to test the cost is taken from the original layers
        cls.product_fifo_1.categ_id = product_ctg
        cls.product_fifo_2.categ_id = product_ctg
        cls.product_fifo_3.categ_id = product_ctg

    @classmethod
    def _create_account_type(cls, name, a_type):
        acc_type = cls.acc_type_model.create(
            {"name": name, "type": a_type, "internal_group": name}
        )
        return acc_type

    @classmethod
    def _create_account(cls, acc_type, name, code, company, reconcile):
        """Create an account."""
        account = cls.account_model.create(
            {
                "name": name,
                "code": code,
                "user_type_id": acc_type.id,
                "company_id": company.id,
                "reconcile": reconcile,
            }
        )
        return account

    def check_accounts_used(
        self, account_move, debit_account=False, credit_account=False
    ):
        debit_line = account_move.mapped("line_ids").filtered(lambda l: l.debit)
        credit_line = account_move.mapped("line_ids").filtered(lambda l: l.credit)
        if debit_account:
            self.assertEqual(debit_line.account_id.code, debit_account)
        if credit_account:
            self.assertEqual(credit_line.account_id.code, credit_account)

    def test_01_cost_from_standard(self):
        """
        Test the price unit is taken from the standard cost when there is no reference
        """
        self.product_fifo_1.standard_price = 15
        rma_line = Form(self.rma_line.with_user(self.rma_basic_user))
        rma_line.partner_id = self.partner_id
        rma_line.product_id = self.product_fifo_1
        rma_line.price_unit = 1234
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._receive_rma(rma_line)
        self.assertEqual(picking.move_lines.stock_valuation_layer_ids.value, 15.0)
        account_move = picking.move_lines.stock_valuation_layer_ids.account_move_id
        self.check_accounts_used(
            account_move, debit_account="inventory", credit_account="cogs"
        )

    def test_02_cost_from_move(self):
        """
        Test the price unit is taken from the cost of the stock move when the
        reference is the stock move
        """
        # Set a standard price on the products
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
            self.env.ref("base.res_partner_2"),
            dropship=False,
        )
        # Set an incorrect price in the RMA (this should not affect cost)
        rma_customer_id.rma_line_ids.price_unit = 999
        rma_customer_id.rma_line_ids.action_rma_to_approve()
        picking = self._receive_rma(rma_customer_id.rma_line_ids)
        # Test the value in the layers of the incoming stock move is used
        for rma_line in rma_customer_id.rma_line_ids:
            value_origin = rma_line.reference_move_id.stock_valuation_layer_ids.value
            move_product = picking.move_lines.filtered(
                lambda l: l.product_id == rma_line.product_id
            )
            value_used = move_product.stock_valuation_layer_ids.value
            self.assertEqual(value_used, -value_origin)
