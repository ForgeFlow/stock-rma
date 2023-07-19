# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, models


class RMAOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.onchange("sale_line_id")
    def _onchange_sale_line_id(self):
        res = super()._onchange_sale_line_id()
        if self.sale_line_id:
            self.analytic_account_id = self.sale_line_id.order_id.analytic_account_id
        return res
