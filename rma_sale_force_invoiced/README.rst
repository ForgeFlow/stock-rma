.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License AGPL-3

=======================
RMA Sale Force Invoiced
=======================

This module allows you to force the sales orders created from RMA order lines
to be set as invoiced once they are created. This use is useful in the
scenario, for example, where you sell goods free of charge and you don't want
to generate an invoice.

Installation
============

This module depends on the module *sale_force_invoiced*, available in
https://github.com/OCA/sale-workflow.

Usage
=====

#. Go to *RMA / Configuration / Customer Operations* and set the flag
*Sale Force Invoiced* to the operation where you'd like to apply this
behaviour.
#. Go to *RMA / Customr RMA* and create a new RMA.
#. Press the button *Create Sale Quotation* available in the RMA.
#. Confirm the sale quotation.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ForgeFlow/stock-rma/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Jordi Ballester Alomar <jordi.ballester@forgeflow.com>


Maintainer
----------

This module is maintained by ForgeFlow
