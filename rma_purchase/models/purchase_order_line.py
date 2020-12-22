# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="RMA",
    )

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Allows to search by PO reference."""
        if not args:
            args = []
        args += [
            "|",
            (self._rec_name, operator, name),
            ("order_id.name", operator, name),
        ]
        return super(PurchaseOrderLine, self).name_search(
            name=name, args=args, operator=operator, limit=limit
        )

    @api.model
    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Typed text is cleared here for better extensibility."""
        return super(PurchaseOrderLine, self)._name_search(
            name="",
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )

    @api.multi
    def name_get(self):
        res = []
        if self.env.context.get("rma"):
            for purchase in self:
                invoices = self.env["account.invoice.line"].search(
                    [("purchase_line_id", "=", purchase.id)]
                )
                if purchase.order_id.name:
                    res.append(
                        (
                            purchase.id,
                            "%s %s %s qty:%s"
                            % (
                                purchase.order_id.name,
                                " ".join(
                                    str(x)
                                    for x in [
                                        inv.number
                                        for inv in invoices.mapped("invoice_id")
                                    ]
                                ),
                                purchase.product_id.name,
                                purchase.product_qty,
                            ),
                        )
                    )
                else:
                    res.append(super(PurchaseOrderLine, purchase).name_get()[0])
            return res
        else:
            return super(PurchaseOrderLine, self).name_get()

    @api.model
    def create(self, vals):
        rma_line_id = self.env.context.get("rma_line_id")
        if rma_line_id:
            vals["rma_line_id"] = rma_line_id
        return super(PurchaseOrderLine, self).create(vals)
