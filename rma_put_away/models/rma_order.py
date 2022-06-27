# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    def _compute_put_away_count(self):
        for order in self:
            pickings = (
                order.mapped("rma_line_ids.move_ids")
                .filtered(lambda m: m.is_rma_put_away)
                .mapped("picking_id")
            )
            order.put_away_count = len(pickings)

    put_away_count = fields.Integer(
        compute="_compute_put_away_count", string="# Put Away"
    )

    def action_view_put_away_transfers(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        pickings = self.env["stock.picking"]
        for line in self.rma_line_ids:
            pickings |= line.move_ids.filtered(lambda m: m.is_rma_put_away).mapped(
                "picking_id"
            )
        return self._view_shipments(result, pickings)
