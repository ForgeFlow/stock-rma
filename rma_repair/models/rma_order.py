# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    def _compute_repair_count(self):
        for rma in self:
            repairs = rma.mapped("rma_line_ids.repair_ids")
            rma.repair_count = len(repairs)

    def _compute_repair_transfer_count(self):
        for order in self:
            pickings = (
                order.mapped("rma_line_ids.move_ids")
                .filtered(lambda m: m.is_rma_put_away)
                .mapped("picking_id")
            )
            order.repair_transfer_count = len(pickings)

    repair_count = fields.Integer(
        compute="_compute_repair_count", string="# of Repairs"
    )

    repair_transfer_count = fields.Integer(
        compute="_compute_repair_transfer_count", string="# Repair Transfers"
    )

    def action_view_repair_order(self):
        action = self.env.ref("repair.action_repair_order_tree")
        result = action.sudo().read()[0]
        repair_ids = self.mapped("rma_line_ids.repair_ids").ids
        result["domain"] = [("id", "in", repair_ids)]
        return result

    def action_view_repair_transfers(self):
        self.ensure_one()
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.sudo().read()[0]
        pickings = self.env["stock.picking"]
        for line in self.rma_line_ids:
            pickings |= line.move_ids.filtered(
                lambda m: m.is_rma_repair_transfer
            ).mapped("picking_id")
        return self._view_shipments(result, pickings)
