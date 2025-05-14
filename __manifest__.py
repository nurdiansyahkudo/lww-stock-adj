{
    'name': 'Stock Adjustment Custom',
    'version': '1.0',
    'depends': ['stock'],
    'category': 'Inventory',
    'summary': 'Custom Stock Adjustment Model using stock.adj',
    'data': [
        'views/stock_adj_views.xml',
        'views/stock_adj_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
