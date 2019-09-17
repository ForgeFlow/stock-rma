# Copyright 2019 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
{
    'name': 'RMA Kanban Stages',
    'summary': 'Stages on RMA',
    'version': '12.0.1.1.0',
    'website': 'https://www.eficent.com/',
    'author': 'Eficent',
    'depends': [
        'rma',
        'base_kanban_stage',
    ],
    'data': [
        'views/rma_order_line_view.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
}
