# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models


class QualityControlIssue(models.Model):
    _inherit = "qc.issue"

    @api.multi
    def _compute_rma_line_count(self):
        for rec in self:
            rec.rma_line_count_customer = len(self.rma_line_ids.filtered(
                lambda l: l.type == 'customer'))
            rec.rma_line_count_supplier = len(self.rma_line_ids.filtered(
                lambda l: l.type == 'supplier'))

    rma_line_ids = fields.One2many(
        comodel_name="rma.order.line", string="RMA order lines",
        inverse_name="qc_issue_id")
    rma_line_count_customer = fields.Integer(compute=_compute_rma_line_count)
    rma_line_count_supplier = fields.Integer(compute=_compute_rma_line_count)

    @api.multi
    def action_view_rma_lines_supplier(self):
        action = self.env.ref('rma.action_rma_supplier_lines')
        result = action.read()[0]
        lines = self.rma_line_ids.filtered(lambda l: l.type == 'supplier')
        # choose the view_mode accordingly
        if len(lines) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(lines.ids) + ")]"
        elif len(lines) == 1:
            res = self.env.ref('rma.view_rma_line_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = lines.id
        return result

    @api.multi
    def action_view_rma_lines_customer(self):
        action = self.env.ref('rma.action_rma_customer_lines')
        result = action.read()[0]
        lines = self.rma_line_ids.filtered(lambda l: l.type == 'customer')
        # choose the view_mode accordingly
        if len(lines) != 1:
            result['domain'] = "[('id', 'in', " + \
                               str(lines.ids) + ")]"
        elif len(lines) == 1:
            res = self.env.ref('rma.view_rma_line_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = lines.id
        return result
