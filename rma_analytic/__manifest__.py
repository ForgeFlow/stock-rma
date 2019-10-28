# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "Analytic Account in RMA",
    "version": "12.0.1.0.0",
    "author": "Eficent," "Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "http://www.eficent.com",
    "category": "Analytic",
    "depends": [
        "rma_account",
        "stock_analytic",
        "procurement_mto_analytic",
    ],
    "data": ["views/rma_order_line_view.xml"],
    "installable": True,
}
