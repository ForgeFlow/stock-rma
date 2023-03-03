# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.html)
from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    sale_force_invoiced = fields.Boolean(
        help="Forces the sales order created from RMA to be flagged invoiced. "
        "This is useful when the sales order is free of charge.",
    )
