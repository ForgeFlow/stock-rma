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
            line = self.env["rma.order.line"].browse([line])
            move = line.reference_move_id
            if move and move.stock_valuation_layer_ids:
                cost = move.stock_valuation_layer_ids[-1].unit_cost
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
