# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models
from odoo.fields import Domain


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if self.env.context.get("rma"):
            domain = Domain.AND([domain, [("display_type", "=", False)]])
        return domain

    def _get_sale_line_rma_name_get_label(self):
        self.ensure_one()
        return "SO:{} | INV: {}, | PART:{} | QTY:{}".format(
            self.order_id.name,
            " ".join(str(x) for x in [inv.name for inv in self.order_id.invoice_ids]),
            self.product_id.name,
            self.product_uom_qty,
        )

    def _compute_display_name(self):
        if not self.env.context.get("rma"):
            return super()._compute_display_name()
        for sale_line in self:
            for sale_line in self:
                if sale_line.order_id.name:
                    sale_line.display_name = (
                        sale_line._get_sale_line_rma_name_get_label()
                    )
                else:
                    return super(SaleOrderLine, sale_line)._compute_display_name()

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA", ondelete="restrict", copy=False
    )

    def _prepare_procurement_values(self):
        vals = super()._prepare_procurement_values()
        vals.update({"rma_line_id": self.rma_line_id.id})
        return vals
