from odoo import _, api, fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    picking_ids = fields.One2many(
        comodel_name="stock.picking",
        inverse_name="rma_line_id",
        string="Pickings",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )

    qty_to_put_away = fields.Float(
            string="Qty To Put Away",
            digits="Product Unit of Measure",
            compute="_compute_qty_to_put_away",
            store=True,
        )

    qty_put_away = fields.Float(
        string="Qty Put Away",
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

    @api.depends("qty_to_receive", "qty_put_away")
    def _compute_qty_to_put_away(self):
        self.qty_to_put_away = 0.0
        if self.put_away_policy == "ordered":
            self.qty_to_put_away = max(self.product_qty - self.qty_put_away, 0)
        elif self.put_away_policy == "received":
            self.qty_to_put_away = max(self.qty_received - self.qty_put_away, 0)

    @api.depends("qty_to_receive")
    def _compute_qty_put_away(self):
        self.qty_put_away = 0.0
        for pick in self.picking_ids.filtered(lambda p: p.state == "done"):
            repair_qty = self.uom_id._compute_quantity(
                pick.product_qty, pick.product_uom
            )
            self.qty_put_away += repair_qty
        return self.qty_put_away

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.put_away_policy = self.operation_id.put_away_policy or "no"
        return result

