# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


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

    def _compute_used_in_rma_count(self):
        for invl in self:
            rma_lines = invl.mapped("rma_line_ids")
            invl.used_in_rma_line_count = len(rma_lines)

    def _compute_rma_count(self):
        for invl in self:
            rma_lines = invl.mapped("rma_line_id")
            invl.rma_line_count = len(rma_lines)

    used_in_rma_line_count = fields.Integer(
        compute="_compute_used_in_rma_count", string="# of used RMA"
    )
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
        index=True,
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
