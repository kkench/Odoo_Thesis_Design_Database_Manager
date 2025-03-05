from odoo import api,models, fields
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = "res.users"

    # rpi_password = fields.Char(string='RPI Password', widget='password')

    article_publication_ids = fields.Many2many(
        "article.publication",
        "article_publication_res_users_rel",
        "user_id",
        "publication_id",
        string="Article Publications", readonly=True
    )

    conformity_publication_filter_ids = fields.Many2many(
        "article.publication",
        "article_publication_conformity_filter_rel",
        string="Articles For Conformity", readonly=True,
        compute="_compute_conformity_publications"
    )

    publication_non_scopus_filter_ids = fields.Many2many(
        "article.publication",
        "article_publication_non_scopus_filter_rel",
        string="Articles For Scopus", readonly=True,
        compute="_compute_non_scopus_publications"
    )

    @api.depends("article_publication_ids","conformity_publication_filter_ids")
    def _compute_conformity_publications(self):
        for record in self:
            conformity_articles = record.article_publication_ids.filtered(lambda a: a.state in ['proposal_minor_revisions','final_minor_revisions'])
            record.conformity_publication_filter_ids = conformity_articles

    @api.depends("article_publication_ids","publication_non_scopus_filter_ids")
    def _compute_non_scopus_publications(self):
        for record in self:
            non_scopus_articles = record.article_publication_ids.filtered(lambda a: ((a.state in ['accepted']) 
                                                                                     and a.publishing_state in ['not_published']))
            record.publication_non_scopus_filter_ids = non_scopus_articles

    def act_open_faculty_list(self):
        group = self.env.ref('thesis_design_database_manager.group_article_faculty_adviser')
        faculty_advisers = self.env['res.users'].search([('groups_id', 'in', group.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Adviser List',
            'view_mode': 'tree,form',
            'res_model': 'res.users',
            'domain': [('id', 'in', faculty_advisers.ids)],
            'views': [(self.env.ref('thesis_design_database_manager.article_faculty_adviser_tree_view').id, 'tree'),
                      (self.env.ref('thesis_design_database_manager.article_faculty_adviser_form_view').id, 'form')],  # Replace with your view ID
        }
    
    def act_shutdown_rpi(self):
        is_not_instructor = ((self.env.user.has_group('thesis_design_database_manager.group_article_thesis_instructor')) or 
            (self.env.user.has_group('thesis_design_database_manager.group_article_design_instructor')))
        
        if is_not_instructor:
            raise UserError("Instructors Only")

        import subprocess
        # Check if the device is a Raspberry Pi
        def is_raspberry_pi():
            try:
                with open('/sys/firmware/devicetree/base/model', 'r') as model_file:
                    model = model_file.read().strip()
                    if 'Raspberry Pi' in model:
                        return True
            except FileNotFoundError:
                return False
            return False

        if not is_raspberry_pi():
            raise UserError("This only works on RPI Systems")

        # rpi_password = 'article_database_password_C8i3ZS'.encode()  # Encode the password to bytes
        try:
            # Execute the shutdown command and capture the output
            result = subprocess.run(
                ['sudo', '-S', 'shutdown', '-h', 'now'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Read the output and error
            output = result.stdout.decode('utf-8')
            error = result.stderr.decode('utf-8')

            # Check for errors
            if result.returncode != 0:
                raise UserError(f"Error Shutting Down: {error}")
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Shutdown Initiated',
                        'message': f'The shutdown command has been successfully executed by. {self.name}',
                        'type': 'success',
                        'sticky': False,
                    }
                }
        
        except Exception as e:
            raise UserError(f"An unexpected error occurred: {str(e)}")