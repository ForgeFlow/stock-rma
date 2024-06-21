# Copyright (C) 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class RmaRefund(models.TransientModel):

    _inherit = "rma.refund"

    @api.model
    def _get_refund_reason(self):
        active_ids = self.env.context.get("active_ids", False)
        return (
            active_ids
            and self.env["rma.order.line"].browse(active_ids[0]).refund_reason_id.id
            or False
        )

    refund_reason_id = fields.Many2one(
        comodel_name="account.move.refund.reason",
        string="Refund Reason",
        default=lambda self: self._get_refund_reason(),
    )

    @api.onchange("refund_reason_id")
    def _onchange_refund_reason_id(self):
        self.description = self.refund_reason_id.name

    @api.model
    def _prepare_refund(self, wizard, rma_line):
        values = super(RmaRefund, self)._prepare_refund(wizard, rma_line)
        if rma_line.refund_reason_id:
            values.update(
                {
                    "reason_id": wizard.refund_reason_id.id,
                }
            )
        return values
