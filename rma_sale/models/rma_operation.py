# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    sale_policy = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Sale Policy",
        default="no",
    )
