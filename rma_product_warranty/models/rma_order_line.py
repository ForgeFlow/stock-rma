# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import fields, models


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    warranty_end_date = fields.Date(compute="_compute_warranty_end_date")
    under_warranty = fields.Boolean(compute="_compute_under_warranty")

    def _compute_warranty_end_date(self):
        for rec in self:
            warranty = rec.product_id.warranty
            if rec.reference_move_id and warranty:
                if rec.product_id.warranty_type == "day":
                    rec.warranty_end_date = rec.reference_move_id.date + relativedelta(
                        days=warranty
                    )
                elif rec.product_id.warranty_type == "week":
                    rec.warranty_end_date = rec.reference_move_id.date + relativedelta(
                        weeks=warranty
                    )
                elif rec.product_id.warranty_type == "month":
                    rec.warranty_end_date = rec.reference_move_id.date + relativedelta(
                        months=warranty
                    )
                elif rec.product_id.warranty_type == "year":
                    rec.warranty_end_date = rec.reference_move_id.date + relativedelta(
                        years=warranty
                    )
                else:
                    rec.warranty_end_date = False
            else:
                rec.warranty_end_date = False

    def _compute_under_warranty(self):
        today = datetime.today()
        for rec in self:
            if not rec.warranty_end_date:
                rec.under_warranty = True
            else:
                rec.under_warranty = rec.warranty_end_date >= today.date()
