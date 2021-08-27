# Copyright (C) 2021 Open Source Integrators (https://www.opensourceintegrators.com)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Recall",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "To track inventory items by lot number",
    "author": "Open Source Integrators, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma"],
    "data": [
        "security/ir.model.access.csv",
        "data/data.xml",
        "views/rma_recall_view.xml",
    ],
    "installable": True,
}
