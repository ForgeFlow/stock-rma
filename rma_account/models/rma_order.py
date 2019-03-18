# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class RmaOrder(models.Model):
    _inherit = "rma.order"

    @api.multi
    def _compute_invoice_refund_count(self):
        for rec in self:
            invoices = rec.mapped(
                'rma_line_ids.refund_line_ids.invoice_id')
            rec.invoice_refund_count = len(invoices)

    @api.multi
    def _compute_invoice_count(self):
        for rec in self:
            invoices = rec.mapped('rma_line_ids.invoice_id')
            rec.invoice_count = len(invoices)

    add_invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Add Invoice',
        ondelete='set null', readonly=True,
    )
    invoice_refund_count = fields.Integer(
        compute='_compute_invoice_refund_count', string='# of Refunds')
    invoice_count = fields.Integer(
        compute='_compute_invoice_count', string='# of Invoices')

    def _prepare_rma_line_from_inv_line(self, line):
        if self.type == 'customer':
            operation =\
                self.rma_line_ids.product_id.rma_customer_operation_id or \
                self.rma_line_ids.product_id.categ_id.rma_customer_operation_id
        else:
            operation =\
                self.rma_line_ids.product_id.rma_supplier_operation_id or \
                self.rma_line_ids.product_id.categ_id.rma_supplier_operation_id
        data = {
            'invoice_line_id': line.id,
            'product_id': line.product_id.id,
            'name': line.name,
            'origin': line.invoice_id.number,
            'uom_id': line.uom_id.id,
            'operation_id': operation,
            'product_qty': line.quantity,
            'price_unit': line.invoice_id.currency_id.compute(
                line.price_unit, line.currency_id, round=False),
            'rma_id': self.id
        }
        return data

    @api.onchange('add_invoice_id')
    def on_change_invoice(self):
        if not self.add_invoice_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.add_invoice_id.partner_id.id
        new_lines = self.env['rma.order.line']
        for line in self.add_invoice_id.invoice_line_ids:
            # Load a PO line only once
            if line in self.rma_line_ids.mapped('invoice_line_id'):
                continue
            data = self._prepare_rma_line_from_inv_line(line)
            new_line = new_lines.new(data)
            new_lines += new_line

        self.rma_line_ids += new_lines
        self.date_rma = fields.Datetime.now()
        self.delivery_address_id = self.add_invoice_id.partner_id.id
        self.invoice_address_id = self.add_invoice_id.partner_id.id
        self.add_invoice_id = False
        return {}

    @api.model
    def prepare_rma_line(self, origin_rma, rma_id, line):
        line_values = super(RmaOrder, self).prepare_rma_line(
            origin_rma, rma_id, line)
        line_values['invoice_address_id'] = line.invoice_address_id.id
        return line_values

    @api.model
    def _prepare_rma_data(self, partner, origin_rma):
        res = super(RmaOrder, self)._prepare_rma_data(partner, origin_rma)
        res['invoice_address_id'] = partner.id
        return res

    @api.multi
    def action_view_invoice_refund(self):
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        invoice_ids = self.mapped(
            'rma_line_ids.refund_line_ids.invoice_id').ids
        if invoice_ids:
            # choose the view_mode accordingly
            if len(invoice_ids) > 1:
                result['domain'] = [('id', 'in', invoice_ids)]
            else:
                res = self.env.ref('account.invoice_supplier_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = invoice_ids[0]
        return result

    @api.multi
    def action_view_invoice(self):
        if self.type == "supplier":
            action = self.env.ref('account.action_invoice_tree2')
            res = self.env.ref('account.invoice_supplier_form', False)
        else:
            action = self.env.ref('account.action_invoice_tree')
            res = self.env.ref('account.invoice_form', False)
        result = action.read()[0]
        invoice_ids = self.mapped('rma_line_ids.invoice_id').ids
        if invoice_ids:
            # choose the view_mode accordingly
            if len(invoice_ids) > 1:
                result['domain'] = [('id', 'in', invoice_ids)]
            else:
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = invoice_ids[0]
        return result
