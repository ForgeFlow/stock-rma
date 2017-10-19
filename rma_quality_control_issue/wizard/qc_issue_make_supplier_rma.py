# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class QcIssueMakeSupplierRma(models.TransientModel):
    _name = "qc.issue.make.supplier.rma"

    _description = "QC Issue Make Supplier RMA"

    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Supplier',
        required=False, domain=[('supplier', '=', True)],
    )
    item_ids = fields.One2many(
        comodel_name='qc.issue.make.supplier.rma.item',
        inverse_name='wiz_id', string='Items',
    )
    supplier_rma_id = fields.Many2one(
        comodel_name='rma.order', string='Supplier RMA Group',
        required=False, domain=[('type', '=', 'supplier')]
    )
    use_group = fields.Boolean(string="Use RMA Group")

    @api.model
    def _prepare_item(self, issue):
        return {
            'issue_id': issue.id,
            'product_id': issue.product_id.id,
            'lot_id': issue.lot_id.id,
            'name': issue.name,
            'product_qty': issue.product_qty,
            'uom_id': issue.product_uom.id,
        }

    @api.model
    def default_get(self, fields):
        res = super(QcIssueMakeSupplierRma, self).default_get(
            fields)
        qc_issue_obj = self.env['qc.issue']
        qc_issue_ids = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']

        if not qc_issue_ids:
            return res
        assert active_model == 'qc.issue', 'Bad context propagation'

        items = []
        issues = qc_issue_obj.browse(qc_issue_ids)
        for issue in issues:
            items.append([0, 0, self._prepare_item(issue)])
        res['item_ids'] = items
        return res

    @api.model
    def _prepare_supplier_rma(self, company):
        if not self.partner_id:
            raise ValidationError(
                _('Enter a supplier.'))
        return {
            'partner_id': self.partner_id.id,
            'delivery_address_id': self.partner_id.id,
            'type': 'supplier',
            'company_id': company.id,
        }

    @api.model
    def _prepare_supplier_rma_line(self, item, rma=False):
        operation = self.env['rma.operation'].search(
            [('type', '=', 'supplier')], limit=1)
        data = {
            'partner_id': rma and rma.partner_id.id or self.partner_id.id,
            'type': 'supplier',
            'rma_id': rma and rma.id or False,
            'lot_id': item.issue_id.lot_id,
            'origin': item.issue_id.name,
            'product_id': item.product_id.id,
            'product_qty': item.product_qty,
            'uom_id': item.uom_id.id,
            'qc_issue_id': item.issue_id.id,
            'operation_id': operation.id,
            'receipt_policy': operation.receipt_policy,
            'delivery_policy': operation.delivery_policy,
            'in_warehouse_id': operation.in_warehouse_id.id,
            'out_warehouse_id': operation.out_warehouse_id.id,
            'location_id': operation.location_id.id or
            operation.in_warehouse_id.lot_rma_id.id,
            'supplier_to_customer': operation.supplier_to_customer,
            'in_route_id': operation.in_route_id.id,
            'out_route_id': operation.out_route_id.id,
        }
        if item.issue_id.location_id:
            data['location_id'] = item.issue_id.location_id.id
            wh = self.env["stock.warehouse"].search([
                ('view_location_id.parent_left', '<=',
                 item.issue_id.location_id.parent_left),
                ('view_location_id.parent_right', '>=',
                 item.issue_id.location_id.parent_left)], limit=1)
            if wh:
                data['in_warehouse_id'] = wh.id
                data['out_warehouse_id'] = wh.id
        return data

    @api.multi
    def make_supplier_rma_group(self):
        res = []
        rma_obj = self.env['rma.order']
        rma_line_obj = self.env['rma.order.line']
        rma = False
        action = self.env.ref(
            'rma.action_rma_supplier')
        action = action.read()[0]

        for item in self.item_ids:
            issue = item.issue_id
            if item.product_qty <= 0.0:
                raise ValidationError(
                    _('Enter a positive quantity.'))

            if self.supplier_rma_id:
                rma = self.supplier_rma_id
            if not rma:
                rma_data = self._prepare_supplier_rma(issue.company_id)
                rma = rma_obj.create(rma_data)

            rma_line_data = self._prepare_supplier_rma_line(item, rma)
            rma_line_obj.create(rma_line_data)
            res.append(rma.id)

        if len(res) != 1:
            action['domain'] = [('id', 'in', res)]
        elif len(res) == 1:
            view = self.env.ref('rma.view_rma_supplier_form',
                                False)
            action['views'] = [(view and view.id or False, 'form')]
            action['res_id'] = res[0]
        return action

    @api.multi
    def make_supplier_rma_no_group(self):
        res = []
        rma_line_obj = self.env['rma.order.line']
        action = self.env.ref(
            'rma.action_rma_supplier_lines')
        action = action.read()[0]
        for item in self.item_ids:
            if item.product_qty <= 0.0:
                raise ValidationError(
                    _('Enter a positive quantity.'))
            rma_line_data = self._prepare_supplier_rma_line(item)
            rma_line = rma_line_obj.create(rma_line_data)
            res.append(rma_line.id)

        if len(res) != 1:
            action['domain'] = [('id', 'in', res)]
        elif len(res) == 1:
            view = self.env.ref(
                'rma.view_rma_line_supplier_form', False)
            action['views'] = [(view and view.id or False, 'form')]
            action['res_id'] = res[0]
        return action

    @api.multi
    def make_supplier_rma(self):
        if self.use_group:
            return self.make_supplier_rma_group()
        else:
            return self.make_supplier_rma_no_group()


class QcIssueMakeSupplierRmaItem(models.TransientModel):
    _name = "qc.issue.make.supplier.rma.item"
    _description = "RMA Line Make Supplier RMA Item"

    wiz_id = fields.Many2one(
        'qc.issue.make.supplier.rma',
        string='Wizard', required=True, ondelete='cascade',
        readonly=True)
    issue_id = fields.Many2one('qc.issue', string='Quality Issue',
                               required=True)
    product_id = fields.Many2one('product.product',
                                 related='issue_id.product_id', readony=True)
    lot_id = fields.Many2one(
        comodel_name="stock.production.lot", string="Lot/Serial Number",
        readonly=True, related='issue_id.lot_id',
    )
    name = fields.Char(related='issue_id.name', readonly=True)
    uom_id = fields.Many2one('product.uom', string='UoM', readonly=True)
    product_qty = fields.Float(string='Quantity to RMA',
                               digits=dp.get_precision('Product UoS'))
