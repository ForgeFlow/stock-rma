# -*- coding: utf-8 -*-
# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests import common


class TestRmaAnalytic(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestRmaAnalytic, cls).setUpClass()
        products2move = [(cls.product_1, 3), (cls.product_2, 5),
                         (cls.product_3, 2)]
        analytic_1 = cls.env['account.analytic.account'].create({
            'name': 'Test account #1',
        })
        cls.rma_ana_id = cls._create_rma_analytic(
            products2move, 'supplier', cls.env.ref('base.res_partner_1'),
            analytic=analytic_1)

    @classmethod
    def _prepare_anal_move(cls, product, qty, src, dest, picking_in, analytic):
        res = {
            'partner_id': cls.partner_id.id,
            'product_id': product.id,
            'name': product.partner_ref,
            'state': 'confirmed',
            'product_uom': cls.product_uom_id.id or product.uom_id.id,
            'product_uom_qty': qty,
            'origin': 'Test RMA',
            'location_id': src.id,
            'location_dest_id': dest.id,
            'picking_id': picking_in.id,
            'analytic_account_id': analytic.id,
        }
        return res

    @classmethod
    def _create_rma_analytic(cls, products2move, type, partner, analytic):
        picking_in = cls._create_picking(partner)
        moves = []
        for item in products2move:
            move_values = cls._prepare_anal_move(
                item[0], item[1], cls.supplier_location,
                cls.stock_rma_location, picking_in, analytic)
            moves.append(cls.env['stock.move'].create(move_values))
        # Create the RMA from the stock_move
        rma_id = cls.rma.create(
            {
                'reference': '0001',
                'type': type,
                'partner_id': partner.id,
                'company_id': cls.env.ref('base.main_company').id
            })
        for move in moves:
            wizard = cls.rma_add_stock_move.with_context(
                {'stock_move_id': move.id, 'supplier': True,
                 'active_ids': rma_id.id,
                 'active_model': 'rma.order',
                 }
            ).create({'rma_id': rma_id.id,
                      'partner_id': partner.id})
            data = wizard._prepare_rma_line_from_stock_move(move)
            wizard.add_lines()

            wizard = cls.rma_add_stock_move.with_context(
                {'stock_move_id': move.id, 'supplier': True,
                 'active_ids': [],
                 'active_model': 'rma.order',
                 }
            ).create({})
            wizard.add_lines()
            wizard.add_lines()
            wizard._prepare_rma_line_from_stock_move(move)
            wizard.add_lines()

            cls.line = cls.rma_line.create(data)
            # approve the RMA Line
            cls.line.action_rma_to_approve()
            cls.line.action_rma_approve()
        rma_id._get_default_type()
        rma_id._compute_in_shipment_count()
        rma_id._compute_out_shipment_count()
        rma_id._compute_supplier_line_count()
        rma_id._compute_line_count()
        rma_id.action_view_in_shipments()
        rma_id.action_view_out_shipments()
        rma_id.action_view_lines()

        rma_id.partner_id.action_open_partner_rma()
        rma_id.partner_id._compute_rma_line_count()
        return rma_id

    def test_analytic(cls):
        for line in cls.rma_ana_id.rma_line_ids:
            for move in line.move_ids:
                cls.assertEqual(
                    line.analytic_account_id, move.analytic_account_id,
                    "the analytic account is not propagated")
