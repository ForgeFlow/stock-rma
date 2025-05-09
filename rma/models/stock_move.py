# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    rma_line_id = fields.Many2one(
        "rma.order.line", string="RMA line", ondelete="restrict", index="btree_not_null"
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("group_id"):
                group = self.env["procurement.group"].browse(vals["group_id"])
                if group.rma_line_id:
                    vals["rma_line_id"] = group.rma_line_id.id
        return super().create(vals_list)

    def _action_assign(self, force_qty=False):
        res = super()._action_assign(force_qty=force_qty)
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

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        res = super()._prepare_merge_moves_distinct_fields()
        return res + ["rma_line_id"]

    def _prepare_procurement_values(self):
        self.ensure_one()
        res = super(StockMove, self)._prepare_procurement_values()
        res["rma_line_id"] = self.rma_line_id.id
        return res


class StockMoveLine(models.Model):

    _inherit = "stock.move.line"

    def _should_bypass_reservation(self, location):
        res = super(StockMoveLine, self)._should_bypass_reservation(location)
        if self.env.context.get(
            "force_no_bypass_reservation"
        ) and location.usage not in ("customer", "supplier"):
            return False
        return res
