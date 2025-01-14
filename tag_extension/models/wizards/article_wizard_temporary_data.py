from odoo import api,fields,models

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.wizard.publications"
    checking_wizard_id = fields.Many2one("article.import.excel.wizard")
