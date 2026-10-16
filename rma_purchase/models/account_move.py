# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_invoice_line_from_rma_line(self, line):
        data = super()._prepare_invoice_line_from_rma_line(line)
        if line.purchase_order_line_id:
            data["purchase_line_id"] = line.purchase_order_line_id.id
        return data

    def _stock_account_prepare_anglo_saxon_in_lines_vals(self):
        lines_vals = super()._stock_account_prepare_anglo_saxon_in_lines_vals()
        rma_line_ids_by_key = {}
        for line in self.invoice_line_ids.filtered("rma_line_id"):
            key = (line.move_id.id, line.product_id.id, line.name[:64])
            rma_line_ids_by_key.setdefault(key, set()).add(line.rma_line_id.id)
        for vals in lines_vals:
            key = (vals["move_id"], vals["product_id"], vals["name"])
            rma_line_ids = rma_line_ids_by_key.get(key, set())
            if len(rma_line_ids) == 1:
                vals["rma_line_id"] = next(iter(rma_line_ids))
        return lines_vals
