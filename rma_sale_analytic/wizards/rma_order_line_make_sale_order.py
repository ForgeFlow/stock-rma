# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaLineMakeSaleOrder(models.TransientModel):
    _inherit = "rma.order.line.make.sale.order"

    @api.model
    def _prepare_sale_order(self, line):
        res = super(RmaLineMakeSaleOrder, self)._prepare_sale_order(line)
        res.update(analytic_account_id=line.analytic_account_id.id)
        return res
