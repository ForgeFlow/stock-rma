# Copyright (C) 2019 Daniel Reis, OpenSource Integrators
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _create_account_move_line(
            self, credit_account_id, debit_account_id, journal_id):
        self.ensure_one()
        rma_price = self.rma_line_id.price_unit
        if rma_price:
            self = self.with_context(force_valuation_amount=rma_price)
        return super(StockMove, self)._create_account_move_line(
            credit_account_id, debit_account_id, journal_id)
