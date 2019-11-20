# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaLineMakePurchaseOrder(models.TransientModel):
    _inherit = "rma.order.line.make.purchase.order"

    @api.model
    def _prepare_purchase_order(self, item):
        res = super(RmaLineMakePurchaseOrder, self)._prepare_purchase_order(
            item)
        res.update(operating_unit_id=item.line_id.operating_unit_id.id)
        return res
