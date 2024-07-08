# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RMAOrderLine(models.Model):
    _inherit = "rma.order.line"

    reason_code_ids = fields.Many2many(
        "rma.reason.code",
        "rma_order_line_reason_code_rel",
        string="Reason Code",
        domain="[('id', 'in', allowed_reason_code_ids)]",
    )
    allowed_reason_code_ids = fields.Many2many(
        comodel_name="rma.reason.code",
        compute="_compute_allowed_reason_code_ids",
    )

    @api.depends("type")
    def _compute_allowed_reason_code_ids(self):
        for rec in self:
            codes = self.env["rma.reason.code"]
            if rec.type == "customer":
                codes = codes.search([("type", "in", ["customer", "both"])])
            else:
                codes = codes.search([("type", "in", ["supplier", "both"])])
            rec.allowed_reason_code_ids = codes

    @api.constrains("reason_code_ids", "product_id")
    def _check_reason_code_ids(self):
        for rec in self:
            if rec.reason_code_ids and not any(
                rc in rec.allowed_reason_code_ids for rc in rec.reason_code_ids
            ):
                raise ValidationError(
                    _(
                        "Any of the reason code selected is not allowed for "
                        "this type of RMA (%s)."
                    )
                    % rec.type
                )
