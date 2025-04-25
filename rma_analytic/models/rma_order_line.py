# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class RmaOrderLine(models.Model):
    _name = "rma.order.line"
    _inherit = ["rma.order.line", "analytic.mixin"]

    analytic_distribution = fields.Json()

    @api.onchange("account_move_line_id")
    def _onchange_account_move_line_id(self):
        if self.analytic_distribution:
            self.analytic_distribution = self.analytic_distribution
        return super()._onchange_account_move_line_id()
