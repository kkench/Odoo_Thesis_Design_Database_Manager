from odoo import fields,models

class ArticlePaper(models.Model):
    _name = "article.paper"
    _description = "Main Study/ies of CpE Students"

    name = fields.Char(string="Name")
    description = fields.Text(string="Article Description")
    