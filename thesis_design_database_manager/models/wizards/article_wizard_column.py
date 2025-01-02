from odoo import models, fields, api
import base64
# DEFAULT_COLUMN_DICTIONARY = {'None':'none'}
class ArticleWizardExcelColumn(models.TransientModel):
    _name = "article.wizard.excel.column"

    name = fields.Char("Excel Column", readonly=True)
    official_record_id = fields.Many2one("article.wizard.record.column", "Attribute")
    import_wizard_id = fields.Many2one("article.import.excel.wizard")
    arrow_icon = fields.Html("Updates", compute="_compute_arrow_icon")
    
    @api.depends('name') 
    def _compute_arrow_icon(self): 
        for record in self: 
            record.arrow_icon = f'<i class="fa fa-arrow-right"></i>'

class ArticleWizardRecordColumn(models.TransientModel):
    _name = "article.wizard.record.column"

    name = fields.Char("Name of Record Column")
    excel_record_id = fields.One2many("article.wizard.excel.column","official_record_id")
    import_wizard_id = fields.Many2one("article.import.excel.wizard")