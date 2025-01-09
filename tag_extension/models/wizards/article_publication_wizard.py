#add temporary column for descriptvie tags???
from odoo import models, fields, api

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"

    _inherit = "article.import.excel.wizard"

    def act_import_new_article_wizard_part3(self):


    def act_import_new_article_wizard_part2(self):
         return { 
            'type': 'ir.actions.act_window', 
            'name': 'Tag Checking', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_tags').id, 'form')], 
            'target': 'current', }
        #Not sure if return will override super, but this will move part 2 to the tagging system
        #Make sure to create the new view listed here