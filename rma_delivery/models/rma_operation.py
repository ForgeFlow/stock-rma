# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaOperation(models.Model):

    _inherit = "rma.operation"

    default_carrier_in_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Default Recepit carrier",
        required=False,
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]",
    )

    default_carrier_out_id = fields.Many2one(
        comodel_name="delivery.carrier",
        string="Default Delivery carrier",
        required=False,
        domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]",
    )
