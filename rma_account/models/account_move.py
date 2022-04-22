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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        """Allows to search by Invoice number. This has to be done this way,
        as Odoo adds extra args to name_search on _name_search method that
        will make impossible to get the desired result."""
        if not args:
            args = []
        lines = self.search([("move_id.name", operator, name)] + args, limit=limit)
        res = lines.name_get()
        if limit:
            limit_rest = limit - len(lines)
        else:
            # limit can be 0 or None representing infinite
            limit_rest = limit
        if limit_rest or not limit:
            args += [("id", "not in", lines.ids)]
            res += super(AccountMoveLine, self).name_search(
                name, args=args, operator=operator, limit=limit_rest
            )
        return res

    def name_get(self):
        res = []
        if self.env.context.get("rma"):
            for inv in self:
                if inv.move_id.ref:
                    res.append(
                        (
                            inv.id,
                            "INV:%s | REF:%s | ORIG:%s | PART:%s | QTY:%s"
                            % (
                                inv.move_id.name or "",
                                inv.move_id.invoice_origin or "",
                                inv.move_id.ref or "",
                                inv.product_id.name,
                                inv.quantity,
                            ),
                        )
                    )
                elif inv.move_id.name:
                    res.append(
                        (
                            inv.id,
                            "INV:%s | ORIG:%s | PART:%s | QTY:%s"
                            % (
                                inv.move_id.name or "",
                                inv.move_id.invoice_origin or "",
                                inv.product_id.name,
                                inv.quantity,
                            ),
                        )
                    )
                else:
                    res.append(super(AccountMoveLine, inv).name_get()[0])
            return res
        else:
            return super(AccountMoveLine, self).name_get()

    def _compute_rma_count(self):
        for invl in self:
            rma_lines = invl.mapped("rma_line_ids")
            invl.rma_line_count = len(rma_lines)

    rma_line_count = fields.Integer(compute="_compute_rma_count", string="# of RMA")
    rma_line_ids = fields.One2many(
        comodel_name="rma.order.line",
        inverse_name="account_move_line_id",
        string="RMA",
        readonly=True,
        help="This will contain the RMA lines for the invoice line",
    )

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="RMA line refund",
        ondelete="set null",
        help="This will contain the rma line that originated the refund line",
    )
