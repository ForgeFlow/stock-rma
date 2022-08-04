# Copyright 2020-22 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    repair_location_dest_id = fields.Many2one(
        string="Repair Destination Location",
        comodel_name="stock.location",
        help="Indicate here the destination location of the repair",
    )
