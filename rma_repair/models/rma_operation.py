# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

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
