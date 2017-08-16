# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import api, fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    @api.multi
    def _compute_sales_count(self):
        self.ensure_one()
        sales_list = []
        for rma_line in self.rma_line_ids:
            if rma_line.sale_line_id and rma_line.sale_line_id.id:
                sales_list.append(rma_line.sale_line_id.order_id.id)
        self.sale_count = len(list(set(sales_list)))

    sale_count = fields.Integer(compute=_compute_sales_count,
                                string='# of Sales', copy=False, default=0)

    @api.model
    def _get_line_domain(self, rma_id, line):
        if line.sale_line_id and line.sale_line_id.id:
            domain = [('rma_id', '=', rma_id.id),
                      ('type', '=', 'supplier'),
                      ('sale_line_id', '=', line.sale_line_id.id)]
        else:
            domain = super(RmaOrder, self)._get_line_domain(rma_id, line)
        return domain

    @api.multi
    def action_view_sale_order(self):
        action = self.env.ref('sale.action_quotations')
        result = action.read()[0]
        order_ids = []
        for rma_line in self.rma_line_ids:
            if rma_line.sale_line_id and rma_line.sale_line_id.id:
                order_ids.append(rma_line.sale_line_id.order_id.id)
        result['domain'] = [('id', 'in', order_ids)]
        return result
