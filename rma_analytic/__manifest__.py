# Copyright 2023 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Analytic Account in RMA",
    "version": "15.0.1.0.0",
    "author": "ForgeFlow," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "category": "Analytic",
    "depends": [
        "rma_account",
        "stock_analytic",
        "procurement_mto_analytic",
    ],
    "data": ["views/rma_order_line_view.xml"],
    "installable": True,
}
