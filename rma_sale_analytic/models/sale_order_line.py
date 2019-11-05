# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, exceptions, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.constrains('analytic_account_id')
    def check_analytic(self):
        for line in self:
            if (line.analytic_account_id !=
                    line.rma_line_id.analytic_account_id):
                raise exceptions.ValidationError(
                    _("The analytic account in the sale line it's not the same"
                      " as in the rma line"))
