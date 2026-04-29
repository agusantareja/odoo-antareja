from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class ProposalManagement(models.Model):
    _name = 'proposal.management'
    _inherit = [_name,'approval.transaction.task.able.mixin']

    # data yang di perlukan oleh approval.tsk dan mobile.approval.task
    def get_internal_number(self):
        return self.name

    def get_internal_document(self):
        return self._description

    def get_internal_description(self):
        return self.perihal

    def get_internal_requester_id(self):
        return self.user_id.id

    # untuk build internal url
    def get_internal_menu_id(self):
        return 'proposal_management.main_proposal_management'

    def get_internal_action_id(self):
        return 'proposal_management.proposal_to_approve_action'

    def get_next_approval_task_line(self,**kwargs):
        return self.approval_ids.get_next_approval_task_line()

    def register_approval_task(self,**kwargs):
        rec = self.ensure_one()
        kw = dict(kwargs)
        if 'transaction_object' not in kw:
            kw['transaction_object'] = rec

        if rec.state=='cost_control':
            kw['user_ids'] = None
            kw['group_ids'] = self.env.ref('cni_inventory_intra.cost_control_group')
        elif rec.state=='waiting_approve':
            approval_task_line = rec.get_next_approval_task_line()
            return approval_task_line and approval_task_line.register_approval_task(**kw)
        else:
            return None

        #return super(ProposalManagement,self).register_approval_task(**kw)

    def action_approve_request(self):
        result = super(ProposalManagement,self).action_approve_request()
        for rec in self:
            if rec.state in ['cost_control','waiting_approval']:
                # setelah approval bila masih dalam kodisi approval update register approval
                rec.register_approval_task()
        return result

    def write(self, vals):
        # handling bila keluar approval
        in_waiting_approval = []
        if 'state' in vals:
            in_waiting_approval = [res.id for res in self if res.state in ['cost_control','waiting_approval']]
        result = super(ProposalManagement,self).write(vals)
        for rec in self:
            if rec.id in in_waiting_approval and rec.state not in ['cost_control','waiting_approval']:
                rec.unregister_approval_task(skip_create_approval_log=True)
        return result


