# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

{
    'name': 'RMA Account',
    'version': '9.0.1.0.0',
    'license': 'LGPL-3',
    'category': 'RMA',
    'summary': 'Integrates RMA with Invoice Processing',
    'author': "Akretion, Camptocamp, Eezee-it, MONK Software, Vauxoo, Eficent,"
              "Odoo Community Association (OCA)",
    'website': 'http://www.github.com/OCA/rma',
    'depends': ['account', 'rma'],
    'demo': ['demo/rma_operation.xml'],
    'data': ['views/rma_order_view.xml',
             'views/rma_operation_view.xml',
             'views/rma_order_line_view.xml',
             'views/invoice_view.xml',
             'wizards/rma_add_invoice.xml',
             'wizards/rma_refund.xml',
             ],
    'installable': True,
    'auto_install': True,
}
