# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOperation(models.Model):

    _inherit = "rma.operation"

    invoice_policy = fields.Selection(
        string="Invoice policy",
        selection=[
            ("no", "Can't Create Services Invoice"),
            ("yes", "Can Create Services Invoice"),
        ],
        required=False,
        default="no",
    )
