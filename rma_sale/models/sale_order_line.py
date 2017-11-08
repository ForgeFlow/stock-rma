# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Allows to search by SO reference."""
        if not args:
            args = []
        args += ['|',
                 (self._rec_name, operator, name),
                 ('order_id.name', operator, name)]
        return super(SaleOrderLine, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        """Typed text is cleared here for better extensibility."""
        return super(SaleOrderLine, self)._name_search(
            name='', args=args, operator=operator, limit=limit,
            name_get_uid=name_get_uid)

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA', ondelete='restrict')

    @api.multi
    def _prepare_order_line_procurement(self, group_id=False):
        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(
            group_id=group_id)
        vals.update({
            'rma_line_id': self.rma_line_id.id
        })
        return vals
