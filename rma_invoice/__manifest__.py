# © 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Invoices Related",
    "version": "14.0.1.0.0",
    "category": "RMA",
    "summary": "RMA Invoices Related",
    "license": "LGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma", "rma_account", "purchase"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_create_invoice_rma_view.xml",
        "views/account_move_view.xml",
        "views/rma_order_line_view.xml",
    ],
    "maintainers": ["ChisOForgeFlow"],
    "development_status": "Beta",
    "installable": True,
}
