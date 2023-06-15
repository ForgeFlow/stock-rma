# Copyright (C) 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class RmaRefund(models.TransientModel):

    _inherit = "rma.refund"

    @api.model
    def _prepare_refund(self, wizard, rma_line):
        values = super(RmaRefund, self)._prepare_refund(wizard, rma_line)
        if rma_line.refund_reason_id:
            values.update(
                {
                    "reason_id": rma_line.refund_reason_id.id,
                }
            )
        return values
