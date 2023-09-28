# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, exceptions, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.constrains("account_analytic_id")
    def check_analytic(self):
        for line in self.filtered(lambda p: p.rma_line_id):
            if line.account_analytic_id != line.rma_line_id.analytic_account_id:
                raise exceptions.ValidationError(
                    _(
                        "The analytic account in the PO line it's not the same"
                        " as in the rma line"
                    )
                )
