from odoo import models, fields, api
from odoo.exceptions import UserError

class ArticleEnlistmentGroup(models.Model):
    _name = "article.enlistment"
    _description = "Students who wish to undergo defense"
    
    name = fields.Char("TERM, SCHOOL-YEAR, AND WEEK")