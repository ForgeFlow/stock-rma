# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    put_away_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Put Away Policy",
        default="no",
    )

    internal_route_id = fields.Many2one(
        comodel_name="stock.location.route",
        string="Internal Route",
        domain=[("rma_selectable", "=", True)],
        default=lambda self: self._default_routes(),
    )

    internal_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Internal Destination Warehouse",
        default=lambda self: self._default_warehouse_id(),
    )


