# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaAddInvoice(models.TransientModel):
    _inherit = 'rma_add_invoice'

    @api.model
    def _prepare_rma_line_from_inv_line(self, line):
        data = super(RmaAddInvoice, self)._prepare_rma_line_from_inv_line(line)
        data.update(analytic_account_id=line.analytic_account_id.id)
        return data
