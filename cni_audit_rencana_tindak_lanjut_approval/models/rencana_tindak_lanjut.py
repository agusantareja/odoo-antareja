
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from lxml import etree
from pytz import timezone
import logging
import re
import time
from odoo.tools.float_utils import float_round as round
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError
_logger = logging.getLogger(__name__)

class RencanaTindakLanjut(models.Model):
    _name = 'rencana.tindak.lanjut'
    _inherit = [_name, 'approval.transaction.task.able.mixin']

    def get_internal_number(self):
        return self.name

    def get_internal_document(self):
        return self._description

    def get_internal_description(self):
        return self.bukti

    # untuk build internal url
    def get_internal_menu_id(self):
        return 'cni_audit.cni_request_attendance_correction_menuitem'

    def get_internal_action_id(self):
        return 'cni_audit.rencana_tindak_lanjut_to_approve_action'

    def get_internal_requester_id(self):
        return self.employee_id.user_id.id or int(self.create_uid)

    def get_next_approval_task_line(self,**kwargs):
        return self.approval_ids.get_next_approval_task_line()

    def register_approval_task(self,**kwargs):
        rec = self.ensure_one()
        kw = dict(kwargs)
        if 'transaction_object' not in kw:
            kw['transaction_object'] = rec
        if rec.state=='open':
            if rec.user_manager_id:
                kw['user_ids'] = rec.user_manager_id
            else:
                return None
        elif rec.state=='progress':
            if rec.user_auditor_id:
                kw['user_ids'] = rec.user_auditor_id
            else:
                return None
        elif rec.state=='waiting':
            approval_task_line = rec.get_next_approval_task_line()
            return approval_task_line and approval_task_line.register_approval_task(**kw)
        else:
            return None

        return super(RencanaTindakLanjut,self).register_approval_task(**kw)

    def unregister_approval_task(self,skip_create_approval_log=True,**kwargs):
        return super(RencanaTindakLanjut,self).unregister_approval_task(skip_create_approval_log=skip_create_approval_log,**kwargs)
    #_order = 'id desc'

    # @api.model
    # def _get_default_date(self):
    #     return date.today()
    #
    # def default_employee(self):
    #     """untuk otomatis employee saat mengajukan"""
    #     employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], order='id asc', limit=1)
    #     return employee.id
    #
    # def get_active_user_manager(self):
    #     active_user = False
    #     for rec in self:
    #         # if rec.user_manager_id.id == self.env.uid:
    #         #     if rec.state == 'open':
    #         #         active_user = True
    #         for manager in rec.manager_auditee_ids:
    #             if manager.user_id.id == self.env.uid and rec.state == 'open':
    #                 active_user = True
    #
    #         if rec.user_manager_id and rec.user_manager_id.id == self.env.uid and rec.state == 'open':
    #             active_user = True
    #
    #         rec.check_active_user_manager = active_user
    #
    # def get_active_user_auditor(self):
    #     active_user = False
    #     for rec in self:
    #         if rec.user_auditor_id.id == self.env.uid:
    #             if rec.state == 'progress':
    #                 active_user = True
    #
    #         rec.check_active_user_auditor = active_user
    #
    #
    # category_audit = fields.Selection([
    #     ('internal','Internal'),
    #     ('external','External'),
    #     ('reguler','Reguler'),
    #     ],string="Kategori Audit",related='plor_id.category_audit')
    #
    # kategori_temuan_nonreguler = fields.Selection([
    #     ('kritikal','Kritikal'),
    #     ('mayor','Mayor'),
    #     ('minor','Minor'),
    #     ],string="Kategori Temuan Internal & External",related='plor_id.kategori_temuan_nonreguler')
    #
    # kategori_temuan_reguler = fields.Selection([
    #     ('very_low','Very Low Risk'),
    #     ('low_risk',' Low Risk'),
    #     ('medium_risk','Medium Risk'),
    #     ('high_risk','High Risk'),
    #     ('very_high','Very High Risk')
    #     ],string="Kategori Temuan Reguler",related='plor_id.kategori_temuan_reguler')
    #
    # uraian_masalah = fields.Text('Uraian Masalah',related='plor_id.uraian_masalah')
    # bukti = fields.Text('Bukti',related='plor_id.bukti')
    #
    # reference_smkp_id = fields.Many2one('element.smkp',related='plor_id.reference_smkp_id')
    # sub_element_smkp_id = fields.Many2one('sub.element.smkp',related='plor_id.sub_element_smkp_id')
    # sub_subelement_smkp_id = fields.Many2one('sub.sub.element.smkp',related='plor_id.sub_subelement_smkp_id')
    #
    # reference_smkp_number = fields.Char('SMKP Number')
    # sub_element_smkp_number = fields.Char('Element SMKP Number')
    # sub_subelement_smkp_number = fields.Char('Sub Element SMKP Number')
    #
    # reference_iso_id = fields.Many2one('klausul.iso',related='plor_id.reference_iso_id')
    # element_iso_id = fields.Many2one('element.iso', related='plor_id.element_iso_id')
    # sub_element_iso_id = fields.Many2one('sub.element.iso', related='plor_id.sub_element_iso_id')
    # sub_subelement_iso_id = fields.Many2one('sub.subelement.iso', related='plor_id.sub_subelement_iso_id')
    #
    # element_iso_number = fields.Char('Element ISO')
    # sub_element_iso_number = fields.Char('Sub Element ISO')
    # sub_subelement_iso_number = fields.Char('Sub Subelement ISO')
    #
    # other_reference = fields.Text('Referensi Lainnya',related='plor_id.other_reference')
    # iso_ids = fields.Many2many('klausul.iso', related='plor_id.iso_ids')
    #
    # deskripsi_temuan = fields.Text('Deskripsi Temuan', related='plor_id.deskripsi_temuan')
    # date_limit_fixed = fields.Date('Batas Waktu Perbaikan', related='plor_id.date_limit_fixed')
    # auditee_id = fields.Many2one('hr.employee', related='plor_id.auditee_id')
    # manager_auditee_id = fields.Many2one('hr.employee', related='plor_id.manager_auditee_id')
    # auditor_id = fields.Many2one('hr.employee', related='plor_id.employee_id')
    #
    # name = fields.Char('Number')
    # name_company_id = fields.Many2one('audit.company',related='plor_id.name_company_id')
    # department_id = fields.Many2one('audit.department', related='plor_id.department_id')
    # crated_date = fields.Date('Created Date',default=_get_default_date)
    # employee_id = fields.Many2one('hr.employee',string="Request by", default=default_employee)
    #
    # akar_masalah = fields.Text('Akar Permasalahan')
    # korektif = fields.Text('Tindakan Korektif')
    # preventif = fields.Text('Tindakan Preventif')
    #
    # plor_id = fields.Many2one('audit.plor',string="Ketidaksesuaian")
    # date_auditee_approve = fields.Date('Tanggal Auditee Approve')
    # date_auditor_approve = fields.Date('Tanggal Auditor Approve')
    #
    # state = fields.Selection([
    #     ('draft','Draft'),
    #     ('open','Open'),
    #     ('progress','In Progress'),
    #     ('waiting', 'Waiting Approve LA'),
    #     ('rejected','Rejected'),
    #     ('close','Closed'),
    #     ('reject_by_manager', 'Reject by Manager'),
    #     ('reject_by_auditor', 'Reject by Auditor'),
    #     ],string="Status", default='draft',tracking=True)
    # is_interruptions = fields.Boolean(string="Intruptions", default=False)
    # filter_tindak_lanjut = fields.Boolean(compute=True, search='search_filter_tindak_lanjut')
    # filter_tindak_lanjut_to_approve = fields.Boolean(compute=True, search='search_filter_tindak_lanjut_to_approve')
    # filter_tindak_lanjut_audit = fields.Boolean(compute=True, search='search_filter_tindak_lanjut_audit')
    # filter_tindak_lanjut_to_approve_audit = fields.Boolean(compute=True, search='search_filter_tindak_lanjut_to_approve_audit')
    # manager_approve_date = fields.Date('Manager Approve')
    # manager_has_approve = fields.Boolean(string="Manager Has Approve")
    # user_manager_id = fields.Many2one('res.users', related='manager_auditee_id.user_id')
    # user_auditor_id = fields.Many2one('res.users', related='auditor_id.user_id')
    # check_active_user_manager = fields.Boolean(compute=get_active_user_manager, store=False)
    # check_active_user_auditor = fields.Boolean(compute=get_active_user_auditor, store=False)
    # document_ids = fields.One2many('attachment.document.tindak.lanjut', 'document_tindak_lanjut_id')
    # url = fields.Text(sting='URL')
    # email_auditor_ids = fields.Many2many('list.auditor', related='plor_id.email_auditor_ids')
    # access_auditee = fields.Boolean(compute='_compute_access_auditee', string='Access Audetee')
    # year = fields.Char(string='Year')
    # approval_ids = fields.One2many('rencana.tindak.lanjut.approval', 'tindak_lanjut_id', string='Approval')
    # filter_approval = fields.Boolean(compute=True, search='search_filter_approval')
    # access_approval = fields.Boolean(compute='compute_access_approval', string='Access Approval')
    # reg_no = fields.Char(string='Reg No', related='plor_id.reg_no')
    # auditee_ids = fields.Many2many('hr.employee', 'rencana_tindak_lanjut_auditee_rel',related='plor_id.auditee_ids')
    # manager_auditee_ids = fields.Many2many('hr.employee', 'rencana_tindak_lanjut_manager_auditee_rel', related='plor_id.manager_auditee_ids')
    # type = fields.Selection(related='plor_id.type')
    # project_audit_id = fields.Many2one('audit.project', string='Nama Project Audit')
    # start_date = fields.Date(string='Start Date')
    # finish_date = fields.Date(string='Finish Date')
    # deskripsi_masalah = fields.Text(string='Deskripsi Masalah')
    # peringkat_risiko = fields.Selection(selection=
    #                 [('tinggi','Tinggi'),
    #                 ('menengah', 'Menengah'),
    #                 ('rendah', 'Rendah')
    #                 ], string='Peringkat Risiko')
    # batas_waktu = fields.Date(string='Batas Waktu')
    # rekomendasi_ids = fields.One2many('rekomendasi.audit', 'tindak_lanjut_id', string='Rekomendasi')
    # response_management_ids = fields.One2many('response.management', 'tindak_lanjut_id', string='Tanggapan Manajemen', ondelete='cascade')
    # no_engagement_letter = fields.Char(string='No Engagement Letter Audit')
    # access_edit_button = fields.Html(string='Access Edit Button', sanitize=False, compute='_compute_access_edit_button')
    # kategori_audit = fields.Selection(related='plor_id.kategori_audit', string='Kategori Audit')
    # filter_tindak_lanjut_internal_audit = fields.Boolean(compute=True, search='search_filter_tindak_lanjut_internal_audit')
    # filter_tindak_lanjut_to_approve_internal_audit = fields.Boolean(compute=True, search='search_filter_tindak_lanjut_to_approve_internal_audit')
    # active = fields.Boolean('Active', default=True)
    # view_id = fields.Many2one('ir.iu.view', string='View ID')
    #
    #

    # def button_submit(self):
    #     condition = 'manager'
    #     if self.type in ['qms', False]:
    #         self.send_notification_request(condition)
    #         if not self.akar_masalah or self.korektif == False:
    #             raise ValidationError(_("Anda Belum mengisi Tindakan Korektif/Preventif" ))
    #
    #     if self.type == 'audit' and self.response_management_ids:
    #         self.send_notification_internal_audit(condition)
    #         if self.response_management_ids.filtered(lambda r: not r.response):
    #             raise ValidationError(_("Anda Belum mengisi Response" ))
    #         if self.response_management_ids.filtered(lambda r:  not r.attachment_ids):
    #             raise ValidationError(_("Anda Belum mengisi Attachment" ))
    #
    #
    #
    #     day_approve = fields.Datetime.now()
    #     self.plor_id.write({'tindak_lanjut_state':'open'})
    #     self.write({
    #         'state':'open',
    #         'date_auditee_approve':day_approve
    #         })
    #
    def button_approve(self):
        result = super(RencanaTindakLanjut, self).button_approve()
        for rec in self:
           rec.register_approval_task()

        return result
    # def button_approve(self):
    #     day_approve = fields.Datetime.now()
    #     condition = 'auditor'
    #     if self.type in ['qms', False]:
    #         self.send_notification_request(condition)
    #     elif self.type == 'audit':
    #         self.send_notification_internal_audit(condition)
    #     self.write({
    #         'manager_has_approve':True,
    #         'manager_approve_date':day_approve
    #         })
    #
    # def button_closed(self):
    #     day_approve = fields.Datetime.now()
    #     self.plor_id.write({'state':'close'})
    #     self.write({
    #         'state':'close',
    #         'date_auditor_approve':day_approve
    #         })
    #
    def button_approve_to_progress(self):
        result = super(RencanaTindakLanjut,self).button_approve_to_progress()
        for rec in self:
            rec.register_approval_task()

        return result

    # def button_approve_to_progress(self):
    #     condition = 'auditor'
    #     if self.type in ['qms', False]:
    #         self.send_notification_request(condition)
    #     elif self.type == 'audit':
    #         self.send_notification_internal_audit(condition)
    #     day_approve = fields.Datetime.now()
    #     self.plor_id.write({'state':'progress'})
    #     self.write({'state':'progress',
    #         'date_auditee_approve':day_approve
    #         })
    #
    # def button_reject_in_open(self):
    #     return{
    #         'type': 'ir.actions.act_window',
    #         'name': _('Comment Reject'),
    #         'res_model': 'audit.comment.reject',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'active_id': self.id,
    #             'default_tindak_lanjut_id':self.id,
    #             'default_state':self.state
    #         },
    #         'views': [[False, 'form']]
    #     }
    #
    #
    # def search_filter_tindak_lanjut(self, operator, operand):
    #     if self.user_has_groups('cni_audit.group_cni_auditor'):
    #         return []
    #     else:
    #         ids = self.search([('auditee_id.user_id', '=', self._uid)]).ids
    #         ids2 = self.search([('manager_auditee_id.user_id', '=', self._uid)]).ids
    #         return [('id', 'in', ids+ids2)]
    #
    # def search_filter_tindak_lanjut_audit(self, operator, operand):
    #     if self.user_has_groups('cni_audit.group_cni_auditor'):
    #         return []
    #     else:
    #         # ids = self.search([('auditee_id.user_id', '=', self._uid)]).ids
    #         # ids2 = self.search([('manager_auditee_id.user_id', '=', self._uid)]).ids
    #         ids = []
    #         for tindak_lanjut in self.search([('auditee_ids', '!=', False)]):
    #             if self._uid in tindak_lanjut.auditee_ids.mapped('user_id').ids:
    #                 ids.append(tindak_lanjut.id)
    #         for tindak_lanjut in self.search([('manager_auditee_ids', '!=', False)]):
    #             if self._uid in tindak_lanjut.manager_auditee_ids.mapped('user_id').ids:
    #                 ids.append(tindak_lanjut.id)
    #         ids = list(set(ids))
    #         return [('id', 'in', ids)]
    #
    #
    # def search_filter_tindak_lanjut_to_approve(self, operator, operand):
    #     data = []
    #     for rencanas in self.sudo().search([('state', '=', 'waiting'), ('type', 'in', ['qms', False])]):
    #         approval = self.env['rencana.tindak.lanjut.approval'].search([('state', '!=', 'approve'), ('tindak_lanjut_id', '=', rencanas.id)], order='sequence asc', limit=1)
    #         if approval and approval.employee_id.user_id.id == self._uid:
    #             data.append(rencanas.id)
    #     if self.user_has_groups('cni_audit.group_cni_auditor'):
    #         ids = self.search([('state', '=', 'progress'), ('type', 'in', ['qms', False])]).ids
    #         ids += data
    #         ids = list(set(ids))
    #         return [('id', 'in', ids)]
    #     else:
    #         ids = []
    #         tindak_lanjuts = self.search([('manager_auditee_ids', '!=', False),('state','=','open'),('manager_has_approve','=',False), ('type', 'in', ['qms', False])])
    #         for tindak_lanjut in tindak_lanjuts:
    #             if self._uid in tindak_lanjut.manager_auditee_ids.mapped('user_id').ids:
    #                 ids.append(tindak_lanjut.id)
    #         ids += data
    #         ids = list(set(ids))
    #         return [('id', 'in', ids)]
    #
    #
    # def search_filter_tindak_lanjut_to_approve_audit(self, operator, operand):
    #     ids = self.search([('manager_auditee_id.user_id', '=', self._uid),('state','=','open'),('manager_has_approve','=',False)]).ids
    #     ids_progress = self.search([('create_uid', '=', self._uid),('state','=','progress')]).ids
    #     ids += ids_progress
    #     if self.user_has_groups('cni_audit.group_cni_internal_leader_audit'):
    #         ids_leader = self.search([('state', '=', 'waiting')]).ids
    #         ids += ids_leader
    #     return [('id', 'in', ids)]
    #
    #
    # def button_perbaiki_kembali(self):
    #     self.write({
    #         'state':'draft'
    #         })
    #
    # def button_reject_in_progress(self):
    #     condition = 'reject'
    #     if self.type in ['qms', False]:
    #         self.send_notification_request(condition)
    #     elif self.type == 'audit':
    #         self.send_notification_internal_audit(condition)
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Comment Reject'),
    #         'res_model': 'audit.comment.reject',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'active_id': self.id,
    #             'default_tindak_lanjut_id': self.id,
    #             'default_state':self.state
    #         },
    #         'views': [[False, 'form']]
    #     }
    #
    #
    #
    # def send_notification_request(self, condition):
    #     for rec in self:
    #         email = self.env['send_message.email']
    #         list_email_cc = False
    #         template = self.env.ref('cni_audit.audit_manager_to_approve_mail_template')
    #         if condition == 'manager':
    #             param_wa = self.env.ref('cni_audit.message_wa_to_manager_auditee').value
    #             message_wa = param_wa.replace("{nomor}", rec.name).replace("{auditee}",
    #                         ','.join(rec.auditee_ids.mapped('name'))).replace("{link}", rec.url)
    #             template = self.env.ref('cni_audit.audit_manager_to_approve_mail_template')
    #             approvals = rec.manager_auditee_ids.mapped("user_id")
    #         elif condition == 'auditee':
    #             auditor_ids = rec.email_auditor_ids.mapped('name').mapped('name')
    #             audit_name = ', '.join(auditor_ids)
    #             param_wa = self.env.ref('cni_audit.message_wa_to_auditee').value
    #             message_wa = param_wa.replace("{nomor}", rec.name).replace("{auditor}",
    #                         audit_name).replace("{link}", rec.url)
    #             template = self.env.ref('cni_audit.audit_auditee_to_submit_mail_template')
    #             approvals = rec.auditee_ids.mapped('user_id')
    #         elif condition == 'auditor':
    #             param_wa = self.env.ref('cni_audit.message_wa_to_auditor').value
    #             message_wa = param_wa.replace("{nomor}", rec.name).replace("{auditee}",
    #                         ','.join(rec.auditee_ids.mapped('name'))).replace("{link}", rec.url)
    #             template = self.env.ref('cni_audit.audit_auditor_to_validate_mail_template')
    #             approvals = rec.auditor_id.user_id
    #         elif condition == 'reject':
    #             param_wa = self.env.ref('cni_audit.message_wa_reject_by_auditor_and_manager').value
    #             message_wa = param_wa.replace("{nomor}", rec.name).replace("{rejector}",
    #                         rec.write_uid.name).replace("{link}", rec.url)
    #             template = self.env.ref('cni_audit.audit_auditor_to_reject_mail_template')
    #             approvals = rec.auditee_ids.mapped('user_id')
    #         elif condition == 'closed':
    #             auditor_ids = rec.email_auditor_ids.mapped('name').mapped('name')
    #             audit_name = ', '.join(auditor_ids)
    #             param_wa = self.env.ref('cni_audit.message_wa_closed_audit').value
    #             message_wa = param_wa.replace("{nomor}", rec.name).replace("{auditor}",
    #                         audit_name).replace("{link}", rec.url)
    #             template = self.env.ref('cni_audit.audit_rencana_tindak_lanjut_closed_mail_template')
    #             auditee = [user for user in rec.auditee_ids.mapped('user_id')]
    #             manager_auditee = [user for user in rec.manager_auditee_ids.mapped('user_id')]
    #             approvals = list(set(auditee + manager_auditee))
    #         elif condition == 'reject_by_leader_auditor':
    #             param_wa = self.env.ref('cni_audit.message_wa_reject_by_leader_auditor').value
    #             message_wa = param_wa.replace("{nomor}", rec.name).replace("{leader_auditor}",
    #                         rec.write_uid.name).replace("{link}", rec.url)
    #             template = self.env.ref('cni_audit.reject_by_leader_auditor_mail_template')
    #             approvals = rec.auditee_ids.mapped('user_id')
    #
    #
    #         email_cc_auditor = ''
    #         for list_auditor in self.env['list.auditor'].search([('state','=','added'),('is_recieve_email','=',True)]):
    #             if list_auditor.email:
    #                 email_cc_auditor += str(list_auditor.email) + ','
    #                 email.create({
    #                     'receiver'  : list_auditor.name.user_id.id,
    #                     'template'  : template.id,
    #                     'company_id': rec.create_uid.company_id.id,
    #                     'id_record' : rec.id,
    #                     'ref'       : rec.name,
    #                     'is_send_wa': True
    #                     # 'email_cc'  : list_email_cc,
    #                 })
    #
    #         list_email_cc = email_cc_auditor
    #
    #         for user in approvals:
    #             message = message_wa.replace("{receiver}", user.name)
    #             email.create({
    #                 'receiver'  : user.id,
    #                 'template'  : template.id,
    #                 'message'   : message,
    #                 'company_id': rec.create_uid.company_id.id,
    #                 'id_record' : rec.id,
    #                 'ref'       : rec.name,
    #             })
    #
    # @api.model
    # def create(self, vals):
    #     result = super(RencanaTindakLanjut, self).create(vals)
    #     company_id = self.env.company.id
    #     for user in result.auditee_ids:
    #         if user.company_id:
    #             company_id = user.company_id.id
    #             break
    #
    #     link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
    #         self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
    #         result.id,
    #         result._name,
    #         company_id,
    #         self.env.ref('cni_audit.menu_rencana_tindak_lanjut').id
    #     )
    #     if result.create_date:
    #         year = result.create_date.year
    #         result.year = year
    #     condition = 'auditee'
    #     if result.type in ['qms', False]:
    #         view_id = self.env.ref('cni_audit.rencana_tindak_lanjut_view_form').id
    #         link = f"{link}&view_id={view_id}"
    #         result.view_id = view_id
    #         result.url = link
    #         result.send_notification_request(condition)
    #     elif result.type == 'audit':
    #         view_id = self.env.ref('cni_audit.internal_audit_tindak_lanjut_view_form').id
    #         link = f"{link}&view_id={view_id}"
    #         result.view_id = view_id
    #         result.url = link
    #         result.send_notification_internal_audit(condition)
    #     return result
    #
    # @api.depends('plor_id')
    # def _compute_access_auditee(self):
    #     for rec in self:
    #         access_auditee = False
    #         if rec.auditee_ids and self._uid in rec.auditee_ids.mapped('user_id').ids:
    #             access_auditee = True
    #         elif rec.auditee_id and rec.auditee_id.user_id.id == self._uid:
    #             access_auditee = True
    #         rec.access_auditee = access_auditee
    #

    def request_approval(self):
        result = super(RencanaTindakLanjut,self).request_approval()
        for rec in self:
            rec.register_approval_task()
        return result

    # def request_approval(self):
    #     approvers = self.env['cni_audit.approval'].search([('employee_id', '!=', False)], order='sequence')
    #     waiting = [(5,0,0)]
    #     for approver in approvers:
    #         waiting.append((0, 0, {
    #             'employee_id': approver.employee_id.id,
    #             'email': approver.email,
    #             'sequence': approver.sequence,
    #         }))
    #     self.write({
    #         'state': 'waiting',
    #         'approval_ids': waiting,
    #     })
    #     approval = self.env['rencana.tindak.lanjut.approval'].search([('tindak_lanjut_id', '=', self.id), ('state', '=', 'waiting')], order='sequence',limit=1)
    #     if approval:
    #         if self.type in ['qms', False]:
    #             self.send_notification_approval(approval.employee_id, approval)
    #         else:
    #             self.send_notification_approval_internal_audit(approval.employee_id, approval)
    #
    #
    # def send_notification_approval(self, employee_id, model_id):
    #     email = self.env['send_message.email']
    #     template = self.env.ref('cni_audit.leader_auditor_mail_template')
    #     param_wa = self.env.ref('cni_audit.message_wa_leader_audit').value
    #     if model_id.tindak_lanjut_id.auditee_ids:
    #         message_wa = param_wa.replace("{approver}", model_id.employee_id.name).replace("{name}", model_id.tindak_lanjut_id.name)
    #         auditee_names = []
    #         auditee_departments = []
    #         for auditee in model_id.tindak_lanjut_id.auditee_ids:
    #             auditee_names.append(auditee.name)
    #         auditee_name = ', '.join(auditee_names)
    #         auditee_data = message_wa.replace("{auditee}", auditee_name)
    #         message_wa = auditee_data.replace("{link}", model_id.tindak_lanjut_id.url)
    #     elif model_id.tindak_lanjut_id.auditee_id:
    #         message_wa = param_wa.replace("{approver}", model_id.employee_id.name).replace("{name}", model_id.tindak_lanjut_id.name)
    #         auditee_name = model_id.tindak_lanjut_id.auditee_id.name
    #         message_wa = message_wa.replace("{auditee}", auditee_name).replace("{link}", model_id.tindak_lanjut_id.url)
    #     email.create({
    #         'receiver'  : employee_id.user_id.id,
    #         'template'  : template.id,
    #         'message'   : message_wa,
    #         'company_id': model_id.tindak_lanjut_id.create_uid.company_id.id,
    #         'id_record' : model_id.id,
    #         'ref'       : model_id.tindak_lanjut_id.name
    #     })
    #
    # def send_notification_approval_internal_audit(self, employee_id, model_id):
    #     params = self.env['ir.config_parameter'].sudo()
    #     off_notification = params.get_param('cni_audit.off_notification')
    #     if off_notification:
    #         return
    #     email = self.env['send_message.email']
    #     template = self.env.ref('cni_audit.leader_auditor_mail_template')
    #     param_wa = self.env.ref('cni_audit.message_wa_leader_audit').value
    #     if model_id.tindak_lanjut_id.auditee_ids:
    #         message_wa = param_wa.replace("{approver}", model_id.employee_id.name).replace("{name}", model_id.tindak_lanjut_id.name)
    #         auditee_names = []
    #         auditee_departments = []
    #         for auditee in model_id.tindak_lanjut_id.auditee_ids:
    #             auditee_names.append(auditee.name)
    #         auditee_name = ', '.join(auditee_names)
    #         auditee_data = message_wa.replace("{auditee}", auditee_name)
    #         message_wa = auditee_data.replace("{link}", model_id.tindak_lanjut_id.url)
    #     elif model_id.tindak_lanjut_id.auditee_id:
    #         message_wa = param_wa.replace("{approver}", model_id.employee_id.name).replace("{name}", model_id.tindak_lanjut_id.name)
    #         auditee_name = model_id.tindak_lanjut_id.auditee_id.name
    #         message_wa = message_wa.replace("{auditee}", auditee_name).replace("{link}", model_id.tindak_lanjut_id.url)
    #     email.create({
    #         'receiver'  : employee_id.user_id.id,
    #         'template'  : template.id,
    #         'message'   : message_wa,
    #         'company_id': model_id.tindak_lanjut_id.create_uid.company_id.id,
    #         'id_record' : model_id.id,
    #         'ref'       : model_id.tindak_lanjut_id.name
    #     })
    #
    #
    #
    #
    def action_approval(self):
        result = super(RencanaTindakLanjut,self).action_approval()
        for rec in self:
            rec.register_approval_task()
        return result

    def write(self, vals):
        # handling bila keluar approval
        in_waiting_approval = []
        if 'state' in vals:
            in_waiting_approval = [res.id for res in self if res.state in ['open','progress','waiting']]
        result = super(RencanaTindakLanjut,self).write(vals)
        for rec in self:
            if rec.id in in_waiting_approval and rec.state not in ['open','progress','waiting']:
                rec.unregister_approval_task(skip_create_approval_log=True)
        return result
    # def action_approval(self):
    #     for rec in self:
    #         approval = self.env['rencana.tindak.lanjut.approval'].search([('employee_id.user_id', '=', self._uid), ('tindak_lanjut_id', '=', rec.id)], order='sequence asc',limit=1)
    #         if approval:
    #             approval.write({
    #                 'state': 'approve'
    #             })
    #         else:
    #             raise ValidationError(_("You are not allowed to approve this request."))
    #
    #         approval = self.env['rencana.tindak.lanjut.approval'].search([('tindak_lanjut_id', '=', rec.id), ('state', '=', 'waiting')], order='sequence asc',limit=1)
    #         if not approval:
    #             rec.send_notification_request('closed')
    #             rec.plor_id.write({'state':'close'})
    #             rec.write({
    #                 'state': 'close',
    #                 'date_auditor_approve': fields.Datetime.now()
    #             })
    #         else:
    #             if self.type in ['qms', False]:
    #                 self.send_notification_approval(approval.employee_id, approval)
    #             else:
    #                 self.send_notification_approval_internal_audit(approval.employee_id, approval)
    #
    #
    #
    #
    # def compute_access_approval(self):
    #     for rec in self:
    #         access = False
    #         if rec.approval_ids:
    #             approval = self.env['rencana.tindak.lanjut.approval'].search([('state', '!=', 'approve'), ('tindak_lanjut_id', '=', rec.id)], order='sequence asc', limit=1)
    #             if approval.employee_id.user_id.id == self._uid:
    #                 access = True
    #         rec.access_approval = access
    #
    #
    # def action_reject_approval(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Comment Reject'),
    #         'res_model': 'audit.comment.reject',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {
    #             'active_id': self.id,
    #             'default_tindak_lanjut_id': self.id,
    #             'default_state':self.state
    #         },
    #         'views': [[False, 'form']]
    #     }
    #
    #
    def request_approval_audit(self):
        # handling saat masuk approval
        result =super(RencanaTindakLanjut,self).request_approval_audit()
        for rec in self:
            rec.register_approval_task()
        return result
    # def request_approval_audit(self):
    #     approvers = self.env.ref('cni_audit.group_cni_internal_leader_audit')
    #     waiting = [(5,0,0)]
    #     for approver in approvers.users:
    #         employee = approver.employee_ids[0]
    #         waiting.append((0, 0, {
    #             'employee_id': employee.id,
    #             'email': approver.work_email,
    #         }))
    #     self.write({
    #         'state': 'waiting',
    #         'approval_ids': waiting,
    #     })
    #     approvals = self.env['rencana.tindak.lanjut.approval'].search([('tindak_lanjut_id', '=', self.id), ('state', '=', 'waiting')])
    #     if approvals:
    #         for approval in approvals:
    #             if self.type in ['qms', False]:
    #                 self.send_notification_approval(approval.employee_id, approval)
    #             else:
    #                 self.send_notification_approval_internal_audit(approval.employee_id, approval)
    #
    # def action_approve_leader_audit(self):
    #     self.plor_id.write({'state':'close'})
    #     self.write({
    #         'state': 'close',
    #         'date_auditor_approve': fields.Datetime.now()
    #     })
    #
    #
    #
    # def _compute_access_edit_button(self):
    #     for rec in self:
    #         rec.access_edit_button = """<style>.o_form_button_edit {display: none !important;}</style>"""
    #         if rec.create_uid.id == self.env.uid and rec.state == 'progress':
    #             rec.access_edit_button = False
    #         elif rec.auditee_id and rec.auditee_id.user_id.id == self.env.uid and rec.state == 'draft':
    #             rec.access_edit_button = False
    #         elif rec.manager_auditee_id and rec.manager_auditee_id.user_id.id == self.env.uid and rec.state == 'open':
    #             rec.access_edit_button = False
    #         elif self.user_has_groups('cni_audit.group_cni_internal_leader_audit') and rec.state == 'waiting':
    #             rec.access_edit_button = False
    #
    #
    # def send_notification_internal_audit(self, condition):
    #     params = self.env['ir.config_parameter'].sudo()
    #     off_notification = params.get_param('cni_audit.off_notification')
    #     if off_notification:
    #         return
    #
    #     email = self.env['send_message.email']
    #     if condition == 'auditee':
    #         template_email = self.env.ref('cni_audit.audit_auditee_to_submit_mail_template')
    #         user_id = self.auditee_id.user_id
    #     elif condition == 'manager':
    #         template_email = self.env.ref('cni_audit.audit_manager_to_approve_mail_template')
    #         user_id = self.manager_auditee_id.user_id
    #     elif condition == 'auditor':
    #         template_email = self.env.ref('cni_audit.audit_auditor_to_validate_mail_template')
    #         user_id = self.auditor_id.user_id
    #     elif condition == 'reject':
    #         template_email = self.env.ref('cni_audit.audit_auditor_to_reject_mail_template')
    #         user_id = self.auditee_id.user_id
    #
    #     email.create({
    #         'receiver'  : user_id.id,
    #         'template'  : template_email.id,
    #         'is_send_wa': True,
    #         'company_id': self.create_uid.company_id.id,
    #         'id_record' : self.id,
    #         'ref'       : self.name
    #     })
    #
    #
    # def search_filter_tindak_lanjut_internal_audit(self, operator, operand):
    #     """Filter for internal audit, to show only the rencana tindak lanjut that the user is involved in"""
    #     if self.user_has_groups('cni_audit.group_cni_internal_auditor'):
    #         return []
    #     else:
    #         user_auditees = self.search([('auditee_id.user_id', '=', self._uid), ('type', '=', 'audit')]).ids
    #         user_approvers = self.search([('manager_auditee_id.user_id', '=', self._uid), ('type', '=', 'audit')]).ids
    #         ids = user_auditees + user_approvers
    #         ids = list(set(ids))
    #         return [('id', 'in', ids)]
    #
    #
    # def search_filter_tindak_lanjut_to_approve_internal_audit(self, operator, operand):
    #     """Filter for internal audit, to show only the rencana tindak lanjut that the user can approve"""
    #     data = []
    #     for rencanas in self.sudo().search([('state', '=', 'waiting'), ('type', '=', 'audit')]):
    #         approval = self.env['rencana.tindak.lanjut.approval'].search([('state', '!=', 'approve'), ('tindak_lanjut_id', '=', rencanas.id)], order='sequence asc', limit=1)
    #         if approval and approval.employee_id.user_id.id == self._uid:
    #             data.append(rencanas.id)
    #     if self.user_has_groups('cni_audit.group_cni_internal_auditor'):
    #         ids = self.search([('state', '=', 'progress'), ('type', '=', 'audit')]).ids
    #         ids += data
    #     else:
    #         tindak_lanjuts = self.search([('manager_auditee_id.user_id', '=', self.env.user.id),('state','=','open'),('manager_has_approve','=',False), ('type', '=', 'audit')])
    #         ids = tindak_lanjuts.ids
    #         ids += data
    #
    #     ids = list(set(ids))
    #     return [('id', 'in', ids)]
    #
        




