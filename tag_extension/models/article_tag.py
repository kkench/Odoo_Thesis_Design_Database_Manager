from odoo import api, fields, models

class ArticleTag(models.Model):
    _name = "article.tag"
    _description = "Tags for Scanning Similarities"
    _inherit = "article.tag"

    category = fields.Selection(string="Tag Category",
                                    required=True,
                                    selection=[
                                                ("field", "field"),
                                                ("descriptive", "descriptive")
                                                ],
                                    default="descriptive")
