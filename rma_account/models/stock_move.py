# Copyright 2017-22 ForgeFlow S.L. (www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves = super()._action_done(cancel_backorder=cancel_backorder)
        # qty_received is not reliably recomputed by its api.depends at this point
        moves.filtered(
            lambda m: m.rma_line_id and m.is_in and m.company_id.anglo_saxon_accounting
        ).rma_line_id._check_refund_zero_cost()
        return moves

    def _get_value_from_returns(self, quantity, at_date=None):
        reference_move = self.rma_line_id.reference_move_id
        if self.is_in and reference_move.is_out:
            reference_qty = reference_move._get_valued_qty()
            return {
                "value": 0
                if self.product_uom.is_zero(reference_qty)
                else reference_move.sudo().value * quantity / reference_qty,
                "quantity": quantity,
                "description": self.env._(
                    "Value based on original move %(reference)s",
                    reference=reference_move.reference,
                ),
            }
        return super()._get_value_from_returns(quantity, at_date=at_date)

    def _get_account_move_line_vals(self):
        lines_vals = super()._get_account_move_line_vals()
        if self.rma_line_id:
            for vals in lines_vals:
                vals["rma_line_id"] = self.rma_line_id.id
        return lines_vals
