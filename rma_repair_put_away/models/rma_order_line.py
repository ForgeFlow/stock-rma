# Copyright 2024 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    def _compute_repair_transfer_count(self):
        for line in self:
            pickings = line.move_ids.filtered(lambda m: m.is_rma_put_away).mapped(
                "picking_id"
            )
            line.repair_transfer_count = len(pickings)

    def action_view_repair_transfers(self):
        super().action_view_repair_transfers()
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        pickings = self.env["stock.picking"]
        for line in self:
            pickings |= line.move_ids.filtered(lambda m: m.is_rma_put_away).mapped(
                "picking_id"
            )
        # choose the view_mode accordingly
        if len(pickings) != 1:
            result["domain"] = "[('id', 'in', " + str(pickings.ids) + ")]"
        elif len(pickings) == 1:
            res = self.env.ref("stock.view_picking_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = pickings.ids[0]
        return result
