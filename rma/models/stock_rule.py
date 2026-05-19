# Copyright (C) 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models
from odoo.exceptions import ValidationError


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
        res = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        line = self.env["rma.order.line"]
        if "rma_line_id" in values:
            line = values.get("rma_line_id")
            line = self.env["rma.order.line"].browse([line])
        elif "stock_reference_id" in values and values["stock_reference_id"]:
            stock_reference = values["stock_reference_id"]
            line = stock_reference.rma_line_id
        if line:
            res["rma_line_id"] = line.id
            if line.delivery_address_id:
                res["partner_id"] = line.delivery_address_id.id
            elif line.rma_id.partner_id:
                res["partner_id"] = line.rma_id.partner_id.id
            res["price_unit"] = line._get_price_unit()
        return res

    @api.model
    def _get_rule(self, product_id, location_id, values):
        # upon move confirmation some values are missing
        picking_type = self.env.context.get("picking_type")
        if picking_type and (not values.get("route_ids") and values.get("rma_line_id")):
            rma_line_id = values.get("rma_line_id")
            rma_line = self.env["rma.order.line"].browse([rma_line_id])
            if rma_line and rma_line.in_route_id:
                if picking_type == "incoming":
                    values["route_ids"] = rma_line.in_route_id
                else:
                    values["route_ids"] = rma_line.out_route_id
        res = super()._get_rule(product_id, location_id, values)
        # Ensure that the selected rule is valid for RMAs
        rma_route_check = self.env.context.get("rma_route_check")
        if rma_route_check:
            if res and not res.route_id.rma_selectable:
                msg = (
                    "No rule found for this product {product} and location {location} "
                    "that is valid for RMA operations."
                )
                raise ValidationError(
                    self.env._(msg).format(
                        product=product_id.default_code or product_id.name,
                        location=location_id.complete_name,
                    )
                )
            # Don't enforce check on any chained moves
            rma_route_check.clear()
        return res
