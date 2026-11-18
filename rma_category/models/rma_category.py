# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import fields, models


class RmaCategory(models.Model):
    _name = "rma.category"
    _description = "RMA Cagtegories"
    _order = "name"

    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide the category without removing it.",
    )
    name = fields.Char(
        required=True,
        copy=False,
    )

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Category name already exists !"),
    ]
