# Copyright 2020-21 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class RepairOrder(models.Model):
    _inherit = "repair.order"

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA", ondelete="restrict"
    )
    under_warranty = fields.Boolean(
        related="rma_line_id.under_warranty",
    )
    payment_state = fields.Selection(
        related="invoice_id.payment_state", string="Payment Status"
    )
