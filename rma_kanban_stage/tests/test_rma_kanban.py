# Copyright 2019 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)
from odoo.tests import common


class TestRmaKanban(common.TransactionCase):

    def setUp(self):
        super(TestRmaKanban, self).setUp()

        self.rma_obj = self.env['rma.order']
        self.rma_line_obj = self.env['rma.order.line']
        self.rma_op_obj = self.env['rma.operation']
        self.kanban_stage_model = self.env['base.kanban.stage']
        self.kanban_abstract_model = self.env['base.kanban.abstract']
        self.product_obj = self.env['product.product']
        self.partner_obj = self.env['res.partner']

        self.rma_route_cust = self.env.ref('rma.route_rma_customer')
        self.cust_refund_op = self.env.ref(
            'rma_account.rma_operation_customer_refund')

        # Create partners
        customer1 = self.partner_obj.create({'name': 'Customer 1'})
        # Create RMA group and operation:
        self.rma_group_customer = self.rma_obj.create({
            'partner_id': customer1.id,
            'type': 'customer',
        })

    def test_read_group_stage_ids(self):
        self.assertEqual(
            self.rma_line_obj._read_group_stage_ids(
                self.kanban_stage_model, [], 'id'),
            self.kanban_stage_model.search([], order='id'),
        )

    def test_copy_method(self):
        self.rma_group_customer.copy()
