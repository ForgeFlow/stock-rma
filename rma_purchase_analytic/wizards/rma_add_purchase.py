# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, models


class RmaAddPurchase(models.TransientModel):
    _inherit = 'rma_add_purchase'

    @api.model
    def _prepare_rma_line_from_po_line(self, line):
        data = super(RmaAddPurchase, self)._prepare_rma_line_from_po_line(line)
        data.update(analytic_account_id=line.analytic_account_id.id)
        return data


class RmaLineMakePurchaseOrder(models.TransientModel):
    _inherit = "rma.order.line.make.purchase.order"
    _description = "Make Purchases Order from RMA Line"

    @api.model
    def _prepare_purchase_order_line(self, po, item):
        res = super(
            RmaLineMakePurchaseOrder, self)._prepare_purchase_order_line(
            po, item)
        res['account_analytic_id'] = item.line_id.analytic_account_id.id
        return res
