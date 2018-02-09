# © 2017 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from . import test_rma


class TestRmaDropship(test_rma.TestRma):

    def setUp(self):
        super(TestRmaDropship, self).setUp()
        self.product_id.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        self.product_1.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        self.product_2.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        self.product_3.write(
            {'rma_customer_operation_id': self.rma_cust_replace_op_id.id,
             'rma_supplier_operation_id': self.rma_sup_replace_op_id.id})
        products2move = [(self.product_1, 3), (self.product_2, 5),
                         (self.product_3, 2)]
        self.rma_droship_id = self._create_rma_from_move(
            products2move, 'customer', self.env.ref('base.res_partner_2'),
            dropship=True,
            supplier_address_id=self.env.ref('base.res_partner_3'))

    def test_dropship(self):
        wizard = self.make_supplier_rma.with_context({
            'active_ids': self.rma_droship_id.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'active_id': 1
        }).create({'partner_id': self.partner_id.id,
                   'supplier_rma_id': self.rma_droship_id.id,
                   })

        res = wizard.make_supplier_rma()
        supplier_rma = self.rma.browse(res['res_id'])
        for line in supplier_rma.rma_line_ids:
            line.action_rma_to_approve()
            line.action_rma_approve()
        wizard = self.rma_make_picking.with_context({
            'active_id': 1,
            'active_ids': supplier_rma.rma_line_ids.ids,
            'active_model': 'rma.order.line',
            'picking_type': 'incoming',
        }).create({})
        procurements = wizard._create_picking()
        group_ids = set([proc.group_id.id for proc in procurements if
                         proc.group_id])
        domain = [('group_id', 'in', list(group_ids))]
        picking = self.stockpicking.search(domain)
        self.assertEquals(len(picking), 1,
                          "Incorrect number of pickings created")
        moves = picking.move_lines
        self.assertEquals(len(moves), 3,
                          "Incorrect number of moves created")
        for line in supplier_rma.rma_line_ids:
            # common qtys for all products
            self.assertEquals(line.qty_received, 0,
                              "Wrong qty received")
            self.assertEquals(line.qty_outgoing, 0,
                              "Wrong qty incoming")
            self.assertEquals(line.qty_delivered, 0,
                              "Wrong qty delivered")
            # product specific
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_receive, 3,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_received, 0,
                                  "Wrong qty receive")
                self.assertEquals(line.qty_outgoing, 0,
                                  "Wrong qty outgoing")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_receive, 5,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_delivered, 0,
                                  "Wrong qty deliver")
                self.assertEquals(line.qty_outgoing, 0,
                                  "Wrong qty outgoing")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_receive, 2,
                                  "Wrong qty to receive")
                self.assertEquals(line.qty_delivered, 0,
                                  "Wrong qty deliver")
                self.assertEquals(line.qty_outgoing, 0,
                                  "Wrong qty outgoing")

        for line in self.rma_droship_id.rma_line_ids[0]:
            if line.product_id == self.product_1:
                self.assertEquals(line.qty_to_supplier_rma, 0,
                                  "Wrong qty to supplier rma")
                self.assertEquals(line.qty_in_supplier_rma, 3,
                                  "Wrong qty in supplier rma")
            if line.product_id == self.product_2:
                self.assertEquals(line.qty_to_supplier_rma, 0,
                                  "Wrong qty to supplier rma")
                self.assertEquals(line.qty_in_supplier_rma, 5,
                                  "Wrong qty in supplier rma")
            if line.product_id == self.product_3:
                self.assertEquals(line.qty_to_supplier_rma, 0,
                                  "Wrong qty to supplier rma")
                self.assertEquals(line.qty_in_supplier_rma, 2,
                                  "Wrong qty in supplier rma")
        for line in self.rma_droship_id.rma_line_ids:
            line.action_rma_done()
            self.assertEquals(line.state, 'done',
                              "Wrong State")
