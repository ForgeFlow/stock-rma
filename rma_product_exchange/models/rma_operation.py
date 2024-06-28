# Copyright 2024 Akretion
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    product_exchange = fields.Boolean(
        help="Check if you wish to authorize product exchange.", default=False
    )
