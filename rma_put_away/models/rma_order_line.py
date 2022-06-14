from odoo import _, api, fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    qty_to_put_away = fields.Float(
            string="Qty To Put Away",
            digits="Product Unit of Measure",
            compute="_compute_qty_to_put_away",
            store=True,
        )

    qty_put_away = fields.Float(
        string="Qty Put Away",
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_put_away",
        store=True,
        help="Quantity Put Away.",
    )

    put_away_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Put Away Policy",
        default="no",
        required=True,
    )

    def _compute_qty_to_put_away(self):
        for rec in self:
            rec.qty_to_put_away = 0.0
            if rec.put_away_policy == "ordered":
                rec.qty_to_put_away = rec.product_qty - rec.qty_put_away
            elif rec.put_away_policy == "received":
                rec.qty_to_put_away = rec.qty_received - rec.qty_put_away
