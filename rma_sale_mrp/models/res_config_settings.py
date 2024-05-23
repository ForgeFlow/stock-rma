# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    rma_add_component_from_sale = fields.Boolean(
        related="company_id.rma_add_component_from_sale",
        readonly=False,
        help="If active, when creating a rma from a sale order, in case the product "
        "is a kit, the delivered components will be added instead of the kit.",
    )
