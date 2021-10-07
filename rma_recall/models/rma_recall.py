# Copyright (C) 2021 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models


class RmaRecall(models.Model):
    _name = "rma.recall"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "RMA Recall"

    name = fields.Char(
        "Name",
        required=True,
        copy=False,
        readonly=True,
        states={"new": [("readonly", False)]},
        default=lambda self: _("New"),
    )
    lot_id = fields.Many2one(
        "stock.production.lot",
        "Lot/Serial",
        required=True,
        index=True,
        states={"new": [("readonly", False)]},
    )
    product_id = fields.Many2one(
        related="lot_id.product_id", string="Product", store=True
    )
    rma_date = fields.Date("Date", default=fields.Date.today())
    origin = fields.Char("Origin", copy=False, states={"new": [("readonly", False)]})
    state = fields.Selection(
        [
            ("new", "New"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        readonly=True,
        index=True,
        copy=False,
        default="new",
        tracking=True,
    )
    line_ids = fields.One2many("rma.recall.line", "recall_id", "Lines", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("rma.recall") or _(
                "New"
            )
        return super().create(vals)

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == "tracking" or super()._valid_field_parameter(field, name)

    def _prepare_recall_line(self, line, recall_lines=[]):
        TraceabilityReport = self.env["stock.traceability.report"]
        vals = {}
        move_line = self.env[line.get("model")].browse(line.get("model_id"))
        if line.get("usage") == "out" and not line.get("is_used"):
            if line.get("res_model") == "stock.picking":
                picking = self.env[line.get("res_model")].browse(line.get("res_id"))
                vals = {
                    "location_id": move_line.location_dest_id.id,
                    "partner_id": picking and picking.partner_id.id or False,
                    "picking_id": line.get("res_id"),
                    "product_id": move_line.product_id.id,
                    "qty": move_line.qty_done,
                    "uom_id": move_line.product_uom_id.id
                    or move_line.product_id.uom_id.id,
                }
                recall_lines.append((0, 0, vals))
            elif line.get("res_model") == "stock.scrap":
                scrap_order = self.env[line.get("res_model")].browse(line.get("res_id"))
                vals = {
                    "location_id": scrap_order.scrap_location_id.id,
                    "scrap_id": line.get("res_id"),
                    "product_id": move_line.product_id.id,
                    "qty": move_line.qty_done,
                    "uom_id": move_line.product_uom_id.id
                    or move_line.product_id.uom_id.id,
                }
                recall_lines.append((0, 0, vals))
        elif line.get("usage") == "in" and not line.get("is_used"):
            if move_line.location_dest_id.usage == "internal":
                vals = {
                    "location_id": move_line.location_dest_id.id,
                    "product_id": move_line.product_id.id,
                    "qty": move_line.lot_id.product_qty,
                    "uom_id": move_line.product_uom_id.id
                    or move_line.product_id.uom_id.id,
                }
                recall_lines.append((0, 0, vals))
        elif line.get("usage") == "out" and line.get("is_used"):
            res_record = self.env[line.get("res_model")].browse(line.get("res_id"))
            if line.get("res_model") == "mrp.production":
                if res_record.lot_producing_id:
                    lines = TraceabilityReport.with_context(
                        model=res_record.lot_producing_id._name,
                        active_id=res_record.lot_producing_id.id,
                    ).get_lines()
                    for mol in lines:
                        self._prepare_recall_line(mol, recall_lines=recall_lines)
        return recall_lines

    def action_search(self):
        TraceabilityReport = self.env["stock.traceability.report"]
        for rec in self:
            lines = TraceabilityReport.with_context(
                model=rec.lot_id._name, active_id=rec.lot_id.id
            ).get_lines()
            recall_lines = []
            for line in lines:
                recall_lines = rec._prepare_recall_line(line, recall_lines=recall_lines)
            rec.write(
                {
                    "line_ids": recall_lines,
                    "state": "in_progress",
                }
            )

    def action_done(self):
        self.write({"state": "done"})

    def action_cancel(self):
        self.write({"state": "cancelled"})


class RmaRecallLine(models.Model):
    _name = "rma.recall.line"
    _description = "RMA Recall Lines"

    def _compute_state(self):
        for rec in self:
            state_value = False
            if rec.scrap_id:
                state_value = dict(rec.scrap_id._fields["state"].selection).get(
                    rec.scrap_id.state
                )
            elif rec.rma_id:
                state_value = dict(rec.rma_id._fields["state"].selection).get(
                    rec.rma_id.state
                )
            rec.state = state_value

    location_id = fields.Many2one("stock.location", "Inventory Location")
    recall_id = fields.Many2one(
        "rma.recall", "Recall", required=True, ondelete="cascade"
    )
    partner_id = fields.Many2one("res.partner", "Contact")
    rma_id = fields.Many2one("rma.order.line", "RMA")
    scrap_id = fields.Many2one("stock.scrap", "Scrap")
    picking_id = fields.Many2one("stock.picking", "Transfer")
    product_id = fields.Many2one("product.product", "Product")
    qty = fields.Float("Quantity")
    uom_id = fields.Many2one(related="product_id.uom_id", string="UoM")
    state = fields.Char("State", compute="_compute_state")

    def button_rma_order(self):
        RmaOrderLine = self.env["rma.order.line"]
        for rec in self:
            if not rec.rma_id and rec.partner_id:
                partner_type = "customer"
                operation = self.env.ref("rma.rma_operation_customer_replace")
                if rec.picking_id.picking_type_code == "incoming":
                    partner_type = "supplier"
                    operation = self.env.ref("rma.rma_operation_supplier_replace")
                vals = {
                    "partner_id": rec.partner_id.id,
                    "product_id": rec.product_id.id,
                    "lot_id": rec.recall_id.lot_id.id,
                    "type": partner_type,
                    "operation_id": operation.id,
                    "origin": rec.recall_id.name,
                    'product_qty': rec.qty
                }
                rma_order_line_new = RmaOrderLine.new(vals)
                vals.update(rma_order_line_new.default_get(rma_order_line_new._fields))
                rma_order_line_new._onchange_operation_id()
                rma_order_line_new._onchange_product_id()
                vals.update(
                    rma_order_line_new.sudo()._convert_to_write(
                        {
                            name: rma_order_line_new[name]
                            for name in rma_order_line_new._cache
                        }
                    )
                )
                vals.update({"operation_id": operation.id})
                rma_line = RmaOrderLine.create(vals)
                rec.rma_id = rma_line.id

    def button_scrap_order(self):
        StockScrap = self.env["stock.scrap"]
        for rec in self:
            if not rec.scrap_id:
                vals = {"product_id": rec.product_id.id}
                new_scrap_order_new = StockScrap.new(vals)
                vals.update(
                    new_scrap_order_new.default_get(new_scrap_order_new._fields)
                )
                new_scrap_order_new._onchange_product_id()
                vals.update(
                    new_scrap_order_new.sudo()._convert_to_write(
                        {
                            name: new_scrap_order_new[name]
                            for name in new_scrap_order_new._cache
                        }
                    )
                )
                vals.update(
                    {
                        "lot_id": rec.recall_id.lot_id.id,
                        "location_id": rec.location_id.id,
                        "origin": rec.recall_id.name,
                        "scrap_qty": rec.qty,
                    }
                )
                scrap_order = StockScrap.create(vals)
                rec.scrap_id = scrap_order.id
