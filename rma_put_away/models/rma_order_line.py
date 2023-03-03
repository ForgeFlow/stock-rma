# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.depends(
        "move_ids",
        "move_ids.state",
        "move_ids.is_rma_put_away",
        "qty_put_away",
        "put_away_policy",
        "product_qty",
    )
    def _compute_qty_to_put_away(self):
        for rec in self:
            rec.qty_to_put_away = 0.0
            if rec.put_away_policy == "ordered":
                rec.qty_to_put_away = rec.product_qty - rec.qty_put_away
            elif rec.put_away_policy == "received":
                rec.qty_to_put_away = rec.qty_received - rec.qty_put_away

    @api.depends("move_ids", "move_ids.state", "move_ids.is_rma_put_away")
    def _compute_qty_in_put_away(self):
        product_obj = self.env["uom.uom"]
        for rec in self:
            qty = 0.0
            for move in rec.move_ids.filtered(
                lambda m: m.state in ["draft", "confirmed", "assigned"]
                and m.is_rma_put_away
            ):
                qty += product_obj._compute_quantity(move.product_uom_qty, rec.uom_id)
            rec.qty_in_put_away = qty

    @api.depends("move_ids", "move_ids.state", "move_ids.is_rma_put_away")
    def _compute_qty_put_away(self):
        product_obj = self.env["uom.uom"]
        for rec in self:
            qty = 0.0
            for move in rec.move_ids.filtered(
                lambda m: m.state in ["done"] and m.is_rma_put_away
            ):
                qty += product_obj._compute_quantity(move.product_uom_qty, rec.uom_id)
            rec.qty_put_away = qty

    def _compute_put_away_count(self):
        for line in self:
            pickings = self.move_ids.filtered(lambda m: m.is_rma_put_away).mapped(
                "picking_id"
            )
            line.put_away_count = len(pickings)

    qty_to_put_away = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_to_put_away",
        store=True,
    )
    qty_in_put_away = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_in_put_away",
        store=True,
    )
    qty_put_away = fields.Float(
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_put_away",
        store=True,
    )
    put_away_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
        required=True,
        readonly=False,
    )
    put_away_count = fields.Integer(
        compute="_compute_put_away_count", string="# Put Aways"
    )

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        res = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.put_away_policy = self.operation_id.put_away_policy or "no"
        return res

    def action_view_put_away_transfers(self):
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
