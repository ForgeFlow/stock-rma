# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _account_entry_move(self, qty, description, svl_id, cost):
        res = super(StockMove, self)._account_entry_move(qty, description, svl_id, cost)
        if self.company_id.anglo_saxon_accounting:
            # Eventually reconcile together the invoice and valuation accounting
            # entries on the stock interim accounts
            self.rma_line_id._stock_account_anglo_saxon_reconcile_valuation()
        return res
