from odoo import api, fields, models

class PaperInfo(models.Model):
    _name = "paper.info"
    _order = "add_date desc" #order by date on initial open then sort by alphabetical later? 

    name = fields.Char(string="Paper Title", required=True)
    add_date = fields.Date(string="Date Added")
    state = fields.Selection(string="Current Status",
                             required=True,
                             selection=[
                                 ("proposed", "Proposed"),
                                 ("defense1", "Proposal Defense Complete"),
                                 ("defense2", "Final Defense Complete"),
                                 ("published", "Published") #published and presented combined because this isnt a status tracker, just a similarity checker
                             ])
    publish = fields.Boolean(string="Publication Status") #if published and presented before defended? should probably add function check with status

    paper_tag_ids = fields.Many2one("paper.info.tags", "paper_tag", string="Tags") #split topic-related tags and system tags? (i.e. "Embedded Systems" as "department/spec/type" tag and "Fish"  as "topic focus" tag respectively)
#add res users as teacher account?
#add csv importation