# class ProposalManagement(models.Model):
#     _name = 'proposal.management'
#     _description = 'Proposal Management'
#     _inherit = ['mail.thread']

    # name = fields.Char(string='Name', readonly=True)
    # nama_proposal = fields.Char(string='Nama Proposal', required=True, )
    # date = fields.Date(string='Tanggal Request', default=fields.Date.today())
    # perihal = fields.Char(string='Perihal')
    # department_id = fields.Many2one('hr.department', default=lambda self: self.env.user.department_id.id,
    #                                 string='Department')
    # department = fields.Char(string='Department', related='department_id.name')
    # state = fields.Selection(string="State", selection=PM_STATES, readonly=True, default=PM_STATES[0][0],
    #                          track_visibility='onchange', )
    # note_approve = fields.Text(string='Note Approve', readonly=True)
    # note_reject = fields.Text(string='Note Reject', readonly=True)
    # note_revision = fields.Text(string='Note Revision', readonly=True)
    # from_user_disposisi = fields.Many2one('res.users', string='From User Disposisi')
    # to_user_disposisi = fields.Many2one('res.users', string='To User Disposisi')
    # file = fields.Binary(string='File', required=True, attachment=True)
    # file_name = fields.Char("File Name")
    # file_approve = fields.Binary(string='File Approve', required=False, attachment=True)
    # file_approve_name = fields.Char("File Approve Name")
    # approve_pdf_link = fields.Char('PDF Link', compute="_compute_link")
    # qr_code_pdf = fields.Binary("QR Code PDF", attachment=True, store=True)
    # qr_code = fields.Binary("QR Code", attachment=True, store=True)
    # pdf_preview = fields.Binary("PDF Preview", attachment=True, compute='_compute_pdf_preview')
    # approve_ids = fields.One2many('proposal_management.approve', 'proposal_management_id', string='Disposisi Approve',
    #                               readonly=False)
    # user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id)
    # creator = fields.Char(string='Creator', related='user_id.name')
    # user_cost_control_id = fields.Many2one('res.users', string='Cost Control')
    # revision = fields.Boolean(string='Revision')
    # acces_button = fields.Boolean(string='Acces Button', compute='get_acces_button')
    # acces_button_hold = fields.Boolean(string='Acces Button Hold', compute='get_acces_button_hold')
    # acces_button_cost_control = fields.Boolean(string='Acces Button Cost Control',
    #                                            compute='get_acces_button_cost_control')
    # current_users_approve = fields.Many2one('res.users', string='Current User Approve', compute='get_current_user')
    # current_job_approve = fields.Many2one('hr.job', string='Current Job Approve', compute='get_current_job')
    # waiting_time = fields.Char(string='Waiting Time', compute='get_waiting_time')
    # company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.company.id)
    # company_currency_id = fields.Many2one(related='company_id.currency_id', string='Company Currency', readonly=True,
    #                                       store=True)
    # nilai = fields.Monetary('Nilai', tracking=True, currency_field='company_currency_id')
    # alert_waiting_approval = fields.Text(string="Alert waiting approval", compute="compute_approver_name")
    # to_approve_filter = fields.Boolean(compute=True, search="search_to_approve_filter")
    # approve_cost_control = fields.Boolean(compute=True, search="search_approve_cost_control")
    # company_code = fields.Char(string='Company Code', related='company_id.code')
    # x_css = fields.Html(
    #     string='CSS',
    #     sanitize=False,
    #     compute='_compute_css',
    #     store=False,
    # )
    # url = fields.Text(string='Url')
    #
    # @api.depends('state')
    # def _compute_css(self):
    #     for rec in self:
    #         rec.x_css = ''
    #         if rec.state != 'draft':
    #             rec.x_css = """
    #             <style>
    #             .o_form_button_edit {display: none !important}
    #             .o_cp_action_menus{display: none !important}
    #             </style>"""
    #
    # @api.model
    # def create(self, vals):
    #     find_name = True
    #     while find_name:
    #         vals['name'] = self.env['ir.sequence'].next_by_code('proposal.management') or _('New')
    #         find_name = self.search([('name', '=', vals['name'])], limit=1)
    #     res = super(ProposalManagement, self).create(vals)
    #     # res.sudo().get_approve_ids()
    #     res.sudo().generate_file_qrcode()
    #     url = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
    #         self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
    #         res.id,
    #         res._name,
    #         res.company_id.id,
    #         self.env.ref('proposal_management.main_proposal_management').id
    #     )
    #     res.url = url
    #     return res

    # @api.model
    # def search_to_approve_filter(self, operator, operand):
    #     ids1 = []
    #     ids2 = []
    #     for proposal in self.search([('state', '=', 'cost_control')]):
    #         if self.user_has_groups('cni_inventory_intra.cost_control_group'):
    #             ids1.append(proposal.id)
    #     # for proposal in self.sudo().search([]):
    #     #     ids1.append(proposal.id)
    #     approval_ids = self.env['proposal_management.approve'].sudo().search([('state', '=', 'waiting_approve')],
    #                                                                          order='seq asc')
    #     for line in approval_ids:
    #         if line.validating_users.id == self.env.user.id:
    #             if line.proposal_management_id:
    #                 ids2.append(line.proposal_management_id.id)
    #
    #     # print("="*50+"TO APPROVE"+"="*50)
    #     # print(ids1)
    #     # print(ids2)
    #     ids = ids1 + ids2
    #     return [('id', 'in', ids)]
    #
    # @api.model
    # def search_approve_cost_control(self, operator, operand):
    #     proposal = self.sudo().search(
    #         [('state', 'in', ['waiting_approve', 'approve']), ('user_cost_control_id', '=', self.env.user.id)])
    #     return [('id', 'in', proposal.ids)]
    #
    # def _compute_link(self):
    #     for rec in self:
    #         rec.approve_pdf_link = "%s/web/content/proposal.management/%s/file_approve" % (
    #         http.request.env['ir.config_parameter'].sudo().get_param('web.base.url'), rec.id)
    #
    # def _compute_pdf_preview(self):
    #     for rec in self:
    #         if rec.state == 'approve':
    #             rec.pdf_preview = rec.file_approve
    #         else:
    #             rec.pdf_preview = rec.file
    #
    # def get_file_approve(self):
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'name': 'contract',
    #         'url': '/web/content/proposal.management/%s/file_approve/%s?download=true' % (self.id, self.file_name),
    #     }
    #
    # @api.depends('approve_ids')
    # def get_waiting_time(self):
    #     self.waiting_time = False
    #     for rec in self:
    #         for line in rec.approve_ids:
    #             # if line.validation_status == False:
    #             if line.state == 'waiting_approve':
    #                 start_date = line.date
    #                 end_date = datetime.now().date()
    #                 date_difference = (start_date - end_date).days
    #                 date = abs(date_difference)
    #                 rec.waiting_time = date
    #
    # @api.depends('approve_ids')
    # def get_current_job(self):
    #     self.current_job_approve = False
    #     for rec in self:
    #         for line in rec.approve_ids:
    #             # if line.validation_status == False:
    #             if line.state == 'waiting_approve':
    #                 employee_obj = self.env['hr.employee'].sudo().search([('user_id', '=', line.validating_users.id)],
    #                                                                      limit=1)
    #                 rec.current_job_approve = employee_obj.job_id.id
    #
    # @api.depends('approve_ids')
    # def get_current_user(self):
    #     self.current_users_approve = False
    #     for rec in self:
    #         for line in rec.approve_ids:
    #             # if line.validation_status == False:
    #             if line.state == 'waiting_approve':
    #                 employee_obj = self.env['hr.employee'].sudo().search([('user_id', '=', line.validating_users.id)],
    #                                                                      limit=1)
    #                 rec.current_users_approve = employee_obj.user_id.id
    #                 # rec.current_users_approve  = line.validating_users.id
    #
    # @api.constrains('file')
    # def _check_file(self):
    #     if str(self.file_name.split(".")[1]) != 'pdf':
    #         raise Warning("Cannot upload file different from .pdf file")
    #
    def action_approve_cost_control(self):
        # for rec in self:
        #     rec.write({
        #         'state': 'waiting_approve',
        #         'user_cost_control_id': self.env.user.id,
        #     })
        result = super(ProposalManagement, self).action_approve_cost_control()
        for rec in self:
            if rec.state=='waiting_approval':
                self.env['approval.audit.log'].create_audit_log(
                    transaction_id=rec.id,
                    transaction_model_name=self._name,
                    user_id=rec.approver_cost_control.id,
                    name='Approval Cost Control',
                    action_type='approve',
                    create_date=fields.Datetime.now(),
                )
                rec.register_approval_task()

        return result

    def button_submit(self):
        # handling saat masuk approval
        result =super(ProposalManagement,self).button_submit()
        for rec in self:
            rec.register_approval_task()
        return result

    # def button_submit(self):
    #     for rec in self:
    #         if rec.nilai == 0.0:
    #             raise Warning("Maaf Nilai tidak boleh 0")
    #         rec.get_approve_ids()
    #         rec.write({'state': 'cost_control'})
    #
    #         # mail bot
    #         # obj = self.env['proposal_management.approve'].search([('proposal_management_id', '=', rec.id),('validation_status', '=', False)], limit=1)
    #         obj = self.env['proposal_management.approve'].search(
    #             [('proposal_management_id', '=', rec.id), ('state', '=', 'waiting_approve')], limit=1)
    #         for user in obj.validating_users:
    #             link = '%s/web#id=%s&model=proposal.management&view_type=form&cids=%s&menu_id=%s' % (
    #                 self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
    #                 rec.id,
    #                 self.company_id.id,
    #                 self.env.ref('proposal_management.main_proposal_management').id
    #             )
    #             params_message = self.env["ir.config_parameter"].sudo().get_param(
    #                 "mail_bot_approve.bot_message_approve")
    #             message_approve = params_message.replace("{user}", user.partner_id.name).replace("{transaction_name}",
    #                                                                                              rec._description + " " + rec.name)
    #             message = _("%s<br/><a href='%s'>%s</a>") % (message_approve, link, rec.name)
    #             self.env['mail.channel'].mail_bot_approve(user.partner_id, message)
    #             self.send_message_email_wa(user)
    #
    # def get_approve_ids(self):
    #     for rec in self:
    #         seq = 0
    #
    #         approve_list = []
    #         # # APPROVAL ATASAN HINGGA DI BAWAH PRESIDENT DIRECTOR
    #         employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)])
    #         while employee_id.parent_id:
    #             parent_id = employee_id.parent_id
    #             job_config = self.env['proposal.matrix.approval'].sudo().search([('job_id', '=', parent_id.job_id.id)],
    #                                                                             limit=1)
    #             if not parent_id.job_id.name == 'PRESIDENT DIRECTOR' and not job_config:
    #                 approve_list.append((0, 0, {
    #                     'seq': seq,
    #                     'validating_users': parent_id.user_id.id,
    #                     'job_id': parent_id.job_id.id,
    #                     'date': rec.date,
    #                 }))
    #                 seq += 1
    #                 employee_id = parent_id
    #             else:
    #                 break
    #
    #         # APPROVAL Matrix
    #         limit_bottom = 0
    #         matrix = self.env['proposal.matrix.approval'].sudo().search([], order='sequence asc')
    #         limits = matrix.mapped('limit')
    #         # limits.sort()
    #         for val in limits:
    #             if val >= rec.nilai:
    #                 limit_bottom = val
    #                 break
    #             else:
    #                 limit_bottom = val
    #
    #         for data in matrix:
    #             employee_id = self.env['hr.employee'].sudo().search([('job_id', '=', data.job_id.id)], limit=1)
    #             print(employee_id.job_id.name)
    #             if data.limit <= limit_bottom:
    #                 approve_list.append((0, 0, {
    #                     'seq': seq,
    #                     'validating_users': employee_id.user_id.id,
    #                     'job_id': employee_id.job_id.id,
    #                     'date': rec.date,
    #                 }))
    #                 seq += 1
    #
    #         # print(approve_list)
    #         rec.approve_ids = approve_list
    #
    # def action_hold(self):
    #     for rec in self:
    #         for line in rec.approve_ids.filtered(lambda l: l.validating_users.id == self.env.user.id):
    #             line.write({
    #                 # 'validation_status' : True,
    #                 'state': 'hold',
    #                 'date': datetime.now().date(),
    #             })
    #
    # def open_approve(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Approve',
    #         'res_model': 'proposal_management.wizard',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_view_type': 'approve',
    #         }
    #     }
    #
    # def open_reject(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Reject',
    #         'res_model': 'proposal_management.wizard',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_view_type': 'reject',
    #         }
    #     }
    #
    # def open_disposisi(self):
    #     job = self.env['proposal_management.approve'].search(
    #         [('proposal_management_id', '=', self.id), ('validating_users', '=', self.env.uid)]).job_id
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Disposisi',
    #         'res_model': 'proposal_management_disposisi.wizard',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'default_job_id': job.id,
    #         }
    #     }
    #
    # @api.depends('approve_ids')
    # def get_acces_button(self):
    #     for rec in self:
    #         rec.acces_button = False
    #         approval_ids = self.env['proposal_management.approve'].sudo().search(
    #             [('proposal_management_id', '=', rec.id), ('state', '=', 'waiting_approve')], order='seq asc, id asc',
    #             limit=1)
    #         for line in approval_ids.filtered(lambda l: l.validating_users.id == self.env.user.id):
    #             # if line.validation_status == False:
    #             if line.state in ['waiting_approve', 'hold']:
    #                 rec.acces_button = True
    #             else:
    #                 rec.acces_button = False
    #
    # @api.depends('approve_ids')
    # def get_acces_button_hold(self):
    #     for rec in self:
    #         rec.acces_button_hold = False
    #         approval_ids = self.env['proposal_management.approve'].sudo().search(
    #             [('proposal_management_id', '=', rec.id), ('state', '=', 'waiting_approve')], order='seq asc, id asc',
    #             limit=1)
    #         for line in approval_ids.filtered(lambda l: l.validating_users.id == self.env.user.id):
    #             # if line.validation_status == False:
    #             if line.state == 'waiting_approve':
    #                 rec.acces_button_hold = True
    #             else:
    #                 rec.acces_button_hold = False
    #
    # @api.depends('user_id')
    # def get_acces_button_cost_control(self):
    #     for rec in self:
    #         rec.acces_button_cost_control = False
    #         if self.user_has_groups('cni_inventory_intra.cost_control_group'):
    #             rec.acces_button_cost_control = True

    # def _get_approval_requests(self):
    #     current_uid = self.env.uid
    #     proposal_management = self.env['proposal.management'].sudo().search([('state','in',['cost_control','disposisi','waiting_approve','approve'])])
    #     data = []
    #     for pm in proposal_management:
    #         cost_control_group_id = self.env.ref('cni_inventory_intra.cost_control_group').id
    #         group_obj = self.env['res.groups'].browse(cost_control_group_id)
    #         for user in group_obj.users:
    #             if user.id == self.env.user.id:
    #                 data.append(pm.id)
    #         for user in pm.approve_ids:
    #             # if user.validating_users.id == current_uid and user.validation_status == False:
    #             if user.validating_users.id == current_uid and user.state == 'waiting_approve':
    #                 data.append(pm.id)
    #     value = {
    #         'domain'    : str([('id', 'in', data)]),
    #         'view_mode' : 'tree,form,kanban',
    #         'res_model' : 'proposal.management',
    #         'view_id'   : False,
    #         'type'      : 'ir.actions.act_window',
    #         'name'      : _('To Approve'),
    #         'res_id'    : self.id,
    #         'target'    : 'current',
    #         'context': {
    #             'create': 0,
    #             'delete': 0
    #         }
    #     }
    #     return value

    # def compute_approver_name(self):
    #     for rec in self:
    #         approver = self.env['proposal_management.approve'].search(
    #             [('proposal_management_id', '=', rec.id), ('state', '=', 'waiting_approve')], limit=1, order='seq asc')
    #         approver_name = approver.validating_users.name if approver else ""
    #
    #         alert = "Menunggu Persetujuan Oleh %s " % (str(approver_name))
    #         if approver.note:
    #             alert += f"({approver.note})"
    #         rec.alert_waiting_approval = alert
    #
    # def generate_qrcode(self):
    #     base_url = self.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')]).value
    #     url = '%s/proposal/%s' % (base_url, self.id)
    #
    #     qr = qrcode.QRCode()
    #     qr.add_data(url)
    #     qr.make(fit=True)
    #
    #     img = qr.make_image()
    #     buffered = BytesIO()
    #     img.save(buffered)
    #     img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    #     return img_str
    #
    # def generate_file_qrcode(self):
    #     base_url = self.env['ir.config_parameter'].sudo().search([('key', '=', 'web.base.url')]).value
    #     url = '%s/proposal/%s' % (base_url, self.id)
    #
    #     qr = qrcode.QRCode(
    #         version=1,
    #         error_correction=qrcode.constants.ERROR_CORRECT_L,
    #         box_size=10,
    #         border=4,
    #     )
    #     qr.add_data(url)
    #     qr.make(fit=True)
    #     img = qr.make_image()
    #     temp = BytesIO()
    #     img.save(temp, format="PNG")
    #     qr_image = base64.b64encode(temp.getvalue())
    #     self.qr_code = qr_image
    #
    #     # qrcode_pdf, _ = self.env.ref('proposal_management.action_report_proposal_qr_code').sudo()._render_qweb_pdf([int(self.id)])
    #     pdf = self.env.ref('proposal_management.action_report_proposal_qr_code').render_qweb_pdf(self.ids)
    #     self.qr_code_pdf = base64.b64encode(pdf[0])
    #
    # def qrcode_to_binary(self):
    #     import tempfile
    #     # import fitz
    #     from pdfrw import PdfReader, PdfWriter, PageMerge
    #     from PyPDF2 import PdfFileMerger
    #
    #     for rec in self:
    #
    #         rec.generate_file_qrcode()
    #
    #         # membuat temporari file
    #         path_infile = tempfile.gettempdir() + '/infile%s.pdf' % rec.id
    #         path_qrcode = tempfile.gettempdir() + '/qrcode%s.png' % rec.id
    #         path_approval = tempfile.gettempdir() + '/approval%s.pdf' % rec.id
    #         path_outfile = tempfile.gettempdir() + '/outfile%s.pdf' % rec.id
    #
    #         # membuka temporari file
    #         a = open(path_infile, 'wb')
    #         # memasukkan binary ke temporary file
    #         a.write(base64.b64decode(rec.file))
    #         a.close()
    #
    #         # membuka temporari file
    #         b = open(path_qrcode, 'wb')
    #         # memasukkan binary ke temporary file
    #         qrcode_pdf = rec.env.ref('proposal_management.action_report_proposal_qr_code').render_qweb_pdf(rec.ids)
    #         qrcode_pdf = base64.b64encode(qrcode_pdf[0])
    #         b.write(base64.b64decode(qrcode_pdf))
    #         b.close()
    #
    #         # membuka temporari file
    #         c = open(path_approval, 'wb')
    #         # memasukkan binary ke temporary file
    #         approval_pdf = rec.env.ref('proposal_management.action_report_approval').render_qweb_pdf(rec.ids)
    #         approval_pdf = base64.b64encode(approval_pdf[0])
    #         c.write(base64.b64decode(approval_pdf))
    #         c.close()
    #
    #         # define the reader and writer objects
    #         reader_input = PdfReader(path_infile)
    #         writer_output = PdfWriter()
    #         watermark_input = PdfReader(path_qrcode)
    #         watermark = watermark_input.pages[0]
    #
    #         # go through the pages one after the next
    #         for current_page in range(len(reader_input.pages)):
    #             merger = PageMerge(reader_input.pages[current_page])
    #             merger.add(watermark).render()
    #
    #         # write the modified content to disk
    #         writer_output.write(path_outfile, reader_input)
    #
    #         d = PdfFileMerger()
    #         d.append(path_outfile, import_bookmarks=False)
    #         d.append(path_approval, import_bookmarks=False)
    #         final_file = tempfile.gettempdir() + '/final%s.pdf' % rec.id
    #         d.write(final_file)
    #         d.close()
    #
    #         e = open(final_file, 'rb')
    #         rec.file_approve = base64.b64encode(e.read())

    # def send_message_email_wa(self, user):
    #     for rec in self:
    #         template_mail = self.env.ref('proposal_management.proposal_approver_mail_template')
    #         param_message = self.env["ir.config_parameter"].sudo().get_param(
    #             "proposal_management.message_wa_proposal_approver")
    #
    #         message_wa = param_message.replace("{approver}", user.partner_id.name).replace("{kode}", rec.name).replace(
    #             "{requester}",
    #             rec.user_id.name).replace("{department}", rec.department_id.name).replace("{url}",
    #                                                                                       rec.url if rec.url else "")
    #
    #         send = self.env['send_message.email'].sudo().create({
    #             'receiver': user.id,
    #             'template': template_mail.id,
    #             'message': message_wa,
    #             'company_id': rec.company_id.id,
    #             'id_record': rec.id,
    #             'ref': rec.name
    #         })
