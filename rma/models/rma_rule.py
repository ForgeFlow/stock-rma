# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from openerp import _, api, fields, models


class RmaRule(models.Model):
    _name = 'rma.rule'
    _description = 'RMA Approval Conditions'

    name = fields.Char('Description', required=True)
    code = fields.Char('Code', required=True)
    approval_policy = fields.Selection([
        ('always', 'Always')], string="Approval Policy",
        required=True, default='always')
