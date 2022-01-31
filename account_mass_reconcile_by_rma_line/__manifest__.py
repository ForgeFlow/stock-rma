# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Mass Reconcile by RMA Order Line",
    "summary": "Allows to reconcile based on the PO line",
    "version": "14.0.1.0.0",
    "author": "ForgeFlow, " "Odoo Community Association (OCA)",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "category": "Finance",
    "depends": [
        "account_mass_reconcile",
        "account_move_line_rma_order_line",
        "rma_account",
    ],
    "license": "AGPL-3",
    "data": ["security/ir.model.access.csv", "views/mass_reconcile.xml"],
    "installable": True,
    "auto_install": False,
    "development_status": "Beta",
    "maintainers": ["ChrisOForgeFlow"],
}
