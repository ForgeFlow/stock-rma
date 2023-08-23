# Copyright (C) 2022 ForgeFlow S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA delivery integration",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "RMA default carrier on operation" "in odoo",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "depends": ["rma", "delivery"],
    "demo": [],
    "data": [
        "views/rma_operation_view.xml",
    ],
    "installable": True,
    "application": False,
    "development_status": "Beta",
    "maintainers": ["ChrisOForgeFlow"],
}
