# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    'name': 'RMA Account',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'RMA',
    'summary': 'Integrates RMA with Invoice Processing',
    'author': "Eficent, Odoo Community Association (OCA)",
    'website': 'https://github.com/Eficent/stock-rma',
    'depends': ['stock_account', 'rma'],
    'demo': ['data/rma_operation.xml'],
    'data': [
        'security/ir.model.access.csv',
        'views/rma_order_view.xml',
        'views/rma_operation_view.xml',
        'views/rma_order_line_view.xml',
        'views/invoice_view.xml',
        'views/rma_account_menu.xml',
        'wizards/rma_add_invoice.xml',
        'wizards/rma_refund.xml',
    ],
    'installable': True,
    'auto_install': True,
}
