# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, exceptions, models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.constrains('analytic_account_id')
    def check_analytic(self):
        for inv in self:
            if inv.analytic_account_id != inv.rma_line_id.analytic_account_id:
                raise exceptions.ValidationError(
                    _("The analytic account in the invoice it's not the same"
                      " as in the rma line"))
