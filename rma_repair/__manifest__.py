# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Repair",
    "version": "11.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Links RMA with Repairs.",
    "author": "Eficent, Odoo Community Association (OCA)",
    "website": "http://www.github.com/OCA/rma",
    "depends": ["rma_account", "mrp_repair_refurbish"],
    "data": ["views/rma_order_view.xml",
             "views/rma_operation_view.xml",
             "views/mrp_repair_view.xml",
             "wizards/rma_order_line_make_repair_view.xml",
             "views/rma_order_line_view.xml",
             "data/mrp_repair_sequence.xml",
             ],
    "installable": True,
    "auto_install": True,
}
