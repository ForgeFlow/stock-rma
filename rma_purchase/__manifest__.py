# Copyright 2017-2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
{
    "name": "RMA Purchase",
    "version": "16.0.1.0.0",
    "category": "RMA",
    "summary": "RMA from PO",
    "license": "LGPL-3",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma_account", "purchase"],
    "data": [
        "wizards/rma_order_line_make_purchase_order_view.xml",
        "security/ir.model.access.csv",
        "views/rma_operation_view.xml",
        "views/rma_order_view.xml",
        "views/rma_order_line_view.xml",
        "wizards/rma_add_purchase.xml",
    ],
    "installable": True,
    "auto_install": True,
}
