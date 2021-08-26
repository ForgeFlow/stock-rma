# Copyright (C) 2021 Open Source Integrators (https://www.opensourceintegrators.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    product_id = fields.Many2one("product.product", "Product", readonly=True)
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

    @api.onchange("lot_id")
    def _onchange_lot_number(self):
        self.product_id = self.lot_id.product_id

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

    def action_search(self):
        MoveLine = self.env["stock.move.line"]
        TraceabilityReport = self.env["stock.traceability.report"]
        for rec in self:
            lines = MoveLine.search(
                [
                    ("lot_id", "=", rec.lot_id.id),
                    ("state", "=", "done"),
                ]
            )
            recall_lines = []
            stock_locations = lines.mapped("location_dest_id")
            for stock_location in stock_locations:
                for move_line in lines.filtered(
                    lambda l: l.location_dest_id == stock_location
                )[-1]:
                    res_model, res_id, ref = TraceabilityReport._get_reference(
                        move_line
                    )
                    picking = False
                    if res_model == "stock.picking":
                        picking = self.env[res_model].browse(res_id)
                    vals = {
                        "location_id": stock_location.id,
                        "partner_id": picking and picking.partner_id.id or False,
                        "picking_id": res_id,
                        "product_id": move_line.product_id.id,
                        "qty": move_line.qty_done,
                        "uom_id": move_line.product_uom_id.id
                        or move_line.product_id.uom_id.id,
                    }
                    recall_lines.append((0, 0, vals))
            rec.line_ids = recall_lines
            rec.state = "in_progress"


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
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    state = fields.Char("State", compute="_compute_state")

    @api.onchange("product_id")
    def _onchange_product(self):
        self.uom_id = self.product_id.uom_id

    def button_rma_order(self):
        # Todo: need to create RMA
        pass

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
