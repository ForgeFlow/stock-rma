# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_invoice_line_from_rma_line(self, line):
        data = super(AccountMove, self)._prepare_invoice_line_from_rma_line(line)
        data["purchase_line_id"]: line.id
        return data
