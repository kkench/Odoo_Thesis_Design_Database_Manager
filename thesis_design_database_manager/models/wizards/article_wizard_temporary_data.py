from odoo import api,fields,models
import re

class ArticleWizardPublication(models.TransientModel):
    _name = "article.wizard.publications"
    _description = "Sample list of what will be uploaded"

    name = fields.Char("Title")
    course = fields.Char("Course Name")
    initial_id = fields.Char("ID",compute="_compute_errors_and_id",readonly=True)
    uploader_email = fields.Char("Uploader Email", readonly=True)
    uploader_name = fields.Char("Uploader Name", readonly=True)
    # registration_date = fields.date("Date Registered")
    # last_edited = fields.date("Last Edited")
    abstract = fields.Text("Abstract")
    author1 = fields.Char("Author1")
    author2 = fields.Char("Author2")
    author3 = fields.Char("Author3")
    adviser = fields.Char("ADVISER")
    student_number_1 = fields.Char("Student Number 1")
    student_number_2 = fields.Char("Student Number 2")
    student_number_3 = fields.Char("Student Number 3")
    error_comment = fields.Char("Comments",compute="_compute_errors_and_id")
    article_2_flag = fields.Boolean("Check if Article 2",default=False)

    tags = fields.Text("TAGS")
    error_code = fields.Integer("Error Code Number", default=0,compute="_compute_errors_and_id", readonly=True)

    import_wizard_id = fields.Many2one("article.import.excel.wizard")
    failed_import_wizard_id = fields.Many2one("article.import.excel.wizard")

    @api.depends('author1', 'author2', 'author3', 'uploader_email', 'tags', 'student_number_1', 'student_number_2', 'student_number_3', 'adviser')
    def _compute_errors_and_id(self):
        ''' Error Codes:
        0 - No Errors
        1 - Incorrect Name Format (Cannot Read) DONE
        2 - Student is not the editor DONE
        3 - Cannot Search Adviser DONE
        4 - Student Number Does Not Follow Proper Formatting
        5 - 3rd Author Exists on Thesis
        6 - Duplicate Record
        7 - Tags Stuff

        OTHER STUFF:
        - Automatically arrange authors by name
        - Get initial ID 
        '''
        for record in self:
            record.error_comment = None
            record.initial_id = None
            record.error_code = 0
            if not record.is_author_name_valid():
                record.error_code = 1
            elif not record.does_author_email_and_name_match(): 
                record.error_code = 2
            elif not record.adviser_is_searchable():
                record.error_code = 3
            elif not record.is_student_number_in_format():
                record.error_code = 4
            elif record.course == "D" and (None in [record.author1,record.author2,record.author3]): # only max 2 authors for thesis
                record.error_code = 5
            elif not record.tags_are_valid():
                record.error_code = 7
            if record.error_code == 0: 
                record.cleanup() ##Includes checking for duplicate (error 6)
                
    def is_author_name_valid(self):
        pattern_name = r'^[A-Za-z]+, ([A-Za-z]+ )+[A-Za-z]\.$'  # LN, FN MI
        if not (self.author1 or self.author2 or self.author3): return False
        for author_name in [self.author1, self.author2, self.author3]:
            if not author_name: continue
            if not re.match(pattern_name, author_name):
                self.error_comment = f"{author_name}, is not proper name format!"
                return False
        return True

    def does_author_email_and_name_match(self):
        pattern_mymail = r'^[a-zA-Z0-9._%+-]+@mymail\.mapua\.edu\.ph$'
        if not re.match(pattern_mymail, self.uploader_email):
            self.error_comment = "Uploader is not from Mapua"
        for author_name in [self.author1, self.author2, self.author3]:
            email_check = self.create_email_from_format(author_name) == self.uploader_email
            name_check = self.create_name_from_format_of_author(author_name) == self.uploader_name
            if email_check and name_check:
                return True
        self.error_comment = "Any of the author does not match uploader name or email"
        return False #did not match any

    def create_email_from_format(self,name):
        if not isinstance(name, str): return "error"
        last_name, first_name_middle_initial = name.split(', ')
        first_names, middle_initial = first_name_middle_initial.rsplit(' ', 1)
        email = f"{''.join([name[0].lower() for name in first_names.split()])}{middle_initial[0].lower()}{last_name.lower()}@mymail.mapua.edu.ph"
        return email
    
    def create_name_from_format_of_author(self,name):
        if not isinstance(name, str): return "error"
        upper_name = name.upper()
        last_name, first_name_middle_initial = upper_name.split(', ')
        first_names, _ = first_name_middle_initial.rsplit(' ', 1)
        return first_names + " " + last_name
    
    def adviser_is_searchable(self):
        return self.env['res.users'].search([('name', '=', self.adviser)], limit=1)
    
    def cleanup(self):
        self.arrange_authors_alphabetically()
        self._update_initial_id()
        self.check_for_duplicate()
        self.clear_newline_from_abstract_and_title()

    def arrange_authors_alphabetically(self):
        for record in self:
            # Collect author names and filter out None values
            author_student_number = {
                record.author1:record.student_number_1, 
                record.author2:record.student_number_2, 
                record.author3:record.student_number_3,
            }
            author_names = [name for name in [record.author1, record.author2, record.author3] if name]

            # Sort the names alphabetically
            sorted_names = sorted(author_names)

            # Fill with None to ensure the list has 3 elements
            sorted_names.extend([None] * (3 - len(sorted_names)))
            sorted_student_number = [author_student_number[author_name] if author_name else None for author_name in sorted_names]
            # print(sorted_student_number)
            # Update the record with sorted names
            record.author1, record.author2, record.author3 = sorted_names
            record.student_number_1, record.student_number_2, record.student_number_3 = sorted_student_number

    def _update_initial_id(self):
        #--------------GET THE LAST NAMES IN ORDER----------------------
        self.initial_id = self.author1.split(', ')[0] #last name
        self.initial_id += self.author2.split(', ')[0] if self.author2 else ""
        self.initial_id += self.author3.split(', ')[0] if self.author3 else ""
        #-------------------------------------------------------------
        #-------------Get latest student Number as year----------------
        #student number is not perfect representation of the year of the student as shs sn exists
        latest_student_number = int(self.student_number_1[0:4])
        for student_number in [self.student_number_2,self.student_number_3,]:
            if not student_number:break
            current_yr = int(student_number[0:4])
            latest_student_number = current_yr if latest_student_number<current_yr else latest_student_number

        self.initial_id += "_" + str(latest_student_number)
        #---------------------------------------------------------
        #-------------Include Course Initial------------------
        self.initial_id += "_" + self.course
        #-------------For Thesis Articles-----------------------
        self.initial_id += "_Art2" if self.article_2_flag else "_Art1"
        # print(self.initial_id) #[LN123]_[BATCH YEAR]_[Article Number if thesis]

    def is_student_number_in_format(self):
        for student_number in [self.student_number_1,self.student_number_2,self.student_number_3]:
            if not student_number:
                continue
            pattern = r'^20\d{2}\d{6}$'
            if not re.match(pattern,student_number):
                return False
        return True

    def check_for_duplicate(self):
        for record in self:
            # Convert the initial_id to a compatible data type if necessary
            initial_id = record.initial_id if record.initial_id else None
            
            # Search for existing records with the same name and initial_id
            existing_records = self.search([
                ('name', '=', record.name),
                ('initial_id', '=', initial_id),
                ('id', '!=', record.id), # Exclude the current record   
                ('import_wizard_id', '=', record.import_wizard_id.id), # Corrected condition
            ])
            if existing_records:
                record.error_code = 6  # Duplicate Record
                return False
        return True

    def clear_newline_from_abstract_and_title(self):
        for record in self:
            print("Got Here")
            if not record.abstract: continue
            abstract = record.abstract 
            abstract = re.sub(r'\n+', ' ', abstract)
            abstract = re.sub(r'\s{2,}', ' ', abstract)
            record.abstract = abstract
            
            title = record.name
            title = re.sub(r'\n+', ' ', title)
            title = re.sub(r'\s{2,}', ' ', title)
            record.name = title
            
    def tags_are_valid(self):
        return True