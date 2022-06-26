from odoo import api, fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    put_away_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="put_away Policy",
        default="no",
        required=True,
    )

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.put_away_policy = self.operation_id.put_away_policy or "no"
        return result
