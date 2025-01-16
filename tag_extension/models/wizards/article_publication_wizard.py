#add temporary column for descriptvie tags???
from odoo import models, fields, api
from difflib import SequenceMatcher, get_close_matches

class ArticleImportExcelWizard(models.TransientModel):
    _description = "Import Your Article Excel Files"
    _inherit = "article.import.excel.wizard"

    wizard_check_tags_records_ids = fields.One2many('article.wizard.publication','checking_wizard_id','List of Records for Checking')

    def process_new_data_for_part_2(self):
       super().process_new_data_for_part_2()
    
       return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2-2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('tag_extension.article_import_excel_wizard_form_view_tags').id, 'form')], 
            'target': 'current', }
    
    def act_go_to_view_part2(self):
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    def act_set_tags(self):       
        for temp_record in self.wizard_check_tags_records_ids:
            tags_record = [] 
            similar_tag_names = [stag.name for stag in temp_record.similar_tag_ids]
            new_tag_names = [ntag.name for ntag in temp_record.for_checking_tag_ids]
            for n_tag in new_tag_names:
               new_tag = self.env["article.tag"].create({'name': n_tag.name})
               tags_record.append(new_tag.id)
            similar_tag = self.env["article.tag"].search([('name','in', similar_tag_names)])
            tags_record.append(similar_tag.id)
            

            
            


    #def process_edit_data_for_part_2(self):

    # def act_import_new_article_wizard_part3(self):
    #run similarity check, abbreviation check then move to tag adjustment page
        

    # def process_new_data_for_part_2(self):
    #     excel_df = self._get_wizard_df()
    #     new_article_list = []
    #     for_checking_list = []
    #     for index, row in excel_df.iterrows():
    #         #---------Static Article Information--------------
    #         row_data_dictionary = self._get_initial_temp_data(row)
    #         #-------------------------------------------------

    #         #----------Excel to Official Column Information-------------
    #         for excel_column_record in self.excel_column_ids:
    #             if not excel_column_record.official_record_id:
    #                 continue    
    #             row_data_dictionary[self.LABEL_TO_RECORD_DICTIONARY[excel_column_record.official_record_id.name]] = row[excel_column_record.name]
    #         new_article = self.env['article.wizard.publication'].create(row_data_dictionary)
    #         changed = self.get_tag_changes(new_article)
    #         if changed:
    #             for_checking_list.append(new_article.id)
    #         else:
    #             new_article_list.append(new_article.id)
    #         #------------------------------------------------------------
    #     self.wizard_check_tags_records_ids = [(6, 0, for_checking_list)]
    #     # temporarily fill it with changed IDs
    #     self.wizard_excel_extracted_record_ids = [(6, 0, new_article_list)]
    #     #for record in wizard_new_record_ids

    #     return { 
    #         'type': 'ir.actions.act_window', 
    #         'name': 'Tag Checking', 
    #         'view_mode': 'form', 
    #         'res_model': 'article.import.excel.wizard',
    #         'res_id': self.id,
    #         'views': [(self.env.ref('tag_extension.article_import_excel_wizard_form_view_tags').id, 'form')],  
    #         'target': 'current', }
        #Not sure if return will override super, but this will move part 2 to the tagging system
        #Make sure to create the new view listed here