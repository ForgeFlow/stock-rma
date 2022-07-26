# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_rma_put_away = fields.Boolean(
        string="Is RMA Put Away",
        copy=False,
        help="This Stock Move has been created from a Put Away operation in "
        "the RMA.",
    )

    def _is_in_out_rma_move(self, op, states, location_type):
        res = super(StockMove, self)._is_in_out_rma_move(op, states, location_type)
        if self.is_rma_put_away:
            return False
        return res
