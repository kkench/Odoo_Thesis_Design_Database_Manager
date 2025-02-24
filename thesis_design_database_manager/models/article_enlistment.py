from odoo import models, fields, api
from odoo.exceptions import UserError

class ArticleEnlistmentGroup(models.Model):
    _name = "article.enlistment"
    _description = "Students who wish to undergo defense"
    _rec_name = 'term_week_year'
    
    term_week_year = fields.Char("TERM, SCHOOL-YEAR, AND WEEK")

    