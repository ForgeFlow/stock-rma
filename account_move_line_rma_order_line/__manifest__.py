# © 2017-2022 ForgeFlow S.L. (www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Rma Order Line",
    "summary": "Introduces the rma order line to the journal items",
    "version": "14.0.1.1.0",
    "author": "ForgeFlow, " "Odoo Community Association (OCA)",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "category": "Generic",
    "depends": ["stock_account", "rma_account"],
    "license": "AGPL-3",
    "data": [
        "security/account_security.xml",
    ],
    "installable": True,
    "maintainers": ["ChisOForgeFlow"],
    "development_status": "Beta",
    "post_init_hook": "post_init_hook",
    "auto_install": True,
}
