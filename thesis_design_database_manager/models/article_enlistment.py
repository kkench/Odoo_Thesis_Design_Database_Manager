from odoo import models, fields, api
from odoo.exceptions import UserError

class ArticleEnlistmentGroup(models.Model):
    _name = "article.enlistment"
    _description = "Students who wish to undergo defense"
    _rec_name = 'term_week_year'
    
    term_week_year = fields.Char("TERM, SCHOOL-YEAR, AND WEEK")
    enlisted_article_ids = fields.Many2many('article.publication','enlistment_article_publication_relation',string="List of Articles for Defense")
    _sql_constraints = [
        ("check_name", "UNIQUE(term_week_year)", "error, already existing enlistment group.")
    ]