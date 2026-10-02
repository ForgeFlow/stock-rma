# Copyright (C) 2021 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class RmaRecall(models.Model):
    _name = "rma.recall"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "RMA Recall"

    name = fields.Char(
        string="Name",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    lot_id = fields.Many2one(
        comodel_name="stock.lot",
        string="Lot/Serial",
        required=True,
        index=True,
    )
    product_id = fields.Many2one(
        related="lot_id.product_id", string="Product", store=True
    )
    rma_date = fields.Date(string="Date", default=fields.Date.context_today)
    origin = fields.Char(string="Origin", copy=False)
    state = fields.Selection(
        selection=[
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
    line_ids = fields.One2many(
        comodel_name="rma.recall.line",
        inverse_name="recall_id",
        string="Lines",
        readonly=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("rma.recall") or _(
                    "New"
                )
        return super().create(vals_list)

    def _product_uom_qty(self, move_line):
        """Quantity of a done move line, in the product's unit of measure."""
        uom = move_line.product_uom_id or move_line.product_id.uom_id
        return uom._compute_quantity(move_line.quantity, move_line.product_id.uom_id)

    def _collect_outgoing_move_line(self, move_line, picking, groups):
        """Group done delivery lines by move and lot."""
        key = (move_line.move_id.id, move_line.lot_id.id)
        group = groups.get(key)
        if group:
            group["lines"] |= move_line
            return
        groups[key] = {
            "lines": move_line,
            "picking": picking,
            "location": move_line.location_dest_id,
        }

    def _recall_lines_from_outgoing_groups(self, groups):
        """One recall line per move and lot, with returns subtracted once."""
        lines = []
        for group in groups.values():
            product = group["lines"].product_id
            product_uom = product.uom_id
            delivered = sum(self._product_uom_qty(line) for line in group["lines"])
            returned = 0.0
            returned_moves = group["lines"].move_id.returned_move_ids.filtered(
                lambda move: move.state == "done"
            )
            lot = group["lines"].lot_id
            for returned_move in returned_moves:
                returned_lines = returned_move.move_line_ids.filtered(
                    lambda line: line.lot_id == lot and line.state == "done"
                )
                for returned_line in returned_lines:
                    returned_uom = returned_line.product_uom_id or product_uom
                    returned += returned_uom._compute_quantity(
                        returned_line.quantity, product_uom
                    )
            qty = delivered - returned
            if float_compare(qty, 0.0, precision_rounding=product_uom.rounding) <= 0:
                continue
            picking = group["picking"]
            lines.append(
                (
                    0,
                    0,
                    {
                        "location_id": group["location"].id,
                        "product_id": product.id,
                        "lot_id": lot.id,
                        "qty": qty,
                        "partner_id": picking.partner_id.id,
                        "picking_id": picking.id,
                    },
                )
            )
        return lines

    def _move_line_qty_vals(self, move_line, location, qty=None):
        return {
            "location_id": location.id,
            "product_id": move_line.product_id.id,
            "lot_id": move_line.lot_id.id,
            "qty": self._product_uom_qty(move_line) if qty is None else qty,
        }

    def _prepare_quant_lines(self, lots):
        """On-hand stock of the affected lots, one line per internal location."""
        quants = self.env["stock.quant"].search(
            [
                ("lot_id", "in", lots.ids),
                ("location_id.usage", "=", "internal"),
            ]
        )
        grouped = {}
        for quant in quants:
            key = (quant.lot_id.id, quant.location_id.id, quant.product_id.id)
            grouped[key] = grouped.get(key, 0.0) + quant.quantity
        lines = []
        for (lot_id, location_id, product_id), qty in grouped.items():
            product = self.env["product.product"].browse(product_id)
            rounding = product.uom_id.rounding
            if float_compare(qty, 0.0, precision_rounding=rounding) <= 0:
                continue
            lines.append(
                (
                    0,
                    0,
                    {
                        "location_id": location_id,
                        "product_id": product_id,
                        "lot_id": lot_id,
                        "qty": qty,
                    },
                )
            )
        return lines

    def _prepare_recall_line(
        self,
        line,
        recall_lines=False,
        visited_lots=None,
        affected_lots=None,
        outgoing_groups=None,
    ):
        # An empty list is a real accumulator. Only start a new one when the
        # caller did not pass one, so recursive calls keep the same list.
        if recall_lines is False:
            recall_lines = []
        if visited_lots is None:
            visited_lots = set()
        if affected_lots is None:
            affected_lots = self.env["stock.lot"]
        if outgoing_groups is None:
            outgoing_groups = {}
        move_line = self.env[line.get("model")].browse(line.get("model_id"))
        if line.get("usage") == "out" and not line.get("is_used"):
            if line.get("res_model") == "stock.picking":
                picking = self.env["stock.picking"].browse(line.get("res_id"))
                self._collect_outgoing_move_line(move_line, picking, outgoing_groups)
            elif line.get("res_model") == "stock.scrap":
                scrap_order = self.env["stock.scrap"].browse(line.get("res_id"))
                vals = self._move_line_qty_vals(
                    move_line, scrap_order.scrap_location_id
                )
                vals["scrap_id"] = scrap_order.id
                recall_lines.append((0, 0, vals))
        elif (
            line.get("usage") == "out"
            and line.get("is_used")
            and line.get("res_model") == "mrp.production"
        ):
            production = self.env["mrp.production"].browse(line.get("res_id"))
            report = self.env["stock.traceability.report"]
            for lot in production.lot_producing_ids:
                if lot.id in visited_lots:
                    continue
                visited_lots.add(lot.id)
                affected_lots |= lot
                produced_lines = report.with_context(
                    model=lot._name,
                    active_id=lot.id,
                ).get_lines()
                for produced_line in produced_lines:
                    recall_lines, affected_lots = self._prepare_recall_line(
                        produced_line,
                        recall_lines=recall_lines,
                        visited_lots=visited_lots,
                        affected_lots=affected_lots,
                        outgoing_groups=outgoing_groups,
                    )
        return recall_lines, affected_lots

    def action_search(self):
        for rec in self:
            if any(line.rma_id or line.scrap_id for line in rec.line_ids):
                raise UserError(
                    _(
                        "Cannot repeat the search while linked RMA or "
                        "scrap orders exist."
                    )
                )
        report = self.env["stock.traceability.report"]
        for rec in self:
            visited_lots = {rec.lot_id.id}
            affected_lots = rec.lot_id
            outgoing_groups = {}
            lines = report.with_context(
                model=rec.lot_id._name, active_id=rec.lot_id.id
            ).get_lines()
            recall_lines = []
            for line in lines:
                recall_lines, affected_lots = rec._prepare_recall_line(
                    line,
                    recall_lines=recall_lines,
                    visited_lots=visited_lots,
                    affected_lots=affected_lots,
                    outgoing_groups=outgoing_groups,
                )
            recall_lines.extend(rec._recall_lines_from_outgoing_groups(outgoing_groups))
            recall_lines.extend(rec._prepare_quant_lines(affected_lots))
            rec.write(
                {
                    "line_ids": [(5, 0, 0), *recall_lines],
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

    location_id = fields.Many2one(
        comodel_name="stock.location", string="Inventory Location"
    )
    recall_id = fields.Many2one(
        comodel_name="rma.recall",
        string="Recall",
        required=True,
        ondelete="cascade",
    )
    partner_id = fields.Many2one(comodel_name="res.partner", string="Contact")
    rma_id = fields.Many2one(comodel_name="rma.order.line", string="RMA")
    scrap_id = fields.Many2one(comodel_name="stock.scrap", string="Scrap")
    picking_id = fields.Many2one(comodel_name="stock.picking", string="Transfer")
    product_id = fields.Many2one(comodel_name="product.product", string="Product")
    lot_id = fields.Many2one(comodel_name="stock.lot", string="Lot/Serial")
    qty = fields.Float(string="Quantity")
    uom_id = fields.Many2one(related="product_id.uom_id", string="UoM")
    state = fields.Char(string="State", compute="_compute_state")

    @api.depends("scrap_id", "scrap_id.state", "rma_id", "rma_id.state")
    def _compute_state(self):
        for rec in self:
            record = rec.scrap_id or rec.rma_id
            if record:
                selection = dict(
                    record._fields["state"]._description_selection(rec.env)
                )
                rec.state = selection.get(record.state)
            else:
                rec.state = False

    def _recall_company(self):
        self.ensure_one()
        return (
            self.picking_id.company_id
            or self.location_id.company_id
            or self.env.company
        )

    def button_rma_order(self):
        rma_line_model = self.env["rma.order.line"]
        for rec in self:
            if rec.rma_id or not rec.partner_id:
                continue
            partner_type = "customer"
            operation = self.env.ref("rma.rma_operation_customer_replace")
            if rec.picking_id.picking_type_code == "incoming":
                partner_type = "supplier"
                operation = self.env.ref("rma.rma_operation_supplier_replace")
            company = rec._recall_company()
            defaults = rma_line_model.with_company(company).default_get(
                list(rma_line_model._fields)
            )
            vals = {
                **defaults,
                "partner_id": rec.partner_id.id,
                "product_id": rec.product_id.id,
                "lot_id": rec.lot_id.id,
                "company_id": company.id,
                "origin": rec.recall_id.name,
                "product_qty": rec.qty,
                "type": partner_type,
            }
            rma_line = rma_line_model.new(vals)
            rma_line._onchange_product_id()
            rma_line.operation_id = operation
            rma_line._onchange_operation_id()
            rma_line.lot_id = rec.lot_id
            rma_line.product_qty = rec.qty
            rma_line.type = partner_type
            rma_line.origin = rec.recall_id.name
            create_vals = rma_line.sudo()._convert_to_write(
                {name: rma_line[name] for name in rma_line._cache}
            )
            create_vals.update(
                {
                    "partner_id": rec.partner_id.id,
                    "product_id": rec.product_id.id,
                    "lot_id": rec.lot_id.id,
                    "type": partner_type,
                    "operation_id": operation.id,
                    "origin": rec.recall_id.name,
                    "product_qty": rec.qty,
                    "company_id": company.id,
                }
            )
            rec.rma_id = rma_line_model.create(create_vals).id

    def button_scrap_order(self):
        for rec in self:
            if rec.scrap_id:
                continue
            company = rec._recall_company()
            scrap_order = (
                self.env["stock.scrap"]
                .with_company(company)
                .create(
                    {
                        "product_id": rec.product_id.id,
                        "lot_id": rec.lot_id.id,
                        "origin": rec.recall_id.name,
                        "company_id": company.id,
                    }
                )
            )
            # location and quantity are computed; set them after create.
            scrap_order.write(
                {
                    "location_id": rec.location_id.id,
                    "scrap_qty": rec.qty,
                }
            )
            rec.scrap_id = scrap_order.id
