# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.addons.rma.tests import test_rma


class TestRmaAnalytic(test_rma.TestRma):

    def setUp(self):
        super(TestRmaAnalytic, self).setUp()
        products2move = [(self.product_1, 3), (self.product_2, 5),
                         (self.product_3, 2)]
        self.rma_ana_id = self._create_rma_from_move(
            products2move, 'supplier', self.env.ref('base.res_partner_1'),
            dropship=False)

    def _prepare_move(self, product, qty, src, dest, picking_in):
        res = super(TestRmaAnalytic, self)._prepare_move(
            product, qty, src, dest, picking_in)
        analytic_1 = self.env['account.analytic.account'].create({
            'name': 'Test account #1',
        })
        res.update({'analytic_account_id': analytic_1.id})
        return res

    def test_analytic(self):
        for line in self.rma_ana_id.rma_line_ids:
            for move in line.move_ids:
                self.assertEqual(
                    line.analytic_account_id, move.analytic_account_id,
                    "the analytic account is not propagated")
