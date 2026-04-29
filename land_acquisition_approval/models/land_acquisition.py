# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class LandAcquisition(models.Model):
    _name = "land.acquisition"
    _inherit = [_name, 'approval.transaction.task.able.mixin']

    # data yang di perlukan oleh approval.tsk dan mobile.approval.task
    def get_internal_number(self):
        return self.name

    def get_internal_document(self):
        return self._description

    def get_internal_description(self):
        return self.desc

    def get_internal_requester_id(self):
        return self.requester_id.user_id.id

    # untuk build internal url
    def get_internal_menu_id(self):
        return 'cni_inventory_intra.menu_to_approve_material_inventory_request'

    def get_internal_action_id(self):
        return 'cni_inventory_intra.to_approve_material_inventory_request_action'

    def get_next_approval_task_line(self, **kwargs):
        if self.state == 'waiting':
            return self.env['land.acquisition.approval'].get_next_approval_task_line(transaction_id= self.id,transaction_model_name=self._name)
        if self.state == 'survey':
            return self.env['land.acquisition.survey.approval'].get_next_approval_task_line(transaction_id= self.id,transaction_model_name=self._name)

        return None

    def register_approval_task(self, **kwargs):
        rec = self.ensure_one()
        kw = dict(kwargs)
        if 'transaction_object' not in kw:
            kw['transaction_object'] = rec
        if rec.state in ['waiting','survey']:
            approval_task_line = rec.get_next_approval_task_line()
            return approval_task_line and approval_task_line.register_approval_task(**kw)
        elif rec.state =='cost_control':
            kw['group_ids'] = self.env.ref('cni_inventory_intra.cost_control_group')
        else:
            return None

        return super(LandAcquisition, self).register_approval_task(**kw)



    # def default_requester(self):
    #     employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
    #
    #     return employee_id.id
    #
    # name = fields.Char(string='No.', copy=False, index=True)
    # requester_id = fields.Many2one('hr.employee', string='Requester', default=default_requester)
    # department_id = fields.Many2one('hr.department', string='Department')
    # active = fields.Boolean(string="Active", default=True)
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('waiting', 'Waiting Approval'),
    #     ('verification', 'LA Verification'),
    #     ('survey', 'Survey Approval'),
    #     ('cost_control', 'Cost Control'),
    #     ('payment_request', 'Payment Request'),
    #     ('done', 'Done')
    # ], default='draft', string='Status', tracking=True)
    # date_required = fields.Date(string='Date Required', index=True)
    # desc = fields.Text(string='Description')
    # required_year = fields.Char(string='Year (Budget)', index=True)
    # area_id = fields.One2many('land.acquisition.area', 'la_id', string='Areas', ondelete='cascade')
    # company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    # approval_id = fields.One2many('land.acquisition.approval', 'la_id', string='Approval', ondelete='cascade')
    # access_approve = fields.Boolean(string='Access Button', compute='_compute_access_approve')
    # filter_approver = fields.Boolean(string='Filter Approver', compute=True, search='search_filter_approver')
    # filter_verification = fields.Boolean(string='Filter Verification', compute=True, search='search_filter_verification')
    # survey_approval_id = fields.One2many('land.acquisition.survey.approval', 'la_id', string='Survey Approval', ondelete='cascade')
    # access_survey_approve = fields.Boolean(string='Access Button Survey Approv', compute='_compute_access_survey_button')
    # url = fields.Text(string="URL")
    # currency_id = fields.Many2one(
    #     "res.currency",
    #     string="Currency",
    #     required=True,
    #     default=lambda self: self.env.user.company_id.currency_id.id,
    # )
    # total_compute = fields.Monetary(string='Total', compute='compute_total', store=False)
    # total = fields.Monetary(related='total_compute', store=True)
    # # payment_request_id = fields.One2many('payment.request', 'la_id', string='Payment_Request', ondelete='cascade')
    # # payment_request_count = fields.Integer(string='Count', compute='_compuate_payment_request_count', default=0)
    # filter_cost_control = fields.Boolean(string='Filter Cost Control', compute=True, search='search_filter_cost_control')
    # alert_waiting_approval = fields.Text(string="Alert waiting approval", compute="compute_approver_name")
    # notes = fields.Text(string='Notes')


    # @api.model
    # def create(self, vals):
    #     """untuk penamaan pada document"""
    #     if vals.get('name', _('New')) == _('New'):
    #         find_dcr = True
    #         while find_dcr:
    #             vals['name'] = self.env['ir.sequence'].next_by_code('land.aquisition') or _('New')
    #             find_dcr = self.env['land.acquisition'].search([('name', '=', vals['name'])], limit=1)
    #         result = super(LandAcquisition, self).create(vals)
    #         link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s'%(
    #                 self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
    #                 result.id,
    #                 result._name,
    #                 result.company_id.id,
    #                 self.env.ref('land_acquisition.land_acquisition_root_menu').id
    #             )
    #         result.url = link
    #
    #     return result
    #
    # @api.onchange('requester_id')
    # def onchange_requester_id(self):
    #     """jika field requester berubah maka akan berpengaruh pada field yang dipilih"""
    #     for rec in self:
    #         rec.department_id = False
    #         rec.approval_id = False
    #         approver = []
    #         if rec.requester_id:
    #             rec.department_id = rec.requester_id.department_id.id
    #
    #         if rec.requester_id.parent_id:
    #             approver.append((0,0,{
    #                 'user_id': rec.requester_id.parent_id.user_id.id
    #             }))
    #         else:
    #             raise ValidationError(_("Anda belum mempunyai atasan"))
    #         rec.approval_id = approver
    def button_submit(self):
        # handling saat masuk approval
        result =super(LandAcquisition,self).button_submit()
        for rec in self:
            rec.register_approval_task()
        return result
    # def button_submit(self):
    #     """untuk button submit"""
    #     for rec in self:
    #         if not rec.area_id:
    #             raise ValidationError(_('Area Harus Diisi'))
    #         if rec.notes:
    #             rec.notes = None
    #
    #         cron = self.env['send_message.email']
    #         template = self.env.ref('land_acquisition.land_acquisition_approver_mail_template')
    #         approver = self.env['land.acquisition.approval'].sudo().search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1)
    #         for user in approver.user_id:
    #             #parameter mwssage wa and replace
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_approval")
    #             message_wa = params_message_wa.replace("{approver}", user.partner_id.name).replace("{kode}", rec.name).replace("{requester}",
    #                         rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}",
    #                         rec.url if rec.url else "")
    #             cron.create({
    #                 'receiver'    : user.id,
    #                 'template'    : template.id,
    #                 'message'     : message_wa,
    #                 'company_id'  : rec.company_id.id,
    #                 'id_record'   : rec.id,
    #                 'ref'         : rec.name
    #             })
    #
    #     self.write({'state': 'waiting'})

    # def button_reject_waiting(self):
    #     """untuk button reject saat state waiting"""
    #     return {
    #         'name'      : 'Reject Message',
    #         'type'      : 'ir.actions.act_window',
    #         'view_mode' : 'form',
    #         'res_model' : 'popup.reject.message',
    #         'target'    : 'new',
    #         'context'   : {
    #             'la_waiting'      : True
    #             }
    #     }
    def button_approve_waiting(self):
        # handling saat masuk approval
        result =super(LandAcquisition,self).button_approve_waiting()
        for rec in self:
            rec.register_approval_task()
        return result
    # def button_approve_waiting(self):
    #     """untuk button approve"""
    #     for rec in self:
    #         approval_id = self.env['land.acquisition.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1)
    #         if self.env.uid in approval_id.user_id.ids:
    #             approval_id.write({'status': 'approved'})
    #
    #         cron = self.env['send_message.email']
    #         template = self.env.ref('land_acquisition.land_acquisition_approver_mail_template')
    #         approver = self.env['land.acquisition.approval'].sudo().search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1)
    #         for user in approver.user_id:
    #             #parameter mwssage wa and replace
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_approval")
    #             message_wa = params_message_wa.replace("{approver}", user.partner_id.name).replace("{kode}", rec.name).replace("{requester}",
    #                         rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}",
    #                         rec.url if rec.url else "")
    #             cron.create({
    #                 'receiver'    : user.id,
    #                 'template'    : template.id,
    #                 'message'     : message_wa,
    #                 'company_id'  : rec.company_id.id,
    #                 'id_record'   : rec.id,
    #                 'ref'         : rec.name
    #             })
    #         self._cr.commit()
    #         approval_ids = self.env['land.acquisition.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')])
    #         if not approval_ids:
    #             self.write({'state': 'verification'})
    
    
    @api.depends('approval_id')
    def _compute_access_approve(self):
        """untuk akses button approve"""
        for rec in self:
            rec.access_approve = False
            approval_ids = self.env['land.acquisition.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')], order='id asc', limit=1)
            for line in approval_ids.filtered(lambda l: l.user_id.id == self.env.uid):
                rec.access_approve = True

    def button_approve_la(self):
        # handling saat masuk approval
        result =super(LandAcquisition,self).button_approve_la()
        for rec in self:
            rec.register_approval_task()
        return result

    # def button_approve_la(self):
    #     """untuk button approve di status verification dan sekaligus buat survey approval"""
    #     for rec in self:
    #         approver = []
    #         survey_approvals = self.env['land.acquisition.matrix.approval'].search([('seq', '!=', False)], order='seq asc')
    #         for survey_approval in survey_approvals:
    #             if survey_approval.approver == True:
    #                 if rec.requester_id.parent_id:
    #                     approver.append((0, 0, {
    #                         'seq': survey_approval.seq,
    #                         'user_id' : rec.requester_id.parent_id.user_id.id,
    #                         'job_id': rec.requester_id.parent_id.job_id.id
    #                     }))
    #                 else:
    #                     raise ValidationError(_("Anda belum mempunyai atasan"))
    #             else:
    #                 approver.append((0,0,{
    #                     'seq': survey_approval.seq,
    #                     'user_id': survey_approval.user_id.id,
    #                     'job_id': survey_approval.job_id.id
    #                 }))
    #         if not rec.survey_approval_id:
    #             rec.survey_approval_id = approver
    #         self._cr.commit()
    #         cron = self.env['send_message.email']
    #         template = self.env.ref('land_acquisition.land_acquisition_approver_mail_template')
    #         approver = self.env['land.acquisition.survey.approval'].sudo().search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1)
    #         for user in approver.user_id:
    #             #parameter mwssage wa and replace
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_approval")
    #             message_wa = params_message_wa.replace("{approver}", user.partner_id.name).replace("{kode}", rec.name).replace("{requester}",
    #                         rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}",
    #                         rec.url if rec.url else "")
    #             cron.create({
    #                 'receiver'    : user.id,
    #                 'template'    : template.id,
    #                 'message'     : message_wa,
    #                 'company_id'  : rec.company_id.id,
    #                 'id_record'   : rec.id,
    #                 'ref'         : rec.name
    #             })
    #     self.write({'state': 'survey'})


    # def button_reject_verification(self):
    #     """untuk button reject saat state verification"""
    #     return {
    #         'name'      : 'Reject Message',
    #         'type'      : 'ir.actions.act_window',
    #         'view_mode' : 'form',
    #         'res_model' : 'popup.reject.message',
    #         'target'    : 'new',
    #         'context'   : {
    #             'la_verification'      : True
    #             }
    #     }
    
    # def search_filter_approver(self, operator, operand):
    #     """untuk menambahkan la pada menu to approve berdasarkan approvernya"""
    #     ids = []
    #     las_waiting = self.env['land.acquisition'].search([('state', '=', 'waiting')])
    #     for la in las_waiting:
    #         for approval in la.approval_id:
    #             if approval.user_id.id == self.env.uid and approval.status == 'waiting':
    #                 ids.append(la.id)
    #
    #     la_survey_approvals = self.env['land.acquisition'].search([('state', '=', 'survey')])
    #     for la in la_survey_approvals:
    #         approval = self.env['land.acquisition.survey.approval'].sudo().search([('la_id', '=', la.id), ('status', '=', 'waiting')], limit=1, order='seq asc')
    #         if approval.user_id.id == self.env.uid:
    #             ids.append(approval.la_id.id)
    #
    #     return [('id', 'in', ids)]
    #
    # def search_filter_verification(self, operator, operand):
    #     """untuk menambahkan la pada menu to approve pada vrifikasi dept.exrel la"""
    #     ids = []
    #     las_verification = self.env['land.acquisition'].search([('state', '=', 'verification')])
    #     for la in las_verification:
    #         if self.user_has_groups('land_acquisition.exrel_land_acquisition'):
    #             ids.append(la.id)
    #
    #     return [('id', 'in', ids)]
    
    def button_approve_la_survey(self):
        # handling saat masuk approval
        result =super(LandAcquisition,self).button_approve_la_survey()
        for rec in self:
            rec.register_approval_task()
        return result

    # def button_approve_la_survey(self):
    #     """untuk approve la pada saat status survey approval"""
    #     for rec in self:
    #         approval_id = self.env['land.acquisition.survey.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1)
    #         if self.env.uid in approval_id.user_id.ids:
    #             approval_id.write({'status': 'approved'})
    #
    #         cron = self.env['send_message.email']
    #         template = self.env.ref('land_acquisition.land_acquisition_approver_mail_template')
    #         approver = self.env['land.acquisition.survey.approval'].sudo().search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1)
    #         for user in approver.user_id:
    #             #parameter mwssage wa and replace
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_approval")
    #             message_wa = params_message_wa.replace("{approver}", user.partner_id.name).replace("{kode}", rec.name).replace("{requester}",
    #                         rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}",
    #                         rec.url if rec.url else "")
    #             cron.create({
    #                 'receiver'    : user.id,
    #                 'template'    : template.id,
    #                 'message'     : message_wa,
    #                 'company_id'  : rec.company_id.id,
    #                 'id_record'   : rec.id,
    #                 'ref'         : rec.name
    #             })
    #
    #         self._cr.commit()
    #         approval_ids = self.env['land.acquisition.survey.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')])
    #         if not approval_ids:
    #             self.write({'state': 'cost_control'})
    #
    #             cron = self.env['send_message.email']
    #             template = self.env.ref('land_acquisition.land_acquisition_cost_control_mail_template')
    #             cost_control = self.env.ref('cni_inventory_intra.cost_control_group')
    #             for user in cost_control.users:
    #                 #parameter mwssage wa and replace
    #                 params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_cost_control")
    #                 message_wa = params_message_wa.replace("{cost_control}", user.partner_id.name).replace("{kode}", rec.name).replace("{requester}",
    #                             rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}",
    #                         rec.url if rec.url else "")
    #                 cron.create({
    #                     'receiver'    : user.id,
    #                     'template'    : template.id,
    #                     'message'     : message_wa,
    #                     'company_id'  : rec.company_id.id,
    #                     'id_record'   : rec.id,
    #                     'ref'         : rec.name
    #                 })


    # def button_reject_la_survey(self):
    #     """untuk button reject saat state survey approval"""
    #     return {
    #         'name'      : 'Reject Message',
    #         'type'      : 'ir.actions.act_window',
    #         'view_mode' : 'form',
    #         'res_model' : 'popup.reject.message',
    #         'target'    : 'new',
    #         'context'   : {
    #             'la_survey_approval' : True
    #             }
    #     }
        
    
    
    # @api.depends('survey_approval_id')
    # def _compute_access_survey_button(self):
    #     for rec in self:
    #         rec.access_survey_approve = False
    #         approval_ids = self.env['land.acquisition.survey.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')], order='seq asc', limit=1)
    #         for line in approval_ids.filtered(lambda l: l.user_id.id == self.env.uid):
    #             rec.access_survey_approve = True


    # def button_approve_cost_control(self):
    #     """untuk approve cost control, membuat payment request dan mengirim notif wa serta email kepada director operation"""
    #     for rec in self:
    #         email = self.env['send_message.email']
    #         payment_request = self.env['payment.request']
    #         # line = []
    #         # for area in rec.area_id:
    #         #     line.append((0,0, {
    #         #         'name': area.name,
    #         #         'amount': area.total
    #         #     }))
    #         # data = payment_request.create({
    #         #     'request_date': date.today(),
    #         #     'la_id': rec.id,
    #         #     'user_id': rec.requester_id.id,
    #         #     'due_date': rec.date_required,
    #         #     'department_id': rec.department_id.id,
    #         #     'request_id': rec.requester_id.id,
    #         #     'reference': rec.name,
    #         #     'priority': 'normal',
    #         #     'line_ids': line
    #         # })
    #
    #         # data.action_submit()
    #         template = self.env.ref('land_acquisition.land_acquisition_approve_dirops_mail_template')
    #         dirops = self.env['hr.employee'].sudo().search([('job_id.name', '=', 'DIRECTOR OPERATION')])
    #         params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_approve_dirops")
    #         message_wa = params_message_wa.replace("{dirops}", dirops.name).replace("{kode}", rec.name).replace("{requester}", rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}", rec.url)
    #         #buat antrian untuk kirim wa dan email
    #         email.create({
    #             'receiver'    : dirops.user_id.id,
    #             'template'    : template.id,
    #             'is_send'     : False,
    #             'is_send_wa'  : False,
    #             'message'     : message_wa,
    #             'company_id'  : rec.company_id.id,
    #             'id_record'   : rec.id,
    #             'ref'         : rec.name
    #         })
    #     self.write({'state': 'done'})

    
    # def button_reject_cost_control(self):
    #     """untuk reject cost control dan mengirim notif wa serta email kepada director operation"""
    #     for rec in self:
    #         email = self.env['send_message.email']
    #         template = self.env.ref('land_acquisition.land_acquisition_reject_dirops_mail_template')
    #         dirops = self.env['hr.employee'].sudo().search([('job_id.name', '=', 'DIRECTOR OPERATION')])
    #         params_message_wa = self.env["ir.config_parameter"].sudo().get_param("land_acquisition.message_wa_reject_dirops")
    #         message_wa = params_message_wa.replace("{dirops}", dirops.name).replace("{kode}", rec.name).replace("{requester}", rec.requester_id.name).replace("{department}", rec.department_id.name if rec.department_id else "-").replace("{link}", rec.url)
    #         #buat antrian untuk kirim wa dan email
    #         email.create({
    #             'receiver'    : dirops.user_id.id,
    #             'template'    : template.id,
    #             'is_send'     : False,
    #             'is_send_wa'  : False,
    #             'message'     : message_wa,
    #             'company_id'  : rec.company_id.id,
    #             'id_record'   : rec.id,
    #             'ref'         : rec.name
    #         })
    #
    #     return {
    #         'name'      : 'Reject Message',
    #         'type'      : 'ir.actions.act_window',
    #         'view_mode' : 'form',
    #         'res_model' : 'popup.reject.message',
    #         'target'    : 'new',
    #         'context'   : {
    #             'la_cost_control' : True
    #             }
    #     }
    #
    # @api.depends('area_id', 'area_id.total')
    # @api.onchange('area_id', 'area_id.total')
    # def compute_total(self):
    #     """untuk menghitung total pada field total"""
    #     for rec in self:
    #         total = sum(rec.area_id.mapped('total'))
    #         rec.total_compute = total


    # @api.depends('payment_request_id')
    # def _compuate_payment_request_count(self):
    #     for rec in self:
    #         rec.payment_request_count = len(rec.payment_request_id.ids)


    # def action_view_pr(self):
    #     self.ensure_one()
    #     action_vals = {
    #         'name': 'Payment Request(s)',
    #         'domain': [('id', 'in', self.payment_request_id.ids)],
    #         'view_type': 'form',
    #         'res_model': 'payment.request',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'context': {'create': False}
    #     }
    #     if len(self.payment_request_id) == 1:
    #         action_vals.update({'res_id': self.payment_request_id.id, 'view_mode': 'form'})
    #     else:
    #         action_vals['view_mode'] = 'tree,form'
    #     return action_vals


    # def search_filter_cost_control(self, operator, operand):
    #     """untuk menambahkan la pada menu to approve cost control"""
    #     ids = []
    #     las_cost_control = self.env['land.acquisition'].search([('state', '=', 'cost_control')])
    #     for la in las_cost_control:
    #         # if self.user_has_groups('cni_inventory_intra.cost_control_group'):
    #         ids.append(la.id)
    #
    #     return [('id', 'in', ids)]
    #
    # def compute_approver_name(self):
    #     for rec in self:
    #         job = ""
    #         alert_approval = ""
    #         alert_survey_approval = ""
    #         rec.alert_waiting_approval = ""
    #         param = self.env['ir.config_parameter'].get_param('cni_inventory_intra.alert_waiting_approval')
    #         approver_name = ""
    #         approver = self.env['land.acquisition.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1, order='id asc')
    #         if approver:
    #             if approver.job_id:
    #                 job = "("+approver.job_id.name+")"
    #                 approver_name = approver.user_id.name + job
    #             else:
    #                 approver_name = approver.user_id.name
    #
    #             alert_approval = param.replace("{approver}", str(approver_name))
    #         survey_approver = self.env['land.acquisition.survey.approval'].search([('la_id', '=', rec.id), ('status', '=', 'waiting')], limit=1, order='seq asc')
    #         if survey_approver:
    #             if survey_approver.job_id:
    #                 job = "("+survey_approver.job_id.name+")"
    #                 approver_name = survey_approver.user_id.name + job
    #             else:
    #                 approver_name = survey_approver.user_id.name
    #
    #             alert_survey_approval = param.replace("{approver}", str(approver_name))
    #         if alert_approval:
    #             rec.alert_waiting_approval = alert_approval
    #         elif alert_survey_approval:
    #             rec.alert_waiting_approval = alert_survey_approval
    #