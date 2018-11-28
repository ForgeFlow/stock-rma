# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    "name": "RMA Quality Control Issue",
    "version": "11.0.1.0.0",
    "license": "LGPL-3",
    "category": "RMA",
    "summary": "Add the possibility to create RMAs from quality control "
               "issues.",
    "author": "Eficent, Odoo Community Association (OCA)",
    "website": "http://www.github.com/OCA/rma",
    "depends": [
        "rma",
        "quality_control_issue"
    ],
    "data": [
        "views/qc_issue_view.xml",
        "wizard/qc_issue_make_supplier_rma_view.xml",
        "views/rma_order_line_view.xml",
    ],
    "installable": True,
    "auto_install": True,
}
