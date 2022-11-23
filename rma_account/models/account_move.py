# Copyright 2017-22 ForgeFlow S.L.
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

    def _prepare_invoice_line_from_rma_line(self, rma_line):
        sequence = max(self.line_ids.mapped("sequence")) + 1 if self.line_ids else 10
        qty = rma_line.qty_to_refund
        if float_compare(qty, 0.0, precision_rounding=rma_line.uom_id.rounding) <= 0:
            qty = 0.0
        # Todo fill taxes from somewhere
        data = {
            "move_id": self.id,
            "product_uom_id": rma_line.uom_id.id,
            "product_id": rma_line.product_id.id,
            "price_unit": rma_line.company_id.currency_id.with_context(
                date=self.date
            ).compute(rma_line.price_unit, self.currency_id, round=False),
            "quantity": qty,
            "discount": 0.0,
            "rma_line_ids": [(4, rma_line.id)],
            "sequence": sequence + 1,
        }
        return data

    def _post_process_invoice_line_from_rma_line(self, new_line, rma_line):
        new_line.name = "%s: %s" % (
            self.add_rma_line_id.name,
            new_line._get_computed_name(),
        )
        new_line.account_id = new_line._get_computed_account()
        new_line._onchange_price_subtotal()
        new_line._onchange_mark_recompute_taxes()
        return True

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
            self._post_process_invoice_line_from_rma_line(
                new_line, self.add_rma_line_id
            )
        line = new_line._convert_to_write(
            {name: new_line[name] for name in new_line._cache}
        )
        # Compute invoice_origin.
        origins = set(self.line_ids.mapped("rma_line_id.name"))
        self.invoice_origin = ",".join(list(origins))
        self.add_rma_line_id = False
        self._onchange_currency()
        return line

    rma_count = fields.Integer(compute="_compute_rma_count", string="# of RMA")

    add_rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="Add from RMA line",
        ondelete="set null",
        help="Create a refund in based on an existing rma_line",
    )

    def action_view_rma(self):
        if self.move_type in ["in_invoice", "in_refund"]:
            action = self.env.ref("rma.action_rma_supplier_lines")
            form_view = self.env.ref("rma.view_rma_line_supplier_form", False)
        else:
            action = self.env.ref("rma.action_rma_customer_lines")
            form_view = self.env.ref("rma.view_rma_line_form", False)
        result = action.sudo().read()[0]
        rma_ids = self.mapped("line_ids.rma_line_ids").ids
        # choose the view_mode accordingly
        if not rma_ids:
            result["domain"] = [("id", "in", [])]
        elif len(rma_ids) > 1:
            result["domain"] = [("id", "in", rma_ids)]
        else:
            res = form_view
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = rma_ids and rma_ids[0] or False
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

    def _stock_account_get_last_step_stock_moves(self):
        rslt = super(AccountMove, self)._stock_account_get_last_step_stock_moves()
        for invoice in self.filtered(lambda x: x.move_type == "out_invoice"):
            rslt += invoice.mapped("line_ids.rma_line_id.move_ids").filtered(
                lambda x: x.state == "done" and x.location_dest_id.usage == "customer"
            )
        for invoice in self.filtered(lambda x: x.move_type == "out_refund"):
            # Add refunds generated from the RMA
            rslt += invoice.mapped("line_ids.rma_line_id.move_ids").filtered(
                lambda x: x.state == "done" and x.location_id.usage == "customer"
            )
        return rslt


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
        string="RMA line",
        ondelete="set null",
        help="This will contain the rma line that originated this line",
    )

    def _stock_account_get_anglo_saxon_price_unit(self):
        self.ensure_one()
        price_unit = super(
            AccountMoveLine, self
        )._stock_account_get_anglo_saxon_price_unit()
        rma_line = self.rma_line_id or self.env["rma.order.line"]
        if rma_line:
            is_line_reversing = bool(self.move_id.reversed_entry_id)
            qty_to_refund = self.product_uom_id._compute_quantity(
                self.quantity, self.product_id.uom_id
            )
            posted_invoice_lines = rma_line.move_line_ids.filtered(
                lambda l: l.move_id.move_type == "out_refund"
                and l.move_id.state == "posted"
                and bool(l.move_id.reversed_entry_id) == is_line_reversing
            )
            qty_refunded = sum(
                x.product_uom_id._compute_quantity(x.quantity, x.product_id.uom_id)
                for x in posted_invoice_lines
            )
            product = self.product_id.with_company(self.company_id).with_context(
                is_returned=is_line_reversing
            )
            average_price_unit = product._compute_average_price(
                qty_refunded, qty_to_refund, rma_line._get_in_moves()
            )
            if average_price_unit:
                price_unit = self.product_id.uom_id.with_company(
                    self.company_id
                )._compute_price(average_price_unit, self.product_uom_id)
        return price_unit
