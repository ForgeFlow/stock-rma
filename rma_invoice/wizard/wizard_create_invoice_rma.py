# Copyright 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizardCreateInvoiceRma(models.TransientModel):

    _name = "wizard.create.invoice.rma"
    _description = "Wizard to create Invoice From RMA"

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        required=True,
    )
    invoice_date = fields.Date(
        string="Invoice date",
        required=True,
        default=fields.Date.today(),
    )

    @api.model
    def default_get(self, fields_list):
        values = super(WizardCreateInvoiceRma, self).default_get(fields_list)
        rma_model = self.env["rma.order.line"]
        journal_model = self.env["account.journal"]
        current_rmas = rma_model.browse(self.env.context.get("active_ids")).filtered(
            lambda x: x.state != "draft"
        )
        rma_type = current_rmas.mapped("type")[0]
        journal_type = (
            rma_type == "customer" and "sale" or rma_type == "supplier" and "purchase"
        )
        journal = journal_model.search([("type", "=", journal_type)], limit=1)
        if journal:
            values["journal_id"] = journal.id
        return values

    def action_create_invoice(self):
        account_move_model = self.env["account.move"]
        rma_model = self.env["rma.order.line"]
        current_rmas = rma_model.browse(self.env.context.get("active_ids")).filtered(
            lambda x: x.state != "draft"
        )
        if len(current_rmas.mapped("partner_id")) != 1:
            raise UserError(_("You can't make service invoice with different partners"))
        rma_type = current_rmas.mapped("type")[0]
        journal_type = (
            rma_type == "customer"
            and "out_invoice"
            or rma_type == "supplier"
            and "in_invoice"
        )
        invoices = account_move_model.create(
            {
                "move_type": journal_type,
                "partner_id": current_rmas.mapped("partner_id").id,
                "rma_order_line_ids": [(6, 0, current_rmas.ids)],
                "invoice_origin": " / ".join(current_rmas.mapped("display_name")),
                "invoice_date": self.invoice_date,
                "journal_id": self.journal_id.id,
            }
        )
        if journal_type == "out_invoice":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_out_invoice_type"
            )
        if journal_type == "in_invoice":
            action = self.env["ir.actions.actions"]._for_xml_id(
                "account.action_move_in_invoice_type"
            )
        form_view = [(self.env.ref("account.view_move_form").id, "form")]
        if "views" in action:
            action["views"] = form_view + [
                (state, view) for state, view in action["views"] if view != "form"
            ]
        else:
            action["views"] = form_view
        action["res_id"] = invoices.id
        return action
