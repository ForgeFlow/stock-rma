# Copyright 2017-22 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.fields import Domain


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _name_search(self, name, domain=None, operator="ilike", limit=None, order=None):
        """Allows to search by Invoice number. This has to be done this way,
        as Odoo adds extra args to name_search on _name_search method that
        will make impossible to get the desired result."""
        domain = domain or []
        if self.env.context.get("rma"):
            domain = Domain.AND(
                [
                    domain,
                    [("display_type", "in", ("product", "line_section", "line_note"))],
                ]
            )
        lines = self.search([("move_id.name", operator, name)] + domain, limit=limit)
        if limit:
            limit_rest = limit - len(lines)
        else:
            # limit can be 0 or None representing infinite
            limit_rest = limit
        if limit_rest or not limit:
            domain += [("id", "in", lines.ids)]
            return super()._name_search(
                name, domain=domain, operator=operator, limit=limit_rest, order=order
            )
        return self._search(domain, limit=limit, order=order)

    def _compute_display_name(self):
        if not self.env.context.get("rma"):
            return super()._compute_display_name()
        for inv in self:
            if inv.move_id.ref:
                name = "INV:{} | REF:{} | ORIG:{} | PART:{} | QTY:{}".format(
                    inv.move_id.name or "",
                    inv.move_id.invoice_origin or "",
                    inv.move_id.ref or "",
                    inv.product_id.name,
                    inv.quantity,
                )
                inv.display_name = name
            elif inv.move_id.name:
                name = "INV:{} | ORIG:{} | PART:{} | QTY:{}".format(
                    inv.move_id.name or "",
                    inv.move_id.invoice_origin or "",
                    inv.product_id.name,
                    inv.quantity,
                )
                inv.display_name = name

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

    def _get_stock_moves(self):
        return super()._get_stock_moves() | self.rma_line_id.move_ids
