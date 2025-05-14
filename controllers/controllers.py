# -*- coding: utf-8 -*-
# from odoo import http


# class LwwStockAdj(http.Controller):
#     @http.route('/lww_stock_adj/lww_stock_adj', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/lww_stock_adj/lww_stock_adj/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('lww_stock_adj.listing', {
#             'root': '/lww_stock_adj/lww_stock_adj',
#             'objects': http.request.env['lww_stock_adj.lww_stock_adj'].search([]),
#         })

#     @http.route('/lww_stock_adj/lww_stock_adj/objects/<model("lww_stock_adj.lww_stock_adj"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('lww_stock_adj.object', {
#             'object': obj
#         })

