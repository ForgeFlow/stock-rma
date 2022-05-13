# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOperation(models.Model):
    _inherit = "rma.operation"

    refund_policy = fields.Selection(
        [
            ("no", "No refund"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        default="no",
    )

    refund_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Refund Account Journal",
        domain="[('id', 'in', valid_refund_journal_ids)]",
    )

    valid_refund_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        compute="_compute_domain_valid_journal",
    )

    @api.onchange("type")
    def _compute_domain_valid_journal(self):
        for rec in self:
            if rec.type == "customer":
                rec.valid_refund_journal_ids = self.env["account.journal"].search(
                    [("type", "=", "sale")]
                )
            else:
                rec.valid_refund_journal_ids = self.env["account.journal"].search(
                    [("type", "=", "purchase")]
                )
