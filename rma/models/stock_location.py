
from odoo import fields, models


class StockLocation(models.Model):
    _inherit = 'stock.location'

    usage = fields.Selection(
        selection_add=[('rma', 'RMA')])
