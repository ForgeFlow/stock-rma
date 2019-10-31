# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class RmaAddInvoice(models.TransientModel):
    _inherit = "rma_add_invoice"

    def _prepare_rma_line_from_inv_line(self, line):
        res = super(
            RmaAddInvoice, self
        )._prepare_rma_line_from_inv_line(line)
        if line.account_analytic_id:
            res.update(
                analytic_account_id=line.account_analytic_id.id
            )
        return res
