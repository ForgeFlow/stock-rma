import logging

_logger = logging.getLogger(__name__)


def set_rma_customer_operation_property(cr):
    """ """
    cr.execute(
        """
        WITH rma_customer_operation_id_field AS (
            SELECT id FROM ir_model_fields WHERE model='product.template'
            AND name='rma_customer_operation_id'
        )
        INSERT INTO ir_property(name, type, fields_id, company_id, res_id,
            value_reference)
        SELECT 'rma_customer_operation_id', 'many2one', rco.id, ro.company_id,
            CONCAT('product.template,', t.id), CONCAT('rma.operation,', ro.id)
        FROM product_template t JOIN rma_operation ro
            ON t.rma_customer_operation_id = ro.id
        , rma_customer_operation_id_field rco
        WHERE ro.company_id IS NOT NULL
              AND NOT EXISTS(SELECT 1
                             FROM ir_property
                             WHERE fields_id=rco.id
                                AND company_id=ro.company_id
                                AND res_id=CONCAT('product.template,', t.id))
    """
    )
    _logger.info(
        "Added %s rma_customer_operation_id_field product properties", cr.rowcount
    )


def set_rma_supplier_operation_property(cr):
    """ """
    cr.execute(
        """
        WITH rma_supplier_operation_id_field AS (
            SELECT id FROM ir_model_fields WHERE model='product.template'
                AND name='rma_supplier_operation_id'
        )
        INSERT INTO ir_property(name, type, fields_id, company_id, res_id,
            value_reference)
        SELECT 'rma_supplier_operation_id', 'many2one', rco.id, ro.company_id,
            CONCAT('product.template,', t.id), CONCAT('rma.operation,', ro.id)
        FROM product_template t JOIN rma_operation ro
            ON t.rma_supplier_operation_id = ro.id
        , rma_supplier_operation_id_field rco
        WHERE ro.company_id IS NOT NULL
              AND NOT EXISTS(SELECT 1
                             FROM ir_property
                             WHERE fields_id=rco.id
                                AND company_id=ro.company_id
                                AND res_id=CONCAT('product.template,', t.id))
    """
    )
    _logger.info(
        "Added %s rma_supplier_operation_id_field product properties", cr.rowcount
    )


def set_rma_customer_operation_category_property(cr):
    """ """
    cr.execute(
        """
        WITH rma_customer_operation_id_field AS (
            SELECT id FROM ir_model_fields WHERE model='product.category'
                AND name='rma_customer_operation_id'
        )
        INSERT INTO ir_property(name, type, fields_id, company_id, res_id,
            value_reference)
        SELECT 'rma_customer_operation_id', 'many2one', rco.id, ro.company_id,
            CONCAT('product.category,', pc.id), CONCAT('rma.operation,', ro.id)
        FROM product_category pc JOIN rma_operation ro
            ON pc.rma_customer_operation_id = ro.id
        , rma_customer_operation_id_field rco
        WHERE ro.company_id IS NOT NULL
              AND NOT EXISTS(SELECT 1
                             FROM ir_property
                             WHERE fields_id=rco.id
                                AND company_id=ro.company_id
                                AND res_id=CONCAT('product.category,', pc.id))
    """
    )
    _logger.info(
        "Added %s rma_customer_operation_id_field product category properties",
        cr.rowcount,
    )


def set_rma_supplier_operation_category_property(cr):
    """ """
    cr.execute(
        """
        WITH rma_supplier_operation_id_field AS (
            SELECT id FROM ir_model_fields WHERE model='product.category'
                AND name='rma_supplier_operation_id'
        )
        INSERT INTO ir_property(name, type, fields_id, company_id, res_id,
            value_reference)
        SELECT 'rma_supplier_operation_id', 'many2one', rco.id, ro.company_id,
            CONCAT('product.category,', pc.id), CONCAT('rma.operation,', ro.id)
        FROM product_category pc JOIN rma_operation ro
            ON pc.rma_supplier_operation_id = ro.id
        , rma_supplier_operation_id_field rco
        WHERE ro.company_id IS NOT NULL
              AND NOT EXISTS(SELECT 1
                             FROM ir_property
                             WHERE fields_id=rco.id
                                AND company_id=ro.company_id
                                AND res_id=CONCAT('product.category,', pc.id))
    """
    )
    _logger.info(
        "Added %s rma_supplier_operation_id_field product category properties",
        cr.rowcount,
    )


def migrate(cr, version=None):
    if not version:
        return
    set_rma_customer_operation_property(cr)
    set_rma_supplier_operation_property(cr)
    set_rma_customer_operation_category_property(cr)
    set_rma_supplier_operation_category_property(cr)
