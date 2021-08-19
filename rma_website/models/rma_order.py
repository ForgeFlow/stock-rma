from odoo import models


class RmaOrder(models.Model):
    _name = "rma.order"
    _inherit = [
        "rma.order",
        "portal.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "utm.mixin",
    ]
