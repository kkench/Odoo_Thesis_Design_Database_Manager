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
    
    def process_edit_data_for_part_2(self):
       super().process_edit_data_for_part_2()
    
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

    def set_similar_tags(self, temp_record):       
        similar_tag_names = [tag.name for tag in temp_record.similar_tag_ids]
        # print(similar_tag_names)
        similar_tag_names.extend([tag.name for tag in temp_record.existing_tag_ids])
        similar_tag = self.env["article.tag"].search([('name','in', similar_tag_names)])
        # print(type(similar_tag))
       
        return similar_tag
    
    def set_new_tags(self, temp_record):
        tag_list = []
        new_tag_names = [ntag.name for ntag in temp_record.to_create_tag_ids]
        for n_tag in new_tag_names:
            tag_dict = {"name": n_tag}
            tag_list.append(tag_dict)
        new_tag = self.env["article.tag"].create(tag_list)
        return new_tag
    
    # def upload_new_records_to_database(self):
    #     super().upload_new_records_to_database()

    #     for form_record in self.created_article_record_ids:
    #         all_tags = []
    #         tag_list = self.set_similar_tags(form_record)
    #         all_tags.extend(tag_list)
    #         new_tag_obj = self.set_new_tags(form_record)
    #         all_tags.extend(new_tag_obj)
    #         form_record.article_tag_ids = [(6,0,[tag.id for tag in all_tags])]
        
    #     for form_record in self.overwritten_article_record_ids:
    #         all_tags = []
    #         tag_list = self.set_similar_tags(form_record)
    #         all_tags.extend(tag_list)
    #         new_tag_obj = self.set_new_tags(form_record)
    #         all_tags.extend(new_tag_obj)
    #         form_record.article_tag_ids = [(6,0,[tag.id for tag in all_tags])]

    #     return {
    #         'type': 'ir.actions.act_window', 
    #         'name': 'Part 3', 
    #         'view_mode': 'form', 
    #         'res_model': 'article.import.excel.wizard',
    #         'res_id': self.id,
    #         'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
    #         'target': 'current', }

    # def upload_edit_records_to_database(self):
    #     super().upload_edit_records_to_database()

    #     for form_record in self.overwritten_article_record_ids:
    #         all_tags = []
    #         tag_list = self.set_similar_tags(form_record)
    #         all_tags.extend(tag_list)
    #         new_tag_obj = self.set_new_tags(form_record)
    #         all_tags.extend(new_tag_obj)
    #         form_record.article_tag_ids = [(6,0,[tag.id for tag in all_tags])]
        
    #     for form_record in self.updated_article_record_ids:
    #         all_tags = []
    #         tag_list = self.set_similar_tags(form_record)
    #         all_tags.extend(tag_list)
    #         new_tag_obj = self.set_new_tags(form_record)
    #         all_tags.extend(new_tag_obj)
    #         form_record.article_tag_ids = [(6,0,[tag.id for tag in all_tags])]

    #     return {
    #         'type': 'ir.actions.act_window', 
    #         'name': 'Part 3', 
    #         'view_mode': 'form', 
    #         'res_model': 'article.import.excel.wizard',
    #         'res_id': self.id,
    #         'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
    #         'target': 'current', }

    #Realized doesn't matter if this is super'd or not because end product will be combined into one module anyway
    #Above methods don't work unless form_records are recalled so no point as well
    def upload_new_records_to_database(self):
        if not self.wizard_excel_extracted_record_ids or self.wizard_type == "null":
            return  # if blank
        record_created_list = []
        record_overwritten_list = []
        record_failed_list = []
        record_updated_list = []

        for form_record in self.wizard_excel_extracted_record_ids:
            all_tags = []
            tag_list = self.set_similar_tags(form_record)
            all_tags.extend(tag_list)
            if form_record.error_code != 0:
                record_failed_list.append(form_record.id)
                continue
            else:
                new_tag_obj = self.set_new_tags(form_record)
                all_tags.extend(new_tag_obj)
            print(tag.name for tag in all_tags)
            form_record_advisor = self.env['res.users'].search([('name', '=', form_record.adviser)], limit=1)
            row_record_dictionary = {
                'custom_id': form_record.initial_id,
                'name': form_record.name,
                'state': 'proposal',
                'publishing_state': 'not_published',
                'course_name': "thesis" if form_record.course == "T" else "design",
                'abstract': form_record.abstract,
                'author1': form_record.author1,
                'author2': form_record.author2,
                'author3': form_record.author3,
                'adviser_ids': [(6, 0, [form_record_advisor.id])],
                'article_tag_ids': [(6, 0, [tag.id for tag in all_tags])],
            }
            if not form_record.article_to_update_id:
                record = self.env['article.publication'].create(row_record_dictionary)
                record_created_list.append(record.id)
            else:
                record = form_record.article_to_update_id.write(row_record_dictionary)
                record_overwritten_list.append(form_record.article_to_update_id.id)
            
        self.created_article_record_ids = [(6, 0, record_created_list)]
        self.overwritten_article_record_ids = [(6, 0, record_overwritten_list)]
        self.failed_form_submissions_record_ids = [(6, 0, record_failed_list)]
        self.updated_article_records_ids = [(6, 0, record_updated_list)]

        #for record in created/overwritten

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 3', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
            'target': 'current', }
    
    def upload_edit_records_to_database(self):
        record_overwritten_list = []
        record_failed_list = []
        record_updated_list = []

        for temp_record in self.wizard_excel_extracted_record_ids:
            record_dictionary = {'custom_id': temp_record.initial_id,}
            override_everything = int(temp_record.edit_binary_string[0])
            update_title_flag = int(temp_record.edit_binary_string[1])
            update_abstract_flag = int(temp_record.edit_binary_string[2])
            update_tag_flag = int(temp_record.edit_binary_string[3])

            all_tags = []
            tag_list = self.set_similar_tags(temp_record)
            all_tags.extend(tag_list)
            new_tag_obj = self.set_new_tags(temp_record)
            all_tags.extend(new_tag_obj)

            if temp_record.error_code:
                record_failed_list.append(temp_record.id)
                continue
            if update_title_flag or override_everything:
                record_dictionary['name'] = temp_record.name
            if update_abstract_flag or override_everything:
                record_dictionary['abstract'] = temp_record.abstract
            if update_tag_flag or override_everything:
                record_dictionary['article_tag_ids'] = [(6, 0, [tag.id for tag in all_tags])] #input tag update here
                #currently untested
            if override_everything:
                record_dictionary['state'] = 'proposal'
                record_dictionary['publishing_state'] = 'not_published'
            temp_record.article_to_update_id.write(record_dictionary)
            if override_everything:
                record_overwritten_list.append(temp_record.article_to_update_id.id)
            else:
                record_updated_list.append(temp_record.article_to_update_id.id)

        self.overwritten_article_record_ids = [(6, 0, record_overwritten_list)]
        self.failed_form_submissions_record_ids = [(6, 0, record_failed_list)]
        self.updated_article_records_ids = [(6, 0, record_updated_list)]

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 3', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
            'target': 'current', }