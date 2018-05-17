# -*- coding: utf-8 -*-
# Copyright 2017-18 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from openerp.tests import common


class TestRmaQcIssue(common.SingleTransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaQcIssue, cls).setUpClass()

        cls.rma_obj = cls.env['rma.order']
        cls.rma_line_obj = cls.env['rma.order.line']
        cls.rma_op_obj = cls.env['rma.operation']
        cls.qc_issue_make_rma_wiz = cls.env['qc.issue.make.supplier.rma']
        cls.qc_issue_obj = cls.env['qc.issue']
        cls.partner_obj = cls.env['res.partner']
        cls.product_obj = cls.env['product.product']

        # Create supplier
        cls.supplier1 = cls.partner_obj.create({'name': 'Supplier 1'})

        # Create products
        cls.product_1 = cls.product_obj.create({
            'name': 'Test Product 1',
            'type': 'product',
        })

        # Create Quality Control issue:
        cls.issue = cls.qc_issue_obj.create({
            'product_id': cls.product_1.id,
            'product_qty': 5.0,
            'product_uom': cls.product_1.uom_id.id,
        })

    def test_01_create_rma_from_qc_issue(self):
        """Test wizard to create supplier RMA from Quality Control issue."""
        self.issue.action_confirm()
        self.assertEqual(self.issue.rma_line_count_supplier, 0)
        wiz_supp = self.qc_issue_make_rma_wiz.with_context({
            'active_ids': self.issue.ids,
            'active_model': 'qc.issue',
        }).create({
            'partner_id': self.supplier1.id,
        })
        wiz_supp.make_supplier_rma()
        self.assertEqual(self.issue.rma_line_count_supplier, 1)
        self.assertEqual(self.issue.rma_line_ids[0].type, 'supplier')
        self.assertEqual(self.issue.rma_line_ids[0].qc_issue_id, self.issue)
