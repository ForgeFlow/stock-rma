# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models, api


class RmaRefund(models.TransientModel):
    _inherit = "rma.refund"

    @api.model
    def prepare_refund_line(self, item, refund):
        refund_line = super(RmaAddInvoice, self).prepare_refund_line(
            item, refund)
        refund_line.update(
            analytic_account_id=item.line_id.analytic_account_id.id)
        return refund_line
