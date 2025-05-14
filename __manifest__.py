# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'LWW Stock Adjustment',
    'version': '1.1',
    'summary': 'Manage your stock and logistics activities',
    'website': '',
    'depends': ['product', 'barcodes_gs1_nomenclature', 'digest'],
    'category': 'Inventory/Inventory',
    'sequence': 25,
    'data': [
        'report/report_stock_quantity.xml',

        'wizard/stock_quantity_history.xml',
        'wizard/stock_quant_relocate.xml',

        'views/stock_adj_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
