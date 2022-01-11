# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class RmaOrderLine(models.Model):

    _inherit = "rma.order.line"

    invoice_policy = fields.Selection(
        string="Invoice policy",
        selection=[
            ("no", "No Service Invoice"),
            ("yes", "Create Service Invoice"),
        ],
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

    def _prepare_rma_line_from_stock_move(self, sm, lot=False):
        operation_model = self.env["rma.operation"]
        res = super()._prepare_rma_line_from_stock_move()
        if res.get("operation_id", False):
            operation = operation_model.browse(res.get("operation_id", False))
            res.update(
                {
                    "invoice_policy": operation.invoice_policy,
                }
            )
        return res

    @api.onchange("operation_id")
    def _onchange_operation_id(self):
        res = super()._onchange_operation_id()
        if self.operation_id:
            self.invoice_policy = self.operation_id.invoice_policy
        return res
