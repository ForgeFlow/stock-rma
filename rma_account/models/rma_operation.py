# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaOperation(models.Model):
    _inherit = 'rma.operation'

    refund_policy = fields.Selection([
        ('no', 'No refund'), ('ordered', 'Based on Ordered Quantities'),
        ('delivered', 'Based on Delivered Quantities'),
        ('received', 'Based on Received Quantities')], string="Refund Policy",
        default='no')
