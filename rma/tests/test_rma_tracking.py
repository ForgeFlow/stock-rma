# © 2022 ForgeFlow
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html)

from odoo.tests.common import TransactionCase


class TestRmaTracking(TransactionCase):
    def setUp(self):
        super().setUp()
        self.rma_add_stock_move = self.env["rma_add_stock_move"]
        self.rma_make_picking = self.env["rma_make_picking.wizard"]
        self.serial_model = self.env["stock.production.lot"]
        self.quant_model = self.env["stock.quant"].with_context(inventory_mode=True)
        self.quant_package_model = self.env["stock.quant.package"]
        self.location_id = self.env.ref("stock.warehouse0").lot_stock_id
        self.product_lot = self.env["product.product"].create(
            {
                "name": "Lot Product",
                "standard_price": 10,
                "tracking": "lot",
                "type": "product",
            }
        )
        self.product_serial = self.env["product.product"].create(
            {
                "name": "Lot Product",
                "standard_price": 10,
                "tracking": "serial",
                "type": "product",
            }
        )
        self.lot_1 = self.serial_model.create(
            {
                "product_id": self.product_lot.id,
                "company_id": self.env.company.id,
            }
        )
        self.lot_2 = self.serial_model.create(
            {
                "product_id": self.product_lot.id,
                "company_id": self.env.company.id,
            }
        )
        self.serial_1 = self.serial_model.create(
            {
                "product_id": self.product_serial.id,
                "company_id": self.env.company.id,
            }
        )
        self.serial_2 = self.serial_model.create(
            {
                "product_id": self.product_serial.id,
                "company_id": self.env.company.id,
            }
        )
        self.serial_3 = self.serial_model.create(
            {
                "product_id": self.product_serial.id,
                "company_id": self.env.company.id,
            }
        )
        self.package_1 = self.quant_package_model.create({})
        self.package_2 = self.quant_package_model.create({})
        self.package_3 = self.quant_package_model.create({})
        self.quant_model.create(
            {
                "product_id": self.product_lot.id,
                "lot_id": self.lot_1.id,
                "inventory_quantity": 100,
                "location_id": self.location_id.id,
            }
        )
        self.quant_model.create(
            {
                "product_id": self.product_lot.id,
                "lot_id": self.lot_2.id,
                "inventory_quantity": 100,
                "location_id": self.location_id.id,
            }
        )
        self.quant_model.create(
            {
                "product_id": self.product_serial.id,
                "lot_id": self.serial_1.id,
                "inventory_quantity": 1,
                "location_id": self.location_id.id,
            }
        )
        self.quant_model.create(
            {
                "product_id": self.product_serial.id,
                "lot_id": self.serial_2.id,
                "inventory_quantity": 1,
                "location_id": self.location_id.id,
            }
        )
        self.quant_model.create(
            {
                "product_id": self.product_serial.id,
                "lot_id": self.serial_3.id,
                "inventory_quantity": 1,
                "location_id": self.location_id.id,
            }
        )

    def test_01_customers(self):
        pass
