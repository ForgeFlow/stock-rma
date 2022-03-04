# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.fields import Datetime
from odoo.tests.common import Form

# pylint: disable=odoo-addons-relative-import
from odoo.addons.rma_account.tests.test_rma_stock_account import TestRmaStockAccount


class TestRmaStockAccountPurchase(TestRmaStockAccount):
    @classmethod
    def setUpClass(cls):
        super(TestRmaStockAccountPurchase, cls).setUpClass()
        cls.pol_model = cls.env["purchase.order.line"]
        cls.po_model = cls.env["purchase.order"]
        # Create PO:
        cls.product_fifo_1.standard_price = 1234
        cls.po = cls.po_model.create(
            {
                "partner_id": cls.partner_id.id,
            }
        )
        cls.pol_1 = cls.pol_model.create(
            {
                "name": cls.product_fifo_1.name,
                "order_id": cls.po.id,
                "product_id": cls.product_fifo_1.id,
                "product_qty": 20.0,
                "product_uom": cls.product_fifo_1.uom_id.id,
                "price_unit": 100.0,
                "date_planned": Datetime.now(),
            }
        )
        cls.po.button_confirm()
        cls._do_picking(cls.po.picking_ids)

    def test_01_cost_from_po_move(self):
        """
        Test the price unit is taken from the cost of the stock move associated to
        the PO
        """
        self.product_fifo_1.standard_price = 1234  # this should not be taken
        supplier_view = self.env.ref("rma_purchase.view_rma_line_form")
        rma_line = Form(
            self.rma_line.with_context(supplier=1).with_user(self.rma_basic_user),
            view=supplier_view.id,
        )
        rma_line.partner_id = self.po.partner_id
        rma_line.purchase_order_line_id = self.pol_1
        rma_line.price_unit = 4356
        rma_line = rma_line.save()
        rma_line.action_rma_to_approve()
        picking = self._deliver_rma(rma_line)
        # The price is not the standard price, is the value of the incoming layer
        # of the PO
        rma_move_value = picking.move_lines.stock_valuation_layer_ids.value
        po_move_value = self.po.picking_ids.mapped(
            "move_lines.stock_valuation_layer_ids"
        )[-1].value
        self.assertEqual(-rma_move_value, po_move_value)
        # Test the accounts used
        account_move = picking.move_lines.stock_valuation_layer_ids.account_move_id
        self.check_accounts_used(account_move, "grni", "inventory")
        # Now forcing a refund to check the stock journals
        rma_line.refund_policy = "ordered"
        make_refund = (
            self.env["rma.refund"]
            .with_context(
                **{
                    "customer": True,
                    "active_ids": rma_line.ids,
                    "active_model": "rma.order.line",
                }
            )
            .create({"description": "Test refund"})
        )
        make_refund.invoice_refund()
        rma_line.refund_line_ids.move_id.action_post()
        account_move = rma_line.mapped("refund_line_ids.move_id")
        self.check_accounts_used(account_move, credit_account="grni")
