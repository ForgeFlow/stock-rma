# Copyright 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RmaOperation(models.Model):
    _inherit = 'rma.operation'

    purchase_policy = fields.Selection(
        selection=[('no', 'Not required'),
                   ('ordered', 'Based on Ordered Quantities'),
                   ('delivered', 'Based on Delivered Quantities')],
        string="Purchase Policy", default='no',
    )

    @api.multi
    @api.constrains('purchase_policy')
    def _check_purchase_policy(self):
        if self.filtered(
                lambda r: r.purchase_policy != 'no' and r.type != 'supplier'):
            raise ValidationError(_(
                'Purchase Policy can only apply to supplier operations'))
