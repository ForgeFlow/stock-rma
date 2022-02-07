# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_assign(self):
        """When you try to bring back a product from a customer location,
        it may happen that there is no quants available to perform the
        picking."""
        res = super(StockPicking, self).action_assign()
        for picking in self:
            for move in picking.move_lines:
                if (
                    move.rma_line_id
                    and move.state == "confirmed"
                    and move.location_id.usage == "customer"
                ):
                    move.force_assign()
        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    rma_line_id = fields.Many2one(
        "rma.order.line", string="RMA line", ondelete="restrict"
    )

    @api.model
    def create(self, vals):
        if vals.get("group_id"):
            group = self.env["procurement.group"].browse(vals["group_id"])
            if group.rma_line_id:
                vals["rma_line_id"] = group.rma_line_id.id
        return super(StockMove, self).create(vals)

    def _action_assign(self):
        res = super(StockMove, self)._action_assign()
        for move in self:
            if move.rma_line_id:
                move.partner_id = move.rma_line_id.partner_id.id or False
        return res

    @api.model
    def _get_first_usage(self):
        if self.move_orig_ids:
            # We assume here that all origin moves come from the same place
            return self.move_orig_ids[0]._get_first_usage()
        else:
            return self.location_id.usage

    @api.model
    def _get_last_usage(self):
        if self.move_dest_ids:
            # We assume here that all origin moves come from the same place
            return self.move_dest_ids[0]._get_last_usage()
        else:
            return self.location_dest_id.usage

    def _should_bypass_reservation(self, forced_location=False):
        res = super()._should_bypass_reservation(forced_location=forced_location)
        if self.env.context.get("force_no_bypass_reservation"):
            return False
        return res
