# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    def _compute_repair_transfer_count(self):
        res = super()._compute_repair_transfer_count()
        for order in self:
            pickings = (
                order.mapped("rma_line_ids.move_ids")
                .filtered(lambda m: m.is_rma_put_away)
                .mapped("picking_id")
            )
            order.repair_transfer_count = len(pickings)
        return res

    def action_view_repair_transfers(self):
        super()._compute_repair_transfer_count()
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        pickings = self.env["stock.picking"]
        for line in self.rma_line_ids:
            pickings |= line.move_ids.filtered(lambda m: m.is_rma_put_away).mapped(
                "picking_id"
            )
        return self._view_shipments(result, pickings)
