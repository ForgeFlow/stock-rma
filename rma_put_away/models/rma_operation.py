# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    put_away_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
    )
    put_away_route_id = fields.Many2one(
        comodel_name="stock.route",
        string="Put Away Route",
        domain=[("rma_selectable", "=", True)],
        default=lambda self: self._default_routes(),
    )

    put_away_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Put Away Destination Location",
    )
