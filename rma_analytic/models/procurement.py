# -*- coding: utf-8 -*-
# © 2018 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, api, exceptions, models


class ProcurementOrder(models.Model):

    _inherit = "procurement.order"

    @api.constrains('account_analytic_id')
    def check_analytic(self):
        for order in self:
            if order.rma_line_id and (order.account_analytic_id !=
                                      order.rma_line_id.analytic_account_id):
                raise exceptions.ValidationError(
                    _("The analytic account in the procurement it's not the "
                      "same as in the rma line"))
