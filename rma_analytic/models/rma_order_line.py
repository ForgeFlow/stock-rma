# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
    )

    @api.multi
    def _prepare_rma_line_from_inv_line(self, line):
        res = super(RmaOrderLine, self)._prepare_rma_line_from_inv_line(line)
        if line.account_analytic_id:
            res.update(analytic_account_id=line.account_analytic_id.id)
        return res
