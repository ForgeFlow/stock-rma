# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models
from odoo.tools import float_is_zero


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    def _get_price_unit(self):
        self.ensure_one()
        price_unit = 0
        if (
            self.env.context.get("product_required")
            and self.env.context.get("product_required") != self.product_id
            and self.sale_line_id
            and self.sale_line_id.move_ids.filtered(
                lambda x: x.state == "done"
                and x.product_id == self.env.context.get("product_required")
            )
        ):
            done_moves = self.sale_line_id.move_ids.filtered(
                lambda x: x.state == "done"
                and x.location_dest_id.usage != "internal"
                and x.location_id.usage == "internal"
                and x.product_id == self.env.context.get("product_required")
            )
            layers_value = sum(done_moves.mapped("stock_valuation_layer_ids.value"))
            layers_quantity = sum(
                done_moves.mapped("stock_valuation_layer_ids.quantity")
            )
            pd = self.env["decimal.precision"].precision_get("Product Price")
            if not float_is_zero(layers_quantity, precision_digits=pd):
                price_unit = layers_value / layers_quantity
            else:
                price_unit = super(RmaOrderLine, self)._get_price_unit()
        else:
            price_unit = super(RmaOrderLine, self)._get_price_unit()
        return price_unit

    def _get_rma_quantity_from_moves(self, moves):
        self.ensure_one()
        boms = moves.bom_line_id.bom_id
        relevant_bom = boms.filtered(
            lambda b: b.type == "phantom"
            and (
                b.product_id == self.product_id
                or (
                    b.product_tmpl_id == self.product_id.product_tmpl_id
                    and not b.product_id
                )
            )
        )
        if relevant_bom:
            # moves are already filtered and we never have return here
            filters = {
                "incoming_moves": lambda m: True,
                "outgoing_moves": lambda m: False,
            }
            order_qty = self.uom_id._compute_quantity(
                self.product_qty, relevant_bom.product_uom_id
            )
            qty = moves._compute_kit_quantities(
                self.product_id, order_qty, relevant_bom, filters
            )
        else:
            qty = super()._get_rma_quantity_from_moves(moves)
        return qty
