# Copyright 2026 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_value_from_returns(self, quantity, at_date=None):
        rma_line = self.rma_line_id
        if self.is_in and rma_line and not rma_line.reference_move_id:
            sale_moves = rma_line._get_sale_delivery_moves()
            if sale_moves:
                return {
                    "value": sale_moves.sudo()._get_price_unit() * quantity,
                    "quantity": quantity,
                    "description": self.env._(
                        "Value based on sales order moves %(reference)s",
                        reference=", ".join(sale_moves.mapped("reference")),
                    ),
                }
        return super()._get_value_from_returns(quantity, at_date=at_date)
