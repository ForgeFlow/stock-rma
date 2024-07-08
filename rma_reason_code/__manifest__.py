# Copyright 2024 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "RMA Reason Code",
    "version": "14.0.1.1.0",
    "license": "AGPL-3",
    "summary": "Reason code for RMA",
    "author": "ForgeFlow",
    "website": "https://github.com/ForgeFlow/stock-rma",
    "category": "Warehouse Management",
    "depends": ["rma"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/reason_code_view.xml",
        "views/rma_order_line_views.xml",
        "reports/rma_reason_code_report_views.xml",
    ],
    "installable": True,
}
