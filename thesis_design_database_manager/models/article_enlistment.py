from odoo import models, fields, api
from odoo.exceptions import UserError

class ArticleEnlistmentGroup(models.Model):
    _name = "article.enlistment"
    _description = "Students who wish to undergo defense"
    _rec_name = 'term_week_year_course'
    
    term_week_year_course = fields.Char("TERM, SCHOOL-YEAR, AND WEEK")
    enlisted_article_ids = fields.Many2many('article.publication','enlistment_article_publication_relation',string="List of Articles for Defense")
    course_name = fields.Selection(string="Course",
                                    required=True,
                                    selection=[
                                                ("design", "Design"),
                                                ("thesis", "Thesis")
                                                ],
                                    default="thesis")
    _sql_constraints = [
        ("check_name", "UNIQUE(term_week_year_course)", "error, already existing enlistment group.")
    ]