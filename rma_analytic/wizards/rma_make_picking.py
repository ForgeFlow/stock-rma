# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaMakePicking(models.TransientModel):
    _inherit = "rma_make_picking.wizard"

    @api.model
    def _get_procurement_data(self, item, group, qty, picking_type):
        procurement_data = super(RmaMakePicking, self)._get_procurement_data(
            item, group, qty, picking_type
        )
        procurement_data.update(analytic_account_id=item.line_id.analytic_account_id.id)
        return procurement_data
