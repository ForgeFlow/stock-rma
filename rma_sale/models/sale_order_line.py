# Copyright 2020 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        """Allows to search by SO reference."""
        if not args:
            args = []
        args += [
            "|",
            (self._rec_name, operator, name),
            ("order_id.name", operator, name),
        ]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def _name_search(
        self, name="", args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Typed text is cleared here for better extensibility."""
        return super()._name_search(
            name="",
            args=args,
            operator=operator,
            limit=limit,
            name_get_uid=name_get_uid,
        )

    def _get_sale_line_rma_name_get_label(self):
        self.ensure_one()
        return "SO:{} | INV: {}, | PART:{} | QTY:{}".format(
            self.order_id.name,
            " ".join(str(x) for x in [inv.name for inv in self.order_id.invoice_ids]),
            self.product_id.name,
            self.product_uom_qty,
        )

    def name_get(self):
        res = []
        if self.env.context.get("rma"):
            for sale_line in self:
                if sale_line.order_id.name:
                    res.append(
                        (sale_line.id, sale_line._get_sale_line_rma_name_get_label())
                    )
                else:
                    res.append(super(SaleOrderLine, sale_line).name_get()[0])
            return res
        else:
            return super().name_get()

    rma_line_id = fields.Many2one(
        comodel_name="rma.order.line", string="RMA", ondelete="restrict", copy=False
    )

    def _prepare_order_line_procurement(self, group_id=False):
        vals = super()._prepare_order_line_procurement(group_id=group_id)
        vals.update({"rma_line_id": self.rma_line_id.id})
        return vals
