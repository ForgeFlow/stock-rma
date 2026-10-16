# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models
from odoo.fields import Domain


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _rec_names_search = ["name", "order_id.name"]

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line",
        string="RMA",
    )

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if self.env.context.get("rma"):
            domain = Domain.AND([domain, [("display_type", "=", False)]])
        return domain

    def _get_purchase_line_rma_name_get_label(self):
        self.ensure_one()
        return "PO:{} | INV: {}, | PART:{} | QTY:{}".format(
            self.order_id.name,
            " ".join(str(x) for x in [inv.name for inv in self.order_id.invoice_ids]),
            self.product_id.name,
            self.product_uom_qty,
        )

    def _compute_display_name(self):
        if not self.env.context.get("rma"):
            return super()._compute_display_name()
        for purchase_line in self:
            for purchase_line in self:
                if purchase_line.order_id.name:
                    purchase_line.display_name = (
                        purchase_line._get_purchase_line_rma_name_get_label()
                    )
                else:
                    return super(
                        PurchaseOrderLine, purchase_line
                    )._compute_display_name()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            rma_line_id = self.env.context.get("rma_line_id")
            if rma_line_id:
                vals["rma_line_id"] = rma_line_id
        return super().create(vals_list)
