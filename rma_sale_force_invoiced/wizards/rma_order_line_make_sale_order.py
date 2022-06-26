# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.html)

from odoo import api, models


class RmaLineMakeSaleOrder(models.TransientModel):
    _inherit = "rma.order.line.make.sale.order"

    @api.model
    def _prepare_sale_order(self, line):
        data = super(RmaLineMakeSaleOrder, self)._prepare_sale_order(line)
        data["force_invoiced"] = line.operation_id.sale_force_invoiced
        return data
