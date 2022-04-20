import imp
import os

from odoo.modules import get_module_resource
from odoo.tests.common import TransactionCase
from odoo.tools import file_open


class TestMigrations(TransactionCase):
    def test_migration_12_0_3_0_0(self):
        """Test the migration scripts to 12.0.3.0.0 """

        # Recreate pre-migration condition
        self.env.cr.execute("""
            ALTER TABLE product_template
            ADD COLUMN IF NOT EXISTS rma_customer_operation_id INTEGER """)
        self.env.cr.execute("""
            ALTER TABLE product_template
            ADD COLUMN IF NOT EXISTS rma_supplier_operation_id INTEGER """)
        self.env.cr.execute("""
            ALTER TABLE product_category
            ADD COLUMN IF NOT EXISTS rma_customer_operation_id INTEGER """)
        self.env.cr.execute("""
            ALTER TABLE product_category
            ADD COLUMN IF NOT EXISTS rma_supplier_operation_id INTEGER """)

        rma_operation = self.env["rma.operation"].search([], limit=1)
        self.env.cr.execute(
            "UPDATE product_template SET rma_customer_operation_id = %d" % rma_operation.id
        )
        self.env.cr.execute(
            "UPDATE product_template SET rma_supplier_operation_id = %d" % rma_operation.id
        )
        self.env.cr.execute(
            "UPDATE product_category SET rma_customer_operation_id = %d" % rma_operation.id
        )
        self.env.cr.execute(
            "UPDATE product_category SET rma_supplier_operation_id = %d" % rma_operation.id
        )

        # Properties are not set
        product = self.env.ref("product.product_product_5")
        product_tmpl = product.product_tmpl_id
        product_categ = product.categ_id
        self.assertFalse(product_tmpl.rma_customer_operation_id)
        self.assertFalse(product_tmpl.rma_supplier_operation_id)
        self.assertFalse(product_categ.rma_customer_operation_id)
        self.assertFalse(product_categ.rma_supplier_operation_id)

        # Run the migration script
        pyfile = get_module_resource(
            "rma", "migrations", "12.0.3.0.0", "post-migration.py")
        name, ext = os.path.splitext(os.path.basename(pyfile))
        fp, pathname = file_open(pyfile, pathinfo=True)
        mod = imp.load_module(name, fp, pathname, (".py", "r", imp.PY_SOURCE))
        mod.migrate(self.env.cr, "12.0.2.3.0")

        # Properties are set
        product_tmpl.refresh()
        product_categ.refresh()
        self.assertEqual(product_tmpl.rma_customer_operation_id, rma_operation)
        self.assertEqual(product_tmpl.rma_supplier_operation_id, rma_operation)
        self.assertEqual(product_categ.rma_customer_operation_id, rma_operation)
        self.assertEqual(product_categ.rma_supplier_operation_id, rma_operation)
