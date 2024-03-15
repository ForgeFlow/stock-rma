# Copyright (C) 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RmaOperation(models.Model):

    _inherit = "rma.operation"

    refund_reason_id = fields.Many2one(
        comodel_name="account.move.refund.reason",
        string="Refund reason",
    )
