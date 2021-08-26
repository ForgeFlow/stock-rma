===========
RMA Recalls
===========

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-LGPL--3-blue.png
    :target: http://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

|badge1| |badge2|

This module allows you to manage recalls, find where the compromised product/lot is
located and create the corresponding document to track the status:

* scrap order if the product is located in a warehouse
* RMA order if the product has already been shipped to a customer

The module supports compromised products used as a component in a manufacturing order
and creates a recall line for the finished good.

**Table of contents**

.. contents::
   :local:

Usage
=====

* Go to RMA
* Create a recall
* Select the lot/serial number
* Click on "Search"
* For each of the line, create a scrap order or RMA order

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/ForgeFlow/stock-rma/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Authors
-------

* Open Source Integrators <contact@opensourceintegrators.com>

Contributors
------------
* Open Source Integrators <contact@opensourceintegrators.com>

  * Melody Fetterly <mfetterly@opensourceintegrators.com>
  * Raphael Lee <rlee@opensourceintegrators.com>
  * Maxime Chambreuil <mchambreuil@opensourceintegrators.com>
  * Vimal Patel <vpatel@opensourceintegrators.com>

Maintainers
-----------

This module is maintained by ForgeFlow.

This module is part of the `ForgeFlow/stock-rma <https://github.com/ForgeFlow/stock-rma>`_ project on GitHub.
