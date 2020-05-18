# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, models


class MakeInvoice(models.TransientModel):
    _inherit = 'repair.order.make_invoice'

    @api.multi
    def make_invoices(self):
        if self._context.get('active_model') == 'rma.order.line':
            rma_lines = self.env['rma.order.line'].browse(
                self._context.get('active_ids'))
            self = self.with_context(
                active_ids=rma_lines.mapped('repair_ids').ids)
        return super().make_invoices()
