# Copyright (C) 2021 Open Source Integrators
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_return_label(self):
        for rec in self:
            if not rec.carrier_id:
                raise UserError(_("You need to assign the carrier."))
            else:
                rma_order_line_id = self.env["rma.order.line"].search(
                    [("name", "=", rec.origin)]
                )
                if rma_order_line_id and rma_order_line_id.rma_id:
                    data, labels = rec.carrier_id.get_return_label(self)
                    rec.carrier_tracking_ref = data["tracking_number"]
                    mail_template = self.env.ref(
                        "rma_website_delivery.rma_return_label_mail"
                    )
                    attach_id = self.env["ir.attachment"].search(
                        [("name", "=", labels[0][0])], limit=1
                    )
                    mail_template.write({"attachment_ids": [(6, 0, attach_id.ids)]})
                    mail_template.send_mail(
                        rma_order_line_id.rma_id.id, force_send=True
                    )
