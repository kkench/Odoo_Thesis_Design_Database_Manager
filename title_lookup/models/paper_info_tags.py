from odoo import api, fields, models

class PaperInfoTag(models.Model):
    _name = "paper.info.tag"
    _sql_constraints = [
        ("check_name", "UNIQUE(name)", "Name must be unique.")
    ] #probably add check for something like "CNN", "cnn" and "Convolutional Neural Network"

    name = fields.Char(string='Name', required=True)