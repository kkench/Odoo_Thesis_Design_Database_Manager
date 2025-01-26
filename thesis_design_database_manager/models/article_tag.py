from odoo import api, fields, models

class ArticleTag(models.Model):
    _name = "article.tag"
    _description = "Tags for Scanning Similarities"
    _sql_constraints = [
        ("check_name", "UNIQUE(name)", "Name must be unique.")
    ] #probably add check for something like "CNN", "cnn" and "Convolutional Neural Network"

    name = fields.Char(string='Name', required=True)

    article_publication_ids = fields.Many2many("article.publication", "paper_tag_ids", string="Related Publications")