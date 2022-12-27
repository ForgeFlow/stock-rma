# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_invoice_line_from_rma_line(self, line):
        data = super(AccountMove, self)._prepare_invoice_line_from_rma_line(line)
        if line.purchase_order_line_id:
            data["purchase_line_id"]: line.purchase_order_line_id.id
        return data

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            rma_mls = move.line_ids.filtered(lambda l: l.rma_line_id)
            if rma_mls:
                # Try to reconcile the interim accounts for RMA lines
                rmas = rma_mls.mapped("rma_line_id")
                for rma in rmas:
                    product_accounts = (
                        rma.product_id.product_tmpl_id._get_product_accounts()
                    )
                    if rma.type == "customer":
                        product_interim_account = product_accounts["stock_output"]
                    else:
                        product_interim_account = product_accounts["stock_input"]
                    if product_interim_account.reconcile:
                        # Get the in and out moves
                        amls = self.env["account.move.line"].search(
                            [
                                ("rma_line_id", "=", rma.id),
                                ("account_id", "=", product_interim_account.id),
                                ("parent_state", "=", "posted"),
                                ("reconciled", "=", False),
                            ]
                        )
                        amls.reconcile()
        return res
