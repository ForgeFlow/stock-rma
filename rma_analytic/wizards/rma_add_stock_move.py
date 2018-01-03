# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaAddStockMove(models.TransientModel):
    _inherit = 'rma_add_stock_move'
    _description = 'Wizard to add rma lines from pickings'

    @api.model
    def _prepare_rma_line_from_stock_move(self, sm, lot=False):
        data = super(RmaAddStockMove, self)._prepare_rma_line_from_stock_move(
            sm, lot)
        data.update(analytic_account_id=sm.analytic_account_id.id)
        return data
