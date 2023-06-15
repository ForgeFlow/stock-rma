# Copyright (C) 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    refund_reason_id = fields.Many2one(
        comodel_name="account.move.refund.reason",
        string="Refund reason",
    )

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.refund_reason_id = self.operation_id.refund_reason_id.id
        return result
