# -*- coding: utf-8 -*-
# Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # TODO: to be removed on migration to v10:
    # This is needed because odoo misspelled `store` in v9 :facepalm:
    state = fields.Selection(related='order_id.state', store=True)

    rma_line_id = fields.Many2one(
        comodel_name='rma.order.line', string='RMA',
    )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Allows to search by PO reference."""
        if not args:
            args = []
        args += ['|',
                 (self._rec_name, operator, name),
                 ('order_id.name', operator, name)]
        return super(PurchaseOrderLine, self).name_search(
            name=name, args=args, operator=operator, limit=limit)

    @api.model
    def _name_search(self, name='', args=None, operator='ilike',
                     limit=100, name_get_uid=None):
        """Typed text is cleared here for better extensibility."""
        return super(PurchaseOrderLine, self)._name_search(
            name='', args=args, operator=operator, limit=limit,
            name_get_uid=name_get_uid)

