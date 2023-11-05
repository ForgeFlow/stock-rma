# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from dateutil.relativedelta import relativedelta

from odoo import models


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    def _compute_warranty_end_date(self):
        res = super()._compute_warranty_end_date()
        for rec in self:
            warranty = rec.product_id.warranty
            if rec.account_move_line_id and warranty:
                if rec.product_id.warranty_type == "day":
                    rec.warranty_end_date = (
                        rec.account_move_line_id.date + relativedelta(days=warranty)
                    )
                elif rec.product_id.warranty_type == "week":
                    rec.warranty_end_date = (
                        rec.account_move_line_id.date + relativedelta(weeks=warranty)
                    )
                elif rec.product_id.warranty_type == "month":
                    rec.warranty_end_date = (
                        rec.account_move_line_id.date + relativedelta(months=warranty)
                    )
                elif rec.product_id.warranty_type == "year":
                    rec.warranty_end_date = (
                        rec.account_move_line_id.date + relativedelta(years=warranty)
                    )
            elif rec.sale_line_id and rec.sale_line_id.invoice_lines:
                rec.warranty_end_date = rec.sale_line_id.invoice_lines[
                    0
                ].date + relativedelta(years=warranty)
        return res
