# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import api, fields, models


class RmaRefund(models.TransientModel):
    _inherit = "rma.refund"

    @api.returns('rma.order.line')
    def _prepare_item(self, line):
        res = super(RmaRefund, self)._prepare_item(line)
        res['sale_line_id'] = line.sale_line_id.id
        return res


class RmaRefundItem(models.TransientModel):
    _inherit = "rma.refund.item"

    sale_line_id = fields.Many2one(
        comodel_name='sale.order.line', string='Sale Order Line')
