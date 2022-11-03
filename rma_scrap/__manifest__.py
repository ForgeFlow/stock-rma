{
    "name": "RMA Put Away",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Allows to put away the received products in odoo",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma"],
    "data": [
        "security/ir.model.access.csv",
        "views/rma_operation_view.xml",
        "views/rma_order_line_view.xml",
        "views/rma_order_view.xml",
        "wizards/rma_scrap_view.xml",
    ],
    "installable": True,
}
