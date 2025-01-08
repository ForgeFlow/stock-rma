# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    repair_type = fields.Selection(
        [
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Repair Policy",
        default="no",
    )
    delivery_policy = fields.Selection(
        selection_add=[("repair", "Based on Repair Quantities")]
    )
    repair_location_id = fields.Many2one(
        string="Repair Location",
        comodel_name="stock.location",
        help="Indicate here the source location of the product to be repaired",
    )
    repair_route_id = fields.Many2one(
        comodel_name="stock.route",
        string="Repair Route",
        domain=[("rma_selectable", "=", True)],
    )
