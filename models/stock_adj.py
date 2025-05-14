from odoo import models, fields

class StockAdj(models.Model):
    _name = 'stock.adj'
    _description = 'Stock Adjustment'
    _inherits = {'stock.quant': 'quant_id'}

    quant_id = fields.Many2one('stock.quant', required=True, ondelete='cascade')
