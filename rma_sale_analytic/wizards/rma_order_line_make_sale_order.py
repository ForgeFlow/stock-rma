# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models, api


class RmaLineMakeSaleOrder(models.TransientModel):
    _inherit = "rma.order.line.make.sale.order"

    @api.model
    def _prepare_sale_order_line(self, so, item):
        sale_line = super(
            RmaLineMakeSaleOrder, self)._prepare_sale_order_line(so, item)
        sale_line.update(
            analytic_account_id=item.line_id.analytic_account_id.id)
        return sale_line
