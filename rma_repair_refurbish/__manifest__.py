# Copyright 2020-22 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "RMA Repair Refurbish",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "category": "RMA",
    "summary": "Links RMA with Repairs and Refurbish.",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma_repair", "repair_refurbish"],
    "data": [
        "wizards/rma_order_line_make_repair_view.xml",
        "views/rma_operation_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
