# Copyright 2017 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    @api.model
    def _default_invoice_address(self):
        partner_id = self.env.context.get("partner_id")
        if partner_id:
            return self.env["res.partner"].browse(partner_id)
        return self.env["res.partner"]

    @api.depends(
        "refund_line_ids", "refund_line_ids.move_id.state", "refund_policy", "type"
    )
    def _compute_qty_refunded(self):
        for rec in self:
            rec.qty_refunded = sum(
                rec.refund_line_ids.filtered(
                    lambda i: i.move_id.state in ("posted")
                ).mapped("quantity")
            )

    @api.depends(
        "refund_line_ids",
        "refund_line_ids.move_id.state",
        "refund_policy",
        "move_ids",
        "move_ids.state",
        "type",
    )
    def _compute_qty_to_refund(self):
        qty = 0.0
        for res in self:
            if res.refund_policy == "ordered":
                qty = res.product_qty - res.qty_refunded
            elif res.refund_policy == "received":
                qty = res.qty_received - res.qty_refunded
            elif res.refund_policy == "delivered":
                qty = res.qty_delivered - res.qty_refunded
            res.qty_to_refund = qty

    def _compute_refund_count(self):
        for rec in self:
            rec.refund_count = len(rec.refund_line_ids.mapped("move_id"))

    invoice_address_id = fields.Many2one(
        "res.partner",
        string="Partner invoice address",
        default=lambda self: self._default_invoice_address(),
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Invoice address for current rma order.",
    )
    refund_count = fields.Integer(
        compute="_compute_refund_count", string="# of Refunds", default=0
    )
    account_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Originating Invoice Line",
        ondelete="restrict",
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    refund_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="rma_line_id",
        string="Refund Lines",
        copy=False,
        index=True,
        readonly=True,
    )
    move_id = fields.Many2one(
        "account.move",
        string="Source",
        related="account_move_line_id.move_id",
        index=True,
        readonly=True,
    )
    refund_policy = fields.Selection(
        [
            ("no", "No refund"),
            ("ordered", "Based on Ordered Quantities"),
            ("delivered", "Based on Delivered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Refund Policy",
        required=True,
        default="no",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    qty_to_refund = fields.Float(
        string="Qty To Refund",
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_to_refund",
        store=True,
    )
    qty_refunded = fields.Float(
        string="Qty Refunded",
        copy=False,
        digits="Product Unit of Measure",
        readonly=True,
        compute="_compute_qty_refunded",
        store=True,
    )

    @api.onchange("product_id", "partner_id")
    def _onchange_product_id(self):
        """Domain for sale_line_id is computed here to make it dynamic."""
        res = super(RmaOrderLine, self)._onchange_product_id()
        if not res.get("domain"):
            res["domain"] = {}
        if not self.product_id:
            domain = [
                "&",
                "|",
                ("move_id.partner_id", "=", self.partner_id.id),
                ("move_id.partner_id", "child_of", self.partner_id.id),
                ("exclude_from_invoice_tab", "=", False),
            ]
            res["domain"]["account_move_line_id"] = domain
        else:
            domain = [
                "&",
                "&",
                "|",
                ("move_id.partner_id", "=", self.partner_id.id),
                ("move_id.partner_id", "child_of", self.partner_id.id),
                ("exclude_from_invoice_tab", "=", False),
                ("product_id", "=", self.product_id.id),
            ]
            res["domain"]["account_move_line_id"] = domain
        return res

    def _prepare_rma_line_from_inv_line(self, line):
        self.ensure_one()
        if not self.type:
            self.type = self._get_default_type()
        if self.type == "customer":
            operation = (
                line.product_id.rma_customer_operation_id
                or line.product_id.categ_id.rma_customer_operation_id
            )
        else:
            operation = (
                line.product_id.rma_supplier_operation_id
                or line.product_id.categ_id.rma_supplier_operation_id
            )
        if not operation:
            operation = self.env["rma.operation"].search(
                [("type", "=", self.type)], limit=1
            )
            if not operation:
                raise ValidationError(_("Please define an operation first"))

        if not operation.in_route_id or not operation.out_route_id:
            route = self.env["stock.location.route"].search(
                [("rma_selectable", "=", True)], limit=1
            )
            if not route:
                raise ValidationError(_("Please define an rma route"))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env["stock.warehouse"].search(
                [("company_id", "=", self.company_id.id), ("lot_rma_id", "!=", False)],
                limit=1,
            )
            if not warehouse:
                raise ValidationError(
                    _("Please define a warehouse with a" " default rma location")
                )
        data = {
            "product_id": line.product_id.id,
            "origin": line.move_id.name,
            "uom_id": line.product_uom_id.id,
            "operation_id": operation.id,
            "product_qty": line.quantity,
            "price_unit": line.move_id.currency_id._convert(
                line.price_unit,
                line.currency_id,
                line.company_id,
                line.date,
                round=False,
            ),
            "delivery_address_id": line.move_id.partner_id.id,
            "invoice_address_id": line.move_id.partner_id.id,
            "receipt_policy": operation.receipt_policy,
            "refund_policy": operation.refund_policy,
            "delivery_policy": operation.delivery_policy,
            "currency_id": line.currency_id.id,
            "in_warehouse_id": operation.in_warehouse_id.id or warehouse.id,
            "out_warehouse_id": operation.out_warehouse_id.id or warehouse.id,
            "in_route_id": operation.in_route_id.id or route.id,
            "out_route_id": operation.out_route_id.id or route.id,
            "location_id": (
                operation.location_id.id
                or operation.in_warehouse_id.lot_rma_id.id
                or warehouse.lot_rma_id.id
            ),
        }
        return data

    @api.onchange("account_move_line_id")
    def _onchange_account_move_line_id(self):
        if not self.account_move_line_id:
            return
        data = self._prepare_rma_line_from_inv_line(self.account_move_line_id)
        self.update(data)
        self._remove_other_data_origin("account_move_line_id")

    @api.constrains("account_move_line_id", "partner_id")
    def _check_invoice_partner(self):
        for rec in self:
            if (
                rec.account_move_line_id
                and rec.account_move_line_id.move_id.partner_id != rec.partner_id
            ):
                raise ValidationError(
                    _(
                        "RMA customer and originating invoice line customer "
                        "doesn't match."
                    )
                )

    def _remove_other_data_origin(self, exception):
        res = super(RmaOrderLine, self)._remove_other_data_origin(exception)
        if not exception == "account_move_line_id":
            self.account_move_line_id = False
        return res

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        result = super(RmaOrderLine, self)._onchange_operation_id()
        if self.operation_id:
            self.refund_policy = self.operation_id.refund_policy or "no"
        return result

    @api.constrains("account_move_line_id")
    def _check_duplicated_lines(self):
        for line in self:
            matching_inv_lines = self.env["account.move.line"].search(
                [("id", "=", line.account_move_line_id.id)]
            )
            if len(matching_inv_lines) > 1:
                raise UserError(
                    _(
                        "There's an rma for the invoice line %s "
                        "and invoice %s"
                        % (line.account_move_line_id, line.account_move_line_id.move_id)
                    )
                )
        return {}

    def action_view_invoice(self):
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)

        return {
            "domain": [("id", "in", [self.account_move_line_id.move_id.id])],
            "name": "Originating Invoice",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }

    def action_view_refunds(self):
        move_ids = self.mapped("refund_line_ids.move_id").ids
        form_view_ref = self.env.ref("account.view_move_form", False)
        tree_view_ref = self.env.ref("account.view_move_tree", False)

        return {
            "domain": [("id", "in", move_ids)],
            "name": "Refunds",
            "res_model": "account.move",
            "type": "ir.actions.act_window",
            "views": [(tree_view_ref.id, "tree"), (form_view_ref.id, "form")],
        }

    def name_get(self):
        res = []
        if self.env.context.get("rma"):
            for rma in self:
                res.append(
                    (
                        rma.id,
                        "%s %s qty:%s"
                        % (rma.name, rma.product_id.name, rma.product_qty),
                    )
                )
            return res
        else:
            return super(RmaOrderLine, self).name_get()
