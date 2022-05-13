# Copyright 2017 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("line_ids.rma_line_ids")
    def _compute_rma_count(self):
        for inv in self:
            rmas = self.mapped("line_ids.rma_line_ids")
            inv.rma_count = len(rmas)

    def _prepare_invoice_line_from_rma_line(self, line):
        qty = line.qty_to_refund
        if float_compare(qty, 0.0, precision_rounding=line.uom_id.rounding) <= 0:
            qty = 0.0
        # Todo fill taxes from somewhere
        invoice_line = self.env["account.move.line"]
        data = {
            "purchase_line_id": line.id,
            "name": line.name + ": " + line.name,
            "product_uom_id": line.uom_id.id,
            "product_id": line.product_id.id,
            "account_id": invoice_line.with_context(
                **{"journal_id": self.journal_id.id, "type": "in_invoice"}
            )._default_account(),
            "price_unit": line.company_id.currency_id.with_context(
                date=self.date
            ).compute(line.price_unit, self.currency_id, round=False),
            "quantity": qty,
            "discount": 0.0,
            "rma_line_ids": [(4, line.id)],
        }
        return data

    @api.onchange("add_rma_line_id")
    def on_change_add_rma_line_id(self):
        if not self.add_rma_line_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_rma_line_id.partner_id.id

        new_line = self.env["account.move.line"]
        if self.add_rma_line_id not in (self.line_ids.mapped("rma_line_id")):
            data = self._prepare_invoice_line_from_rma_line(self.add_rma_line_id)
            new_line = new_line.new(data)
            new_line._set_additional_fields(self)
        self.line_ids += new_line
        self.add_rma_line_id = False
        return {}

    rma_count = fields.Integer(compute="_compute_rma_count", string="# of RMA")

    add_rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="Add from RMA line",
        ondelete="set null",
        help="Create a refund in based on an existing rma_line",
    )

    def action_view_rma_supplier(self):
        action = self.env.ref("rma.action_rma_supplier_lines")
        result = action.sudo().read()[0]
        rma_ids = self.mapped("line_ids.rma_line_ids").ids
        if rma_ids:
            # choose the view_mode accordingly
            if len(rma_ids) > 1:
                result["domain"] = [("id", "in", rma_ids)]
            else:
                res = self.env.ref("rma.view_rma_line_supplier_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = rma_ids[0]
        return result

    def action_view_rma_customer(self):
        action = self.env.ref("rma.action_rma_customer_lines")
        result = action.sudo().read()[0]
        rma_ids = self.mapped("line_ids.rma_line_ids").ids
        if rma_ids:
            # choose the view_mode accordingly
            if len(rma_ids) > 1:
                result["domain"] = [("id", "in", rma_ids)]
            else:
                res = self.env.ref("rma.view_rma_line_form", False)
                result["views"] = [(res and res.id or False, "form")]
                result["res_id"] = rma_ids[0]
        return result

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        product_model = self.env["product.product"]
        res = super()._stock_account_prepare_anglo_saxon_out_lines_vals()
        for line in res:
            if line.get("product_id", False):
                product = product_model.browse(line.get("product_id", False))
                if (
                    line.get("account_id")
                    != product.categ_id.property_stock_valuation_account_id.id
                ):
                    current_move = self.browse(line.get("move_id", False))
                    current_rma = current_move.invoice_line_ids.filtered(
                        lambda x: x.rma_line_id and x.product_id.id == product.id
                    ).mapped("rma_line_id")
                    if len(current_rma) == 1:
                        line.update({"rma_line_id": current_rma.id})
                    elif len(current_rma) > 1:
                        find_with_label_rma = current_rma.filtered(
                            lambda x: x.name == line.get("name")
                        )
                        if len(find_with_label_rma) == 1:
                            line.update({"rma_line_id": find_with_label_rma.id})
        return res
