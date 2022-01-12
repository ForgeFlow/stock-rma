# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    receipt_policy = fields.Selection(
        selection_add=[
            ("prepaid_invoice_ordered", "Prepaid Service Invoice - Ordered"),
            ("prepaid_invoice_delivered", "Prepaid Service Invoice - Delivered"),
        ],
        ondelete={
            "prepaid_invoice_ordered": lambda recs: recs.write(
                {"receipt_policy": "ordered"}
            ),
            "prepaid_invoice_delivered": lambda recs: recs.write(
                {"receipt_policy": "delivered"}
            ),
        },
    )

    invoice_ids = fields.Many2many(comodel_name="account.move", string="Invoices")

    invoice_count = fields.Integer(
        string="Invoices count",
        compute="_compute_invoice_count",
    )

    @api.depends(
        "invoice_ids",
    )
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    def action_show_invoices(self):
        self.ensure_one()
        action = {}
        if self.type == "customer":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_out_invoice_type"
            )
        elif self.type == "supplier":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_in_invoice_type"
            )
        if len(self.invoice_ids) <= 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = self.invoice_ids.ids[0]
        else:
            domain = safe_eval(action["domain"]) or []
            domain += [("id", "in", self.invoice_ids.ids)]
            action["domain"] = action["domain"]
        return action

    qty_to_receive = fields.Float(
        compute="_compute_qty_to_receive",
        store=True,
    )

    @api.depends(
        "move_ids",
        "move_ids.state",
        "qty_received",
        "receipt_policy",
        "product_qty",
        "type",
        "invoice_ids.payment_state",
    )
    def _compute_qty_to_receive(self):
        for rec in self:
            qty_to_receive = 0.0
            if rec.receipt_policy == "ordered":
                qty_to_receive = rec.product_qty - rec.qty_received
            elif rec.receipt_policy == "delivered":
                qty_to_receive = rec.qty_delivered - rec.qty_received
            elif rec.receipt_policy in (
                "prepaid_invoice_ordered",
                "prepaid_invoice_delivered",
            ):
                not_paid_invoices = rec.invoice_ids.filtered(
                    lambda x: x.payment_state not in ("paid", "in_payment")
                )
                if not (not rec.invoice_ids or not_paid_invoices):
                    if rec.receipt_policy == "prepaid_invoice_ordered":
                        qty_to_receive = rec.product_qty - rec.qty_received
                    if rec.receipt_policy == "prepaid_invoice_delivered":
                        qty_to_receive = rec.qty_delivered - rec.qty_received
            rec.qty_to_receive = qty_to_receive
