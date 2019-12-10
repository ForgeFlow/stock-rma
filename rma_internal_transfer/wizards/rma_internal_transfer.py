# Copyright (C) 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class RmaMakePicking(models.TransientModel):
    _name = 'rma_internal_transfer.wizard'
    _description = 'Wizard to create pickings from rma lines'

    @api.returns('rma.order.line')
    def _prepare_item(self, line):
        values = {'product_id': line.product_id.id,
                  'product_qty': line.product_qty,
                  'uom_id': line.uom_id.id,
                  'qty_to_receive': line.qty_to_receive,
                  'qty_to_deliver': line.qty_to_deliver,
                  'line_id': line.id,
                  'rma_id': line.rma_id and line.rma_id.id or False,
                  'wiz_id': self.env.context['active_id'],
                  }
        return values

    @api.model
    def default_get(self, fields_list):
        """Default values for wizard, if there is more than one supplier on
        lines the supplier field is empty otherwise is the unique line
        supplier.
        """
        context = self._context.copy()
        res = super(RmaMakePicking, self).default_get(fields_list)
        rma_line_obj = self.env['rma.order.line']
        rma_line_ids = self.env.context['active_ids'] or []
        active_model = self.env.context['active_model']

        if not rma_line_ids:
            return res
        assert active_model == 'rma.order.line', \
            'Bad context propagation'

        items = []
        lines = rma_line_obj.browse(rma_line_ids)
        if len(lines.mapped('partner_id')) > 1:
            raise ValidationError(
                _('Only RMA lines from the same partner can be processed at '
                  'the same time'))
        for line in lines:
            items.append([0, 0, self._prepare_item(line)])

        types = self.env['stock.picking.type'].search(
            [('code', '=', 'internal'),
             ('warehouse_id', 'in',
              lines.mapped('in_warehouse_id').ids)])[:1]
        if not types:
            raise ValidationError(_('Please define an internal picking type '
                                    'for this warehouse'))
        res['location_id'] = lines.mapped('location_id').ids[0]
        res['picking_type_id'] = types.id
        res['location_dest_id'] = lines.mapped('location_id').ids[0]
        res['item_ids'] = items
        context.update({'items_ids': items})
        return res

    item_ids = fields.One2many(
        'rma_internal_transfer.wizard.item',
        'wiz_id', string='Items')
    picking_type_id = fields.Many2one('stock.picking.type', 'Operation Type',
                                      required=True)
    location_id = fields.Many2one('stock.location', 'Source Location',
                                  required=True)
    location_dest_id = fields.Many2one(
        'stock.location', 'Destination Location', required=True)

    def find_procurement_group(self):
        if self.mapped('item_ids.line_id.rma_id'):
            return self.env['procurement.group'].search([
                ('rma_id', 'in', self.mapped('item_ids.line_id.rma_id').ids)])
        else:
            return self.env['procurement.group'].search([
                ('rma_line_id', 'in', self.mapped('item_ids.line_id').ids)])

    @api.multi
    def action_create_picking(self):
        self.ensure_one()
        picking_obj = self.env['stock.picking']
        type_obj = self.env['stock.picking.type']
        user_obj = self.env['res.users']
        company_id = user_obj.browse(self._uid).company_id.id
        types = type_obj.search([('code', '=', 'internal'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            raise UserError(_("Make sure you have at least an internal picking"
                              "type defined for your company's warehouse."))
        picking_type = types[0]
        group_id = self.find_procurement_group().id
        picking = picking_obj.create({
            'picking_type_id': picking_type.id,
            'location_dest_id': self.location_dest_id.id,
            'location_id': self.location_id.id,
            'move_lines': [(0, 0, {
                'name': item.line_id.name,
                'product_id': item.product_id.id,
                'product_uom_qty': item.product_qty,
                'product_uom': item.uom_id.id,
                'state': 'draft',
                'group_id': group_id,
                'rma_line_id': item.line_id.id,
            }) for item in self.item_ids]
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Picking',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
            'view_type': 'form',
        }

    @api.multi
    def action_cancel(self):
        return {'type': 'ir.actions.act_window_close'}


class RmaMakePickingItem(models.TransientModel):
    _name = "rma_internal_transfer.wizard.item"
    _description = "Items to receive"

    wiz_id = fields.Many2one(
        'rma_internal_transfer.wizard',
        string='Wizard', required=True)
    line_id = fields.Many2one('rma.order.line',
                              string='RMA order Line',
                              readonly=True,
                              ondelete='cascade')
    rma_id = fields.Many2one('rma.order',
                             related='line_id.rma_id',
                             string='RMA Group',
                             readonly=True)
    product_id = fields.Many2one('product.product', string='Product',
                                 required=True)
    product_qty = fields.Float(
        related='line_id.product_qty',
        string='Quantity Ordered', copy=False,
        digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
