# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaOrderLine(models.Model):
    _inherit = "rma.order.line"

    category_ids = fields.Many2many("rma.category", string="Categories")
