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
