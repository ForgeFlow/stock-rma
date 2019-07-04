# Copyright (C) 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    @api.multi
    def receiving_out_of_the_company(self):
        if (not self.location_dest_id.company_id and
                self.location_id.usage in ('customer', 'supplier')):
            return True
        return False

    @api.multi
    def _account_entry_move(self):
        if self.receiving_out_of_the_company():
            return
        else:
            return super(StockMove, self)._account_entry_move()
