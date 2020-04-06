# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.depends("repair_ids", "repair_type", "repair_ids.state", "qty_to_receive")
    def _compute_qty_to_repair(self):
        for line in self:
            if line.repair_type == "no":
                line.qty_to_repair = 0.0
            elif line.repair_type == "ordered":
                qty = line._get_rma_repaired_qty() + line._get_rma_under_repair_qty()
                line.qty_to_repair = line.product_qty - qty
            elif line.repair_type == "received":
                qty = line._get_rma_repaired_qty() + line._get_rma_under_repair_qty()
                line.qty_to_repair = line.qty_received - qty
            else:
                line.qty_to_repair = 0.0

    @api.depends("repair_ids", "repair_type", "repair_ids.state", "qty_to_receive")
    def _compute_qty_repaired(self):
        for line in self:
            line.qty_repaired = line._get_rma_repaired_qty()

    @api.depends("repair_ids", "repair_type", "repair_ids.state", "qty_to_receive")
    def _compute_qty_under_repair(self):
        for line in self:
            line.qty_under_repair = line._get_rma_under_repair_qty()

    @api.depends("repair_ids")
    def _compute_repair_count(self):
        for line in self:
            line.repair_count = len(line.repair_ids)

    repair_ids = fields.One2many(
        comodel_name="repair.order",
        inverse_name="rma_line_id",
        string="Repair Orders",
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
    )
    qty_to_repair = fields.Float(
        string="Qty To Repair",
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_to_repair",
        store=True,
    )
    qty_under_repair = fields.Float(
        string="Qty Under Repair",
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_under_repair",
        store=True,
    )
    qty_repaired = fields.Float(
        string="Qty Repaired",
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_repaired",
        store=True,
        help="Quantity repaired or being repaired.",
    )
    repair_type = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Repair Policy",
        default="no",
        required=True,
    )
    repair_count = fields.Integer(
        compute="_compute_repair_count", string="# of Repairs"
    )

    delivery_policy = fields.Selection(
        selection_add=[("repair", "Based on Repair Quantities")]
    )
    qty_to_pay = fields.Float(compute="_compute_qty_to_pay")
    qty_to_deliver = fields.Float(compute="_compute_qty_to_deliver")

    @api.depends(
        "delivery_policy",
        "product_qty",
        "type",
        "repair_ids",
        "repair_ids.state",
        "repair_ids.invoice_method",
        "repair_type",
        "repair_ids.invoice_status",
    )
    def _compute_qty_to_pay(self):
        for rec in self.filtered(lambda l: l.delivery_policy == "repair"):
            qty_to_pay = 0.0
            for repair in rec.repair_ids.filtered(
                lambda r: r.invoice_method != "none" and r.invoice_status != "posted"
            ):
                qty_to_pay += repair.product_qty
            rec.qty_to_pay = qty_to_pay

    def action_view_repair_order(self):
        action = self.env.ref("repair.action_repair_order_tree")
        result = action.read()[0]
        repair_ids = self.repair_ids.ids
        if len(repair_ids) != 1:
            result["domain"] = [("id", "in", repair_ids)]
        elif len(repair_ids) == 1:
            res = self.env.ref("repair.view_repair_order_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = repair_ids[0]
        return result

    def _get_rma_repaired_qty(self):
        self.ensure_one()
        qty = 0.0
        for repair in self.repair_ids.filtered(lambda p: p.state == "done"):
            repair_qty = self.uom_id._compute_quantity(
                repair.product_qty, repair.product_uom
            )
            qty += repair_qty
        return qty

    def _get_rma_under_repair_qty(self):
        self.ensure_one()
        qty = 0.0
        for repair in self.repair_ids.filtered(
            lambda p: p.state not in ("draft", "cancel", "done")
        ):
            repair_qty = self.uom_id._compute_quantity(
                repair.product_qty, repair.product_uom
            )
            qty += repair_qty
        return qty

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.repair_type = self.operation_id.repair_type or "no"
        return result

    @api.depends(
        "move_ids",
        "move_ids.state",
        "delivery_policy",
        "product_qty",
        "type",
        "qty_delivered",
        "qty_received",
        "repair_ids",
        "repair_type",
        "repair_ids.state",
        "qty_to_pay",
        "repair_ids.invoice_status",
    )
    def _compute_qty_to_deliver(self):
        res = super(RmaOrderLine, self)._compute_qty_to_deliver()
        for rec in self.filtered(lambda l: l.delivery_policy == "repair"):
            rec.qty_to_deliver = rec.qty_repaired - rec.qty_delivered
        return res
