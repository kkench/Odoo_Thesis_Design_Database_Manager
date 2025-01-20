from odoo import models, fields, api

class ArticleTag(models.Model):
    _inherit = "article.tag"
    # similar_temp_tag_ids = fields.Many2many("article.wizard.publication","article_tag_similar")
    existing_temp_tag_ids = fields.Many2many("article.wizard.publication", "article_tag_existing")

    # def assign_existing(self, tag):
    #     existing_tag = self.env['article.tag'].search([tag])
    #     existing_temp_tag_ids = [(6,0,existing_tag.id)]
    # abbv_ids = fields.One2many("article.tag.abb","definition_id",string="Abbreviated Tag")

# class ArticleAbbreviatedTag(models.Model): #make this transient to resolve for user?
#     _name = "article.tag.abb"
#     definition_id = fields.Many2one("article.tag",string="Abbreviation Definition")
