# Copyright (C) 2017-20 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RmaOrder(models.Model):
    _name = "rma.order"
    _description = "RMA Group"
    _inherit = ["mail.thread"]

    @api.model
    def _get_default_type(self):
        if "supplier" in self.env.context:
            return "supplier"
        return "customer"

    def _compute_in_shipment_count(self):
        for rec in self:
            picking_ids = []
            if not rec.rma_line_ids:
                rec.in_shipment_count = 0
                continue
            for line in rec.rma_line_ids:
                for move in line.move_ids:
                    if move.location_dest_id.usage == "internal":
                        picking_ids.append(move.picking_id.id)
                    else:
                        if line.customer_to_supplier:
                            picking_ids.append(move.picking_id.id)
                shipments = list(set(picking_ids))
                rec.in_shipment_count = len(shipments)

    def _compute_out_shipment_count(self):
        picking_ids = []
        for rec in self:
            if not rec.rma_line_ids:
                rec.out_shipment_count = 0
                continue
            for line in rec.rma_line_ids:
                for move in line.move_ids:
                    if move.location_dest_id.usage in ("supplier", "customer"):
                        if not line.customer_to_supplier:
                            picking_ids.append(move.picking_id.id)
                shipments = list(set(picking_ids))
                rec.out_shipment_count = len(shipments)

    def _compute_supplier_line_count(self):
        self.supplier_line_count = len(
            self.rma_line_ids.filtered(lambda r: r.supplier_rma_line_ids)
        )

    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec._get_valid_lines())

    @api.depends("rma_line_ids", "rma_line_ids.state")
    def _compute_state(self):
        for rec in self:
            rma_line_done = self.env["rma.order.line"].search_count(
                [("id", "in", rec.rma_line_ids.ids), ("state", "=", "done")]
            )
            rma_line_approved = self.env["rma.order.line"].search_count(
                [("id", "in", rec.rma_line_ids.ids), ("state", "=", "approved")]
            )
            rma_line_to_approve = self.env["rma.order.line"].search_count(
                [("id", "in", rec.rma_line_ids.ids), ("state", "=", "to_approve")]
            )
            if rma_line_done != 0:
                state = "done"
            elif rma_line_approved != 0:
                state = "approved"
            elif rma_line_to_approve != 0:
                state = "to_approve"
            else:
                state = "draft"
            rec.state = state

    @api.model
    def _default_date_rma(self):
        return datetime.now()

    @api.model
    def _default_warehouse_id(self):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.user.company_id.id)], limit=1
        )
        return warehouse

    name = fields.Char(string="Group Number", index=True, copy=False)
    type = fields.Selection(
        [("customer", "Customer"), ("supplier", "Supplier")],
        string="Type",
        required=True,
        default=lambda self: self._get_default_type(),
        readonly=True,
    )
    reference = fields.Char(
        string="Partner Reference", help="The partner reference of this RMA order."
    )
    comment = fields.Text("Additional Information")
    date_rma = fields.Datetime(
        string="Order Date", index=True, default=lambda self: self._default_date_rma()
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", required=True
    )
    rma_line_ids = fields.One2many("rma.order.line", "rma_id", string="RMA lines")
    in_shipment_count = fields.Integer(
        compute="_compute_in_shipment_count", string="# of Shipments"
    )
    out_shipment_count = fields.Integer(
        compute="_compute_out_shipment_count", string="# of Outgoing Shipments"
    )
    line_count = fields.Integer(compute="_compute_line_count", string="# of RMA lines")
    supplier_line_count = fields.Integer(
        compute="_compute_supplier_line_count", string="# of Supplier RMAs"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    assigned_to = fields.Many2one(
        comodel_name="res.users",
        track_visibility="onchange",
        default=lambda self: self.env.uid,
    )
    requested_by = fields.Many2one(
        comodel_name="res.users",
        track_visibility="onchange",
        default=lambda self: self.env.uid,
    )
    in_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Inbound Warehouse",
        required=True,
        default=_default_warehouse_id,
    )
    customer_to_supplier = fields.Boolean("The customer will send to the supplier")
    supplier_to_customer = fields.Boolean("The supplier will send to the customer")
    supplier_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier Address",
        help="Address of the supplier in case of Customer RMA operation " "dropship.",
    )
    customer_address_id = fields.Many2one(
        comodel_name="res.partner",
        string="Customer Address",
        help="Address of the customer in case of Supplier RMA operation " "dropship.",
    )
    state = fields.Selection(
        compute=_compute_state,
        selection=[
            ("draft", "Draft"),
            ("to_approve", "To Approve"),
            ("approved", "Approved"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
        store=True,
    )

    @api.constrains("partner_id", "rma_line_ids")
    def _check_partner_id(self):
        if self.rma_line_ids and self.partner_id != self.mapped(
            "rma_line_ids.partner_id"
        ):
            raise UserError(_("Group partner and RMA's partner must be the same."))
        if len(self.mapped("rma_line_ids.partner_id")) > 1:
            raise UserError(_("All grouped RMA's should have same partner."))

    @api.model
    def create(self, vals):
        if self.env.context.get("supplier") or vals.get("type") == "supplier":
            vals["name"] = self.env["ir.sequence"].next_by_code("rma.order.supplier")
        else:
            vals["name"] = self.env["ir.sequence"].next_by_code("rma.order.customer")
        return super(RmaOrder, self).create(vals)

    def action_view_in_shipments(self):
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.read()[0]
        picking_ids = []
        for line in self.rma_line_ids:
            for move in line.move_ids:
                if move.location_dest_id.usage == "internal":
                    picking_ids.append(move.picking_id.id)
                else:
                    if line.customer_to_supplier:
                        picking_ids.append(move.picking_id.id)
        if picking_ids:
            shipments = list(set(picking_ids))
            # choose the view_mode accordingly
            if len(shipments) > 1:
                result["domain"] = [("id", "in", shipments)]
            else:
                res = self.env.ref("stock.view_picking_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = shipments[0]
        return result

    def action_view_out_shipments(self):
        action = self.env.ref("stock.action_picking_tree_all")
        result = action.read()[0]
        picking_ids = []
        for line in self.rma_line_ids:
            for move in line.move_ids:
                if move.location_dest_id.usage in ("supplier", "customer"):
                    if not line.customer_to_supplier:
                        picking_ids.append(move.picking_id.id)
        if picking_ids:
            shipments = list(set(picking_ids))
            # choose the view_mode accordingly
            if len(shipments) != 1:
                result["domain"] = [("id", "in", shipments)]
            else:
                res = self.env.ref("stock.view_picking_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = shipments[0]
        return result

    def _get_valid_lines(self):
        """:return: A recordset of rma lines."""
        self.ensure_one()
        return self.rma_line_ids

    def action_view_lines(self):
        if self.type == "customer":
            action = self.env.ref("rma.action_rma_customer_lines")
            res = self.env.ref("rma.view_rma_line_form", False)
        else:
            action = self.env.ref("rma.action_rma_supplier_lines")
            res = self.env.ref("rma.view_rma_line_supplier_form", False)
        result = action.read()[0]
        lines = self._get_valid_lines()
        # choose the view_mode accordingly
        if len(lines.ids) != 1:
            result["domain"] = [("id", "in", lines.ids)]
        else:
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = lines.id
        result["context"] = {}
        return result

    def action_view_supplier_lines(self):
        action = self.env.ref("rma.action_rma_supplier_lines")
        result = action.read()[0]
        lines = self.rma_line_ids
        for line_id in lines:
            related_lines = [line.id for line in line_id.supplier_rma_line_ids]
            # choose the view_mode accordingly
            if len(related_lines) != 1:
                result["domain"] = [("id", "in", related_lines)]
            else:
                res = self.env.ref("rma.view_rma_line_supplier_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = related_lines[0]
        return result

    @api.onchange("in_warehouse_id")
    def _onchange_in_warehouse_id(self):
        if self.in_warehouse_id and self.rma_line_ids:
            self.rma_line_ids.write(
                {
                    "in_warehouse_id": self.in_warehouse_id.id,
                    "location_id": self.in_warehouse_id.lot_rma_id.id,
                }
            )

    @api.onchange("customer_to_supplier", "supplier_address_id")
    def _onchange_customer_to_supplier(self):
        if self.type == "customer" and self.rma_line_ids:
            self.rma_line_ids.write(
                {
                    "customer_to_supplier": self.customer_to_supplier,
                    "supplier_address_id": self.supplier_address_id.id,
                }
            )

    @api.onchange("supplier_to_customer", "customer_address_id")
    def _onchange_supplier_to_customer(self):
        if self.type == "supplier" and self.rma_line_ids:
            self.rma_line_ids.write(
                {
                    "supplier_to_customer": self.supplier_to_customer,
                    "customer_address_id": self.customer_address_id.id,
                }
            )
