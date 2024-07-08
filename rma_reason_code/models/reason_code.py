# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from random import randint

from odoo import fields, models


class RMAReasonCode(models.Model):
    _name = "rma.reason.code"
    _description = "RMA Reason Code"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char("Code", required=True)
    description = fields.Text("Description")
    type = fields.Selection(
        [
            ("customer", "Customer RMA"),
            ("supplier", "Supplier RTV"),
            ("both", "Both Customer and Supplier"),
        ],
        default="both",
        required=True,
    )
    color = fields.Integer("Color", default=_get_default_color)
