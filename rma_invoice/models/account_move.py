# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval


class AccountMove(models.Model):

    _inherit = "account.move"

    rma_order_line_ids = fields.Many2many(
        comodel_name="rma.order.line", string="Rma orders"
    )

    rma_order_line_count = fields.Integer(
        string="Rma order lines Count",
        compute="_compute_rma_order_line_count",
    )

    @api.depends("rma_order_line_ids")
    def _compute_rma_order_line_count(self):
        for rec in self:
            rec.rma_order_line_count = len(rec.rma_order_line_ids)

    def action_show_rma_lines(self):
        self.ensure_one()
        action = {}
        form_view = False
        if self.move_type == "out_invoice":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "rma.action_rma_customer_lines"
            )
            form_view = [(self.env.ref("rma.view_rma_line_form").id, "form")]
        elif self.move_type == "in_invoice":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "rma.action_rma_supplier_lines"
            )
            form_view = [(self.env.ref("rma.view_rma_line_supplier_form").id, "form")]
        if len(self.rma_order_line_ids) <= 1 and form_view:
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = self.rma_order_line_ids.ids[0]
        else:
            action["domain"] += [("id", "in", self.rma_order_line_ids.ids)]
            domain = safe_eval(action["domain"]) or []
            domain += [("id", "in", self.rma_order_line_ids.ids)]
            action["domain"] = action["domain"]
        return action
