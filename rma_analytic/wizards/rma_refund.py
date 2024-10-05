# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaRefund(models.TransientModel):
    _inherit = "rma.refund"

    @api.model
    def prepare_refund_line(self, item):
        res = super(RmaRefund, self).prepare_refund_line(item)
        if item.line_id.analytic_account_id:
            res.update(analytic_account_id=item.line_id.analytic_account_id.id)
        return res
