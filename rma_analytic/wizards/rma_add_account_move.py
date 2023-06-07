# Copyright 2017-23 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class RmaAddAccountMove(models.TransientModel):
    _inherit = "rma_add_account_move"

    def _prepare_rma_line_from_inv_line(self, line):
        res = super(RmaAddAccountMove, self)._prepare_rma_line_from_inv_line(line)
        if line.analytic_account_id:
            res.update(analytic_account_id=line.analytic_account_id.id)
        return res
