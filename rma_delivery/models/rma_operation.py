# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaOperation(models.Model):

    _inherit = "rma.operation"

    default_carrier_id = fields.Many2one(
        comodel_name="delivery.carrier", string="Default carrier", required=False
    )
