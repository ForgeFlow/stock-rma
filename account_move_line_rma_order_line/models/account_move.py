# © 2017-2022 ForgeFlow S.L. (www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        product_model = self.env["product.product"]
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for line in res:
            if line.get("product_id", False):
                product = product_model.browse(line.get("product_id", False))
                if (
                    line.get("account_id")
                    != product.categ_id.property_stock_valuation_account_id.id
                ):
                    current_move = self.browse(line.get("move_id", False))
                    current_rma = current_move.invoice_line_ids.filtered(
                        lambda x: x.rma_line_id and x.product_id.id == product.id
                    ).mapped("rma_line_id")
                    if len(current_rma) == 1:
                        line.update({"rma_line_id": current_rma.id})
                    elif len(current_rma) > 1:
                        find_with_label_rma = current_rma.filtered(
                            lambda x: x.name == line.get("name")
                        )
                        if len(find_with_label_rma) == 1:
                            line.update({"rma_line_id": find_with_label_rma.id})
        return res
