# Copyright 2017 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class RmaRefund(models.TransientModel):
    _name = "rma.refund"
    _description = "Wizard for RMA Refund"

    @api.model
    def _get_reason(self):
        active_ids = self.env.context.get("active_ids", False)
        return self.env["rma.order.line"].browse(active_ids[0]).rma_id.name or ""

    @api.returns("rma.order.line")
    def _prepare_item(self, line):
        values = {
            "product_id": line.product_id.id,
            "product": line.product_id.id,
            "name": line.name,
            "product_qty": line.product_qty,
            "uom_id": line.uom_id.id,
            "qty_to_refund": line.qty_to_refund,
            "refund_policy": line.refund_policy,
            "invoice_address_id": line.invoice_address_id.id,
            "line_id": line.id,
            "rma_id": line.rma_id.id,
        }
        return values

    @api.model
    def default_get(self, fields_list):
        """Default values for wizard, if there is more than one supplier on
        lines the supplier field is empty otherwise is the unique line
        supplier.
        """
        context = self._context.copy()
        res = super(RmaRefund, self).default_get(fields_list)
        rma_line_obj = self.env["rma.order.line"]
        rma_line_ids = self.env.context["active_ids"] or []
        active_model = self.env.context["active_model"]
        if not rma_line_ids:
            return res
        assert active_model == "rma.order.line", "Bad context propagation"

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        if len(lines.mapped("partner_id")) > 1:
            raise ValidationError(
                _(
                    "Only RMAs from the same partner can be processed at "
                    "the same time."
                )
            )
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])
        res["item_ids"] = items
        context.update({"items_ids": items})
        return res

    date_invoice = fields.Date(
        string="Refund Date", default=fields.Date.context_today, required=True
    )
    date = fields.Date(
        string="Accounting Date", default=fields.Date.context_today, required=True
    )
    description = fields.Char(
        string="Reason", required=True, default=lambda self: self._get_reason()
    )
    item_ids = fields.One2many(
        comodel_name="rma.refund.item",
        inverse_name="wiz_id",
        string="Items",
        required=True,
    )

    def compute_refund(self):
        for wizard in self:
            first = self.item_ids[0]
            values = self._prepare_refund(wizard, first.line_id)
            new_refund = self.env["account.move"].create(values)
            return new_refund

    def invoice_refund(self):
        rma_line_ids = self.env["rma.order.line"].browse(self.env.context["active_ids"])
        for line in rma_line_ids:
            if line.refund_policy == "no":
                raise ValidationError(
                    _("The operation is not refund for at least one line")
                )
            if line.state != "approved":
                raise ValidationError(_("RMA %s is not approved") % line.name)
        new_invoice = self.compute_refund()
        action = (
            "action_move_out_refund_type"
            if (new_invoice.move_type in ["out_refund", "out_invoice"])
            else "action_move_in_refund_type"
        )
        result = self.env.ref("account.%s" % action).read()[0]
        form_view = self.env.ref("account.move_supplier_form", False)
        result["views"] = [(form_view and form_view.id or False, "form")]
        result["res_id"] = new_invoice.id
        return result

    @api.model
    def prepare_refund_line(self, item):
        accounts = item.product.product_tmpl_id._get_product_accounts()
        if item.line_id.type == "customer":
            account = accounts["stock_output"]
        else:
            account = accounts["stock_input"]
        if not account:
            raise ValidationError(_("Accounts are not configured for this product."))

        values = {
            "name": item.line_id.name or item.rma_id.name,
            "account_id": account.id,
            "price_unit": item.line_id.price_unit,
            "product_uom_id": item.line_id.uom_id.id,
            "product_id": item.product.id,
            "rma_line_id": item.line_id.id,
            "quantity": item.qty_to_refund,
        }
        return values

    @api.model
    def _prepare_refund(self, wizard, rma_line):
        # origin_invoices = self._get_invoice(rma_line)
        if rma_line.type == "customer":
            journal = self.env["account.journal"].search(
                [("type", "=", "sale")], limit=1
            )
        else:
            journal = self.env["account.journal"].search(
                [("type", "=", "purchase")], limit=1
            )
        values = {
            "name": rma_line.rma_id.name or rma_line.name,
            "payment_reference": rma_line.rma_id.name or rma_line.name,
            "invoice_origin": rma_line.rma_id.name or rma_line.name,
            "ref": False,
            "move_type": "in_refund" if rma_line.type == "supplier" else "out_refund",
            "journal_id": journal.id,
            "fiscal_position_id": rma_line.partner_id.property_account_position_id.id,
            "state": "draft",
            "currency_id": rma_line.currency_id.id,
            "date": wizard.date,
            "invoice_date": wizard.date_invoice,
            "partner_id": rma_line.invoice_address_id.id or rma_line.partner_id.id,
            "invoice_line_ids": [
                (0, None, self.prepare_refund_line(item)) for item in self.item_ids
            ],
        }
        if self.env.registry.models.get("crm.team", False):
            team_ids = self.env["crm.team"].search(
                [
                    "|",
                    ("user_id", "=", self.env.uid),
                    ("member_ids", "=", self.env.uid),
                ],
                limit=1,
            )
            team_id = team_ids[0] if team_ids else False
            if team_id:
                values["team_id"] = team_id.id
        if rma_line.type == "customer":
            values["move_type"] = "out_refund"
        else:
            values["move_type"] = "in_refund"
        return values

    @api.constrains("item_ids")
    def check_unique_invoice_address_id(self):
        addresses = self.item_ids.mapped("invoice_address_id")
        if len(addresses) > 1:
            raise ValidationError(
                _("The invoice address must be the same for all the lines.")
            )
        return True


class RmaRefundItem(models.TransientModel):
    _name = "rma.refund.item"
    _description = "RMA Lines to refund"

    wiz_id = fields.Many2one(comodel_name="rma.refund", string="Wizard", required=True)
    line_id = fields.Many2one(
        "rma.order.line",
        string="RMA order Line",
        required=True,
        ondelete="cascade",
    )
    rma_id = fields.Many2one("rma.order", related="line_id.rma_id", string="RMA")
    product_id = fields.Many2one("product.product", string="Product (Technical)")
    product = fields.Many2one("product.product", string="Product", required=True)
    name = fields.Char(string="Description", required=True)
    product_qty = fields.Float(
        string="Quantity Ordered",
        copy=False,
        digits="Product Unit of Measure",
    )
    invoice_address_id = fields.Many2one(
        comodel_name="res.partner", string="Invoice Address"
    )
    qty_to_refund = fields.Float(
        string="Quantity To Refund", digits="Product Unit of Measure"
    )
    uom_id = fields.Many2one("uom.uom", string="Unit of Measure")
    refund_policy = fields.Selection(
        selection=[
            ("no", "Not required"),
            ("ordered", "Based on Ordered Quantities"),
            ("received", "Based on Received Quantities"),
        ],
        string="Refund Policy",
    )
