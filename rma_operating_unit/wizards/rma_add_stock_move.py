# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models, _
from odoo.exceptions import ValidationError


class RmaAddStockMove(models.TransientModel):
    _inherit = 'rma_add_stock_move'
    _description = 'Wizard to add rma lines from pickings'

    def _prepare_rma_line_from_stock_move(self, sm, lot=False):
        res = super(RmaAddStockMove, self)._prepare_rma_line_from_stock_move(
            sm, lot)
        if self.env.context.get('customer'):
            operation = sm.product_id.rma_customer_operation_id or \
                sm.product_id.categ_id.rma_customer_operation_id
        else:
            operation = sm.product_id.rma_supplier_operation_id or \
                sm.product_id.categ_id.rma_supplier_operation_id
        if not operation:
            operation = self.env['rma.operation'].search(
                [('type', '=', self.rma_id.type)], limit=1)
            if not operation:
                raise ValidationError(_("Please define an operation first"))

        if not operation.in_warehouse_id or not operation.out_warehouse_id:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.rma_id.company_id.id),
                 ('lot_rma_id', '!=', False),
                 ('operating_unit_id', '=', self.line_id.operating_unit_id.id)
                 ], limit=1)
            if not warehouse:
                raise ValidationError(_(
                    "Please define a warehouse with a default RMA location"))
            res.update(warehouse_id=warehouse.id)
        return res
