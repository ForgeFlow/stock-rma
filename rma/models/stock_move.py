# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


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
        if vals.get("move_dest_ids"):
            # in multi steps receipt we ensure the link to rma lines is added
            move_dest_ids = self.env["stock.move"].browse(
                [t[1] for t in vals["move_dest_ids"]]
            )
            if move_dest_ids:
                if move_dest_ids.rma_line_id:
                    vals["rma_line_id"] = move_dest_ids.rma_line_id.id
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

    def _get_available_quantity(
        self,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=False,
        allow_negative=False,
    ):
        if (
            not lot_id
            and self.rma_line_id.lot_id
            and self.location_id.usage == "internal"
        ):
            # In supplier RMA deliveries we can only send the RMA lot/serial.
            lot_id = self.rma_line_id.lot_id
        return super()._get_available_quantity(
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
            allow_negative=allow_negative,
        )

    def _update_reserved_quantity(
        self,
        need,
        available_quantity,
        location_id,
        lot_id=None,
        package_id=None,
        owner_id=None,
        strict=True,
    ):
        if (
            not lot_id
            and self.rma_line_id.lot_id
            and self.location_id.usage == "internal"
        ):
            # In supplier RMA deliveries we can only send the RMA lot/serial.
            lot_id = self.rma_line_id.lot_id
        return super()._update_reserved_quantity(
            need,
            available_quantity,
            location_id,
            lot_id=lot_id,
            package_id=package_id,
            owner_id=owner_id,
            strict=strict,
        )

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        res = super()._prepare_merge_moves_distinct_fields()
        return res + ["rma_line_id"]
