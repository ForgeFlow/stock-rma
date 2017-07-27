# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import _, api, fields, models


class RmaOperation(models.Model):
    _inherit = 'rma.operation'

    sale_type = fields.Selection([
        ('no', 'Not required'), ('ordered', 'Based on Ordered Quantities'),
        ('received', 'Based on Received Quantities')],
        string="Sale Policy", default='no')
