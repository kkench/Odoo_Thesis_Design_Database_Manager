from odoo import models, fields, api

class ArticleTag(models.Model):
    _inherit = "article.tag"
    # abbv_ids = fields.One2many("article.tag.abb","definition_id",string="Abbreviated Tag")

# class ArticleAbbreviatedTag(models.Model): #make this transient to resolve for user?
#     _name = "article.tag.abb"
#     definition_id = fields.Many2one("article.tag",string="Abbreviation Definition")
