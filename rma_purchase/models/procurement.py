# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        res = super(StockRule, self)._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if "rma_line_id" in values:
            line = values.get("rma_line_id")
            if line.reference_move_id:
                return res
            if line.purchase_order_line_id:
                moves = line.purchase_order_line_id.move_ids
                if moves:
                    # TODO: Should we be smart in the choice of the move?
                    layers = moves.mapped("stock_valuation_layer_ids")
                    cost = layers[-1].unit_cost
                    res["price_unit"] = cost
            elif line.account_move_line_id.purchase_line_id:
                purchase_lines = line.account_move_line_id.purchase_line_id
                moves = purchase_lines.mapped("move_ids")
                if moves:
                    layers = moves.mapped("stock_valuation_layer_ids")
                    cost = layers[-1].unit_cost
                    # TODO: Should we be smart in the choice of the move?
                    res["price_unit"] = cost
        return res


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    rma_id = fields.Many2one(
        comodel_name="rma.order", string="RMA", ondelete="set null"
    )
    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA line", ondelete="set null"
    )
