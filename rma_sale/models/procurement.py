# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


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
            if line.reference_move_id:
                return res
            if line.sale_line_id:
                moves = line.sale_line_id.move_ids.filtered(
                    lambda x: x.state == "done"
                    and x.location_id.usage in ("internal", "supplier")
                    and x.location_dest_id.usage == "customer"
                )
                if moves:
                    layers = moves.mapped("stock_valuation_layer_ids")
                    if layers:
                        price_unit = sum(layers.mapped("value")) / sum(
                            layers.mapped("quantity")
                        )
                        res["price_unit"] = price_unit
            elif line.account_move_line_id:
                sale_lines = line.account_move_line_id.sale_line_ids
                moves = sale_lines.mapped("move_ids").filtered(
                    lambda x: x.state == "done"
                    and x.location_id.usage in ("internal", "supplier")
                    and x.location_dest_id.usage == "customer"
                )
                if moves:
                    layers = moves.mapped("stock_valuation_layer_ids")
                    if layers:
                        price_unit = sum(layers.mapped("value")) / sum(
                            layers.mapped("quantity")
                        )
                        res["price_unit"] = price_unit
        return res
