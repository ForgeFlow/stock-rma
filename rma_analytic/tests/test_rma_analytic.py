# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.addons.rma.tests import test_rma


class TestRmaAnalytic(test_rma.TestRma):

    @classmethod
    def setUp(cls):
        super(TestRmaAnalytic, cls).setUp()
        products2move = [(cls.product_1, 3), (cls.product_2, 5),
                         (cls.product_3, 2)]
        cls.rma_ana_id = cls._create_rma_from_move(
            products2move, 'supplier', cls.env.ref('base.res_partner_1'),
            dropship=False)

    @classmethod
    def _prepare_move(cls, product, qty, src, dest, picking_in):
        res = super(TestRmaAnalytic, cls)._prepare_move(
            product, qty, src, dest, picking_in)
        analytic_1 = cls.env['account.analytic.account'].create({
            'name': 'Test account #1',
        })
        res.update({'analytic_account_id': analytic_1.id})
        return res

    def test_analytic(cls):
        for line in cls.rma_ana_id.rma_line_ids:
            for move in line.move_ids:
                cls.assertEqual(
                    line.analytic_account_id, move.analytic_account_id,
                    "the analytic account is not propagated")
