# Copyright (C) 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    rma_id = fields.Many2one(
        comodel_name="rma.order", string="RMA", ondelete="set null"
    )
    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA line", ondelete="set null"
    )

    @api.model
    def _get_rule(self, product_id, location_id, values):
        """Ensure that the selected rule is from the configured route"""
        res = super()._get_rule(product_id, location_id, values)
        force_rule_ids = self.env.context.get("rma_force_rule_ids")
        if force_rule_ids:
            if res and res.id not in force_rule_ids:
                raise ValidationError(
                    _(
                        "No rule found in this RMA's configured route for product "
                        "%(product)s and location %(location)s"
                    )
                    % {
                        "product": product_id.default_code or product_id.name,
                        "location": location_id.complete_name,
                    }
                )
            # Don't enforce rules on any chained moves
            force_rule_ids.clear()
        return res
