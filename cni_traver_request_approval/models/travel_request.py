# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class TravelRequest(models.Model):
    _name = 'travel.request'
    _inherit = [_name,'approval.transaction.task.able.mixin']
    # _check_company_auto = True
    # untuk approval task
    def get_internal_number(self):
        return self.name

    def get_internal_document(self):
        return self._description

    def get_internal_description(self):
        return self.desc

    # untuk build internal url
    def get_internal_menu_id(self):
        return 'cni_travel_request.travel_management_root_menu'

    def get_internal_action_id(self):
        return 'cni_travel_request.travel_to_approve_action'

    def get_internal_requester_id(self):
        return self.user_id.id

    def get_next_approval_task_line(self,**kwargs):
        return self.approval_ids.get_next_approval_task_line()

    def register_approval_task(self,**kwargs):
        rec = self.ensure_one()
        kw = dict(kwargs)
        if 'transaction_object' not in kw:
            kw['transaction_object'] = rec
        #'submit', 'cost_control', 'hc_approval'
        if rec.state == 'submit':
            approval_task_line = rec.get_next_approval_task_line()
            return approval_task_line and approval_task_line.register_approval_task(**kw)
        elif rec.state=='cost_control':
            kw['user_ids'] = None
            kw['group_ids'] = self.env.ref('cni_travel_request.travel_cost_control')
        elif rec.state == 'hc_approval':
            kw['user_ids'] = None
            kw['group_ids'] = self.env.ref('cni_travel_request.travel_hc_approval')
        else:
            return None

        return super(TravelRequest,self).register_approval_task(**kw)

    def unregister_approval_task(self,skip_create_approval_log=True,**kwargs):
        return super(TravelRequest,self).unregister_approval_task(skip_create_approval_log=skip_create_approval_log,**kwargs)

    def write(self, vals):
        # handling bila keluar approval
        in_waiting_approval = []
        if 'state' in vals:
            in_waiting_approval = [res.id for res in self if res.state in ['submit','cost_control','hc_approval']]
        result = super(TravelRequest,self).write(vals)
        for rec in self:
            if rec.id in in_waiting_approval and rec.state not in ['submit','cost_control','hc_approval']:
                rec.unregister_approval_task(skip_create_approval_log=True)
        return result

    # name = fields.Char('')
    # departure_date = fields.Datetime('Departure Date', tracking=True, readonly=True,
    #                                  states={'draft': [('readonly', False)]})
    # return_date = fields.Datetime('Return Date', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    # category = fields.Selection([
    #     ('business', 'BUSINESS'),
    #     ('fb', 'FIELD BREAK'),
    # ], string='Category', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    # route_id = fields.Many2one('travel.route', string='Route', tracking=True, readonly=True,
    #                            states={'draft': [('readonly', False)]})
    # have_ticket = fields.Boolean('Have Ticket', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    # desc = fields.Text('Description', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('submit', 'Waiting Approve'),
    #     ('approve', 'Approved'),
    #     ('cost_control', 'Cost Control'),
    #     ('hc_approval', 'HC Approval'),
    #     ('approve_hrga', 'Processed on GA'),
    #     ('issued', 'Issued'),
    #     ('claimed', 'Claim Submitted'),
    #     ('done', 'Done'),
    #     ('reject', 'Rejected'),
    # ], string='Status', default='draft', copy=False, tracking=True)
    # batch_request = fields.Boolean('Batch Request', tracking=True, readonly=True,
    #                                states={'draft': [('readonly', False)]})
    # employee_id = fields.Many2one('hr.employee', string='Employee', default=lambda self: self.env.user.employee_id.id)
    # user_id = fields.Many2one('res.users', string='Requester', default=lambda self: self.env.user)
    # employee_ids = fields.Many2many('hr.employee', string='Employee', tracking=True, readonly=True,
    #                                 states={'draft': [('readonly', False)]})
    # dept_manager_job_id = fields.Many2one('hr.job', string='Department Manager', default=lambda
    #     self: self.env.user.employee_ids.department_id.manager_id.job_id,
    #                                       tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    # department_id = fields.Many2one('hr.department', 'Unit')
    # manager_id = fields.Many2one('hr.employee', 'Approver', related="department_id.manager_id")
    # line_ids = fields.One2many('travel.detail', 'request_id', string='Line')
    # employee_traveller_ids = fields.One2many('employee.traveller', 'request_id', 'Employee',
    #                                          domain="[('employee_id','!=',False)]")
    # non_employee_traveller_ids = fields.One2many('non_employee.traveller', 'request_id', 'Non Employee',
    #                                              domain="[('employee_id','=',False)]")
    # self_traveller = fields.Boolean()
    # # request_date = fields.Date('Request Date',default=datetime.now())
    # request_date = fields.Date('Request Date', default=fields.Date.today())
    # add_requester_to_traveller = fields.Boolean('I am traveller')
    # self_ticket = fields.Boolean('Buy ticket by my self')
    # ticket_ids = fields.One2many('travel.ticket', 'request_id', 'Ticket')
    # accom_ids = fields.One2many('travel.accom', 'request_id', 'Accomodation')
    # transport_ids = fields.One2many('travel.transport', 'request_id', 'Local Transport')
    # my_request_filter = fields.Boolean(compute=True, search="search_my_request_filter")
    # to_approve_filter = fields.Boolean(compute=True, search="search_to_approve_filter")
    # to_update_filter = fields.Boolean(compute=True, search="search_to_update_filter")
    # approval_ids = fields.One2many('travel.approval', 'travel_id', string='Approval', ondelete='cascade')
    # company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    # # company_id = fields.Many2one('res.company', string='Company', readonly=True)
    # company_code = fields.Char(string='Company Code', related='company_id.code')
    #
    # x_css = fields.Html(
    #     string='CSS',
    #     sanitize=False,
    #     compute='_compute_css',
    #     store=False,
    # )
    # is_approver = fields.Boolean(compute="check_is_user")
    # is_cost_control_approver = fields.Boolean(compute="check_is_user")
    # is_hc_approver = fields.Boolean(compute="check_is_user")
    # is_creator = fields.Boolean(compute="check_is_user")
    # is_final_approver = fields.Boolean(compute="check_is_final_approver")
    # is_pic = fields.Boolean(compute="check_is_user")
    # is_ticket_pic = fields.Boolean(compute="check_is_user")
    # is_accom_pic = fields.Boolean(compute="check_is_user")
    # is_transport_pic = fields.Boolean(compute="check_is_user")
    # # acces_edit_apprval = fields.Boolean(compute="compute_acces_edit_apprval")
    # traveller_no = fields.Integer('Number of Traveller', compute="count_traveller")
    #
    # has_info = fields.Boolean(compute="check_travel_info")
    # issued = fields.Boolean(compute="_check_request")
    # claim_ids = fields.One2many('travel.claim', 'request_id', 'Claim')
    # has_claim = fields.Boolean(compute="check_travel_info")
    #
    # location_from = fields.Many2one('travel.location', string='From')
    # location_to = fields.Many2one('travel.location', string='To')
    # # travel_type = fields.Selection(
    # #     selection=[
    # #         ('domestic_need_flight', 'Domestic - Need Flight'),
    # #         ('domestic_no_flight', 'Domestic - No Flight'),
    # #         ('international', 'International'),
    # #     ],
    # #     string='Travel Type')
    # travel_type_id = fields.Many2one('travel.type', string='Travel Type')
    #
    # link_travel = fields.Char(string='Link Travel', compute='compute_link_travel')
    # ticket_pesawat = fields.Boolean(string='Ticket Pesawat')
    # akomodasi = fields.Boolean(string='Akomodasi')
    # transport = fields.Boolean(string='Transport (Penjemputan/Pengantaran)')
    # cash_advance = fields.Boolean(string='Cash Advance')
    # lampiran_formulir = fields.Binary(string='Lampiran Formulir', attachment=True)
    # lampiran_formulir_name = fields.Char(string='Lampiran Formulir Name')
    # lampiran_surat = fields.Binary(string='Lampiran Surat', attachment=True)
    # lampiran_surat_name = fields.Char(string='Lampiran Surat Name')
    # attachment_ids = fields.Many2many('ir.attachment', 'travel_attachment_rel', string='lampiran')
    # dynamic_approver = fields.Boolean(string='Dynamic Approver', compute='_compute_dynamic_approver')

    # def get_formulir_cash_advance(self):
    #     template_lampiran = self.env['travel.template.lampiran'].search([], limit=1)
    #     return {
    #         'type': 'ir.actions.act_url',
    #         # 'url': '/web/binary/download_document?model=%s&field=formulir_cash_advance&id=%s&filename=product_stock.xls'%(template_lampiran._name, template_lampiran.id),
    #         'url': f'/web/content/?model={template_lampiran._name}&id={template_lampiran.id}&field=formulir_cash_advance&filename_field=formulir_cash_advance_name&download=true',
    #         'target': 'self',
    #     }
    #
    # def get_surat_penugasan(self):
    #     template_lampiran = self.env['travel.template.lampiran'].search([], limit=1)
    #     return {
    #         'type': 'ir.actions.act_url',
    #         # 'url': '/web/binary/download_document?model=%s&field=surat_penugasan&id=%s&filename=product_stock.xls'%(template_lampiran._name, template_lampiran.id),
    #         'url': f'/web/content/?model={template_lampiran._name}&id={template_lampiran.id}&field=surat_penugasan&filename_field=surat_penugasan_name&download=true',
    #         'target': 'self',
    #     }

    # @api.onchange('travel_type_id')
    # @api.constrains('travel_type_id')
    # def get_ticket_pesawat(self):
    #     for rec in self:
    #         rec.ticket_pesawat = False
    #         if rec.travel_type_id.need_ticket == True:
    #             rec.ticket_pesawat = True

    # @api.depends('company_id')
    # def compute_link_travel(self):
    #     for rec in self:
    #         link = '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
    #             self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
    #             rec.id,
    #             rec._name,
    #             rec.company_id.id,
    #             self.env.ref('cni_travel_request.travel_management_root_menu').id
    #         )
    #         rec.link_travel = link

    # @api.depends('user_id')
    # def compute_acces_edit_apprval(self):
    #     for rec in self:
    #         rec.acces_edit_apprval = False
    #         if self.env.user.id in [1,2]:
    #             rec.acces_edit_apprval = True
    #         if self.env.user.id not in [1,2] and rec.company_code == 'CMP':
    #             rec.acces_edit_apprval = True

    # @api.onchange('department_id')
    # def onchange_department(self):
    #     for rec in self:
    #         if rec.department_id and not rec.department_id.manager_id:
    #             raise Warning(f'Manager untuk department {rec.department_id.name} belum ada')

    # @api.onchange('travel_type_id')
    # @api.constrains('travel_type_id')
    # def _onchange_travel_type_id(self):
    #     for rec in self:
    #         seq = 1
    #         approval = self.env['travel.approval'].sudo()
    #
    #         # APPROVER PERTAMA
    #         # if rec.manager_id and rec.manager_id.id == self.env.user.employee_id.id: # JIKA MANAGER UNIT SAMA DENGAN REQUESTER MAKA AMBIL PARENT DARI REQUESTER
    #         #     approval.append(rec.manager_id.parent_id)
    #         # elif rec.manager_id and not rec.manager_id.id == self.env.user.employee_id.id:
    #         #     approval.append(rec.manager_id)
    #         if rec.leave_request_id:
    #             approval = False
    #         else:
    #             if not self.user_has_groups('cni_travel_request.dynamic_travel_approvers'):
    #                 if rec.employee_id.parent_id:
    #                     employee = rec.employee_id.parent_id
    #                     if not approval.search([('travel_id', '=', rec.id), ('employee_id', '=', employee.id)]):
    #                         approval.sudo().create({
    #                             'travel_id': rec.id,
    #                             'seq': seq,
    #                             'employee_id': employee.id,
    #                             'job_id': employee.job_id.id,
    #                         })
    #                         seq += 1
    #
    #                 if rec.employee_id.parent_id.parent_id and 'DIRECTOR' not in str(
    #                         rec.employee_id.parent_id.parent_id.job_id.name):
    #                     employee = rec.employee_id.parent_id.parent_id
    #                     if not approval.search([('travel_id', '=', rec.id), ('employee_id', '=', employee.id)]):
    #                         approval.create({
    #                             'travel_id': rec.id,
    #                             'seq': seq,
    #                             'employee_id': employee.id,
    #                             'job_id': employee.job_id.id,
    #                         })
    #                         seq += 1
    #
    #                 if rec.travel_type_id:
    #                     if rec.travel_type_id.manager_id and rec.category == 'business':
    #                         department_ids = self.env['hr.department'].search(
    #                             [('parent_id', 'child_of', rec.travel_type_id.manager_id.department_id.id)])
    #                         if rec.department_id.id in department_ids.ids:
    #                             employee = rec.travel_type_id.manager_id
    #                             if not approval.search([('travel_id', '=', rec.id), ('employee_id', '=', employee.id)]):
    #                                 approval.create({
    #                                     'travel_id': rec.id,
    #                                     'seq': seq,
    #                                     'employee_id': employee.id,
    #                                     'job_id': employee.job_id.id,
    #                                 })
    #                                 seq += 1
    #                     else:
    #                         for line in rec.travel_type_id.approver_ids:
    #                             employee = line.employee_id
    #                             if not approval.search([('travel_id', '=', rec.id), ('employee_id', '=', employee.id)]):
    #                                 approval.create({
    #                                     'travel_id': rec.id,
    #                                     'seq': seq,
    #                                     'employee_id': employee.id,
    #                                     'job_id': employee.job_id.id,
    #                                 })
    #                                 seq += 1
    #
    # def action_done(self):
    #     for rec in self:
    #         if rec.state == 'issued':
    #             rec.state = 'done'
    #         rec.claim_ids.unlink()

    # def action_submit_claim(self):
    #     for rec in self:
    #         if not rec.claim_ids:
    #             raise Warning('There is no claim in this request')
    #         if rec.state == 'issued':
    #             rec.state = 'claimed'

    # def return_true(self):
    #     return True
    #
    # @api.depends('ticket_ids', 'accom_ids', 'transport_ids')
    # def _check_request(self):
    #     for rec in self:
    #         rec.issued = False
    #         if rec.state not in ['claimed', 'issued', 'done']:
    #             if rec.ticket_pesawat:
    #                 if rec.ticket_ids:
    #                     rec.state = 'issued'
    #                     rec.issued = False
    #             if rec.akomodasi:
    #                 if rec.accom_ids:
    #                     rec.state = 'issued'
    #                     rec.issued = False
    #             if rec.transport:
    #                 if rec.transport_ids:
    #                     rec.state = 'issued'
    #                     rec.issued = False
    #
    #             # if rec.category == 'business':
    #             #     if rec.self_ticket:
    #             #         if rec.accom_ids and rec.transport_ids:
    #             #             rec.state = 'issued'
    #             #             rec.issued = False
    #             #     else:
    #             #         if rec.accom_ids and rec.ticket_ids and rec.transport_ids:
    #             #             rec.state = 'issued'
    #             #             rec.issued = False
    #
    #             # else:
    #             #     if rec.self_ticket:
    #             #         if rec.transport_ids:
    #             #             rec.state = 'issued'
    #             #             rec.issued = False
    #             #     else:
    #             #         if rec.ticket_ids and rec.transport_ids:
    #             #             rec.state = 'issued'
    #             #             rec.issued = False
    #
    # def count_traveller(self):
    #     for rec in self:
    #         rec.traveller_no = len(rec.employee_traveller_ids) + len(rec.non_employee_traveller_ids)
    #
    # def check_travel_info(self):
    #     for rec in self:
    #         rec.has_info = False
    #         rec.has_claim = False
    #         if rec.ticket_ids or rec.accom_ids or rec.transport_ids:
    #             rec.has_info = True
    #         if rec.claim_ids:
    #             rec.has_claim = True
    #
    # def set_to_draft(self):
    #     for rec in self:
    #         rec.state = 'draft'
    #
    # def check_is_user(self):
    #     for rec in self:
    #         employee_id = self.env.user.employee_id
    #         approval_ids = self.env['travel.approval'].sudo().search(
    #             [('travel_id', '=', rec.id), ('state', '=', 'waiting')], order='seq asc', limit=1)
    #         rec.is_approver = approval_ids.employee_id == employee_id
    #         if self.user_has_groups('cni_travel_request.super_approver'):
    #             rec.is_approver = True
    #         # rec.is_approver = rec.manager_id == employee_id
    #         rec.is_creator = rec.user_id == self.env.user
    #         # rec.is_final_approver = rec.route_id.final_approver == employee_id.job_id
    #         rec.is_ticket_pic = rec.route_id.flight_ticket_pic == employee_id
    #         rec.is_accom_pic = rec.route_id.accom_pic == employee_id
    #         rec.is_transport_pic = rec.route_id.local_transport_pic == employee_id
    #
    #         # if self.user_has_groups('cni_travel_request.travel_hc_approval'):
    #         #     rec.is_hc_approver = True
    #         travel_cost_control_id = self.env.ref('cni_travel_request.travel_cost_control').id
    #         travel_cost_control = self.env['res.groups'].browse(travel_cost_control_id).users
    #         rec.is_cost_control_approver = self.env.user.id in travel_cost_control.ids
    #
    #         travel_hc_approval_id = self.env.ref('cni_travel_request.travel_hc_approval').id
    #         travel_hc_approval = self.env['res.groups'].browse(travel_hc_approval_id).users
    #         rec.is_hc_approver = self.env.user.id in travel_hc_approval.ids
    #
    # @api.depends('approval_ids')
    # def check_is_final_approver(self):
    #     """access button final approver"""
    #     for rec in self:
    #         employee_id = self.env.user.employee_id
    #         rec.is_final_approver = False
    #         approval_ids = self.env['travel.approval'].sudo().search(
    #             [('travel_id', '=', rec.id), ('state', '=', 'waiting')], order='seq asc', limit=1)
    #         for line in approval_ids.filtered(lambda l: l.job_id.id == employee_id.job_id.id):
    #             rec.is_final_approver = True
    #
    # @api.depends('state')
    # def _compute_css(self):
    #     for rec in self:
    #         rec.x_css = ''
    #         if rec.state != 'draft' and not self.env.user.has_group('base.group_erp_manager'):
    #             rec.x_css = """
    #             <style>
    #             .o_form_button_edit {display: none !important}
    #             .o_cp_action_menus{display: none !important}
    #             </style>"""
    #
    # @api.model
    # def search_my_request_filter(self, operator, operand):
    #     if self.env.user.has_group('base.group_erp_manager'):
    #         return []
    #     elif self.env.user.has_group('cni_travel_request.travel_ticket_pic'):
    #         return ['|', ('user_id', '=', self._uid), ('ticket_pesawat', '=', True)]
    #     elif self.env.user.has_group('cni_travel_request.travel_accom_pic'):
    #         return ['|', ('user_id', '=', self._uid), ('akomodasi', '=', True)]
    #     elif self.env.user.has_group('cni_travel_request.travel_transport_pic'):
    #         return ['|', ('user_id', '=', self._uid), ('transport', '=', True)]
    #     return [('user_id', '=', self._uid)]
    #
    # @api.model
    # def search_to_approve_filter(self, operator, operand):
    #     # if not self.env.user.employee_id:
    #     #     return [('id','=',0)]
    #
    #     super_approver = []
    #     for travel in self.search([]):
    #         if self.user_has_groups('cni_travel_request.super_approver'):
    #             super_approver.append(travel.id)
    #
    #     list_approval = []
    #     approval = False
    #     employee_id = self.env.user.employee_id
    #     approval_ids = self.env['travel.approval'].sudo().search(
    #         [('state', '=', 'waiting'), ('employee_id', '=', employee_id.id)], order='seq asc')
    #     for line in approval_ids:
    #         if line.travel_id:
    #             list_approval.append(line.travel_id.id)
    #
    #     cost_control = []
    #     for travel in self.search([('state', '=', 'cost_control')]):
    #         if self.user_has_groups('cni_travel_request.travel_cost_control'):
    #             cost_control.append(travel.id)
    #
    #     # ids1 = []
    #     # travels = self.search([('department_id.manager_id','=',self.env.user.employee_id.id), ('state','in',['claimed','submit'])])
    #     # for travel in travels:
    #     #     ids1.append(travel.id)
    #
    #     hc_approval = []
    #     point_allocation = [allocation.name for allocation in self.env.user.point_allocation_ids]
    #     for travel in self.search(
    #             [('state', '=', 'hc_approval'), ('employee_id.point_allocation', 'in', point_allocation)]):
    #         if self.user_has_groups('cni_travel_request.travel_hc_approval'):
    #             hc_approval.append(travel.id)
    #
    #     ids = super_approver + list_approval + cost_control + hc_approval
    #     print("=" * 50 + "TO APPROVE" + "=" * 50)
    #     print(ids)
    #     return [('id', 'in', ids)]
    #
    # @api.model
    # def search_to_update_filter(self, operator, operand):
    #     if not self.env.user.employee_id:
    #         return [('id', '=', 0)]
    #     return ['|', '|', ('route_id.flight_ticket_pic', '=', self.env.user.employee_id.id), '&',
    #             ('category', '=', 'business'), ('route_id.accom_pic', '=', self.env.user.employee_id.id),
    #             ('route_id.local_transport_pic', '=', self.env.user.employee_id.id)]
    #
    # @api.onchange('add_requester_to_traveller')
    # def onchange_add_requester_to_traveller(self):
    #     if self.add_requester_to_traveller:
    #         employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
    #         if employee_id:
    #             self.employee_traveller_ids = [(0, 0, {
    #                 'employee_id': employee_id.id,
    #                 'job_id': employee_id.job_id.id,
    #                 'department_id': employee_id.department_id.id,
    #             })]
    #
    # @api.model
    # def default_get(self, fields):
    #     res = super(TravelRequest, self).default_get(fields)
    #     # res['create_uid'] = self._uid
    #     self = self.sudo()
    #     if self._uid not in [1, 2]:
    #         employee_id = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
    #         if not employee_id:
    #             raise Warning('Cannot create Travel Request, there is no related employee to this user')
    #         department_id = employee_id.department_id
    #         if employee_id.company_id.name == 'PT. CERIA NUGRAHA INDOTAMA':
    #             while department_id.category_id.tingkatan > 2:
    #                 department_id = department_id.parent_id
    #
    #         # Acces edit department dan karyawan traveller
    #         self_traveller = True
    #         if self.env.user.has_group('cni_travel_request.travel_admin_requester'):
    #             self_traveller = False
    #
    #         res.update({
    #             'employee_traveller_ids': [(0, 0, {
    #                 'employee_id': employee_id.id,
    #                 'job_id': employee_id.job_id.id,
    #                 'department_id': employee_id.department_id.id,
    #             })],
    #             'self_traveller': self_traveller,
    #             'department_id': department_id.id,
    #             'manager_id': department_id.manager_id.id,
    #         })
    #     return res
    #
    # def update_ticket(self):
    #     return {
    #         'name': _('Update Flight Ticket'),
    #         'view_mode': 'form',
    #         'res_model': self._name,
    #         'type': 'ir.actions.act_window',
    #         'res_id': self.id,
    #         'target': 'new',
    #         'context': {'form_view_ref': 'cni_travel_request.travel_request_ticket_form'}
    #     }
    #
    # def update_accom(self):
    #     for rec in self:
    #         accom_ids = []
    #         for line in rec.accom_ids:
    #             accom_ids.append((0, 0, {
    #                 'name': line.name,
    #                 'akomodasi_id': line.akomodasi_id.id,
    #                 'desc': line.desc,
    #                 'attachment_id': line.attachment_id,
    #                 'attachment_name': line.attachment_name,
    #                 'cost': line.cost,
    #                 'contact': line.contact,
    #             }))
    #
    #     return {
    #         'name': _('Update Accomodation'),
    #         'view_mode': 'form',
    #         'res_model': self._name,
    #         'type': 'ir.actions.act_window',
    #         'res_id': self.id,
    #         'target': 'new',
    #         'context': {'form_view_ref': 'cni_travel_request.travel_request_accom_form'}
    #
    #         # 'name': _('Update Accomodation'),
    #         # 'view_mode': 'form',
    #         # 'res_model': 'update.accomodation',
    #         # 'type': 'ir.actions.act_window',
    #         # 'target': 'new',
    #         # 'context': {'default_accom_ids': accom_ids}
    #     }

    # def update_transport(self):
    #     return {
    #         'name': _('Update Local Transport'),
    #         'view_mode': 'form',
    #         'res_model': self._name,
    #         'type': 'ir.actions.act_window',
    #         'res_id': self.id,
    #         'target': 'new',
    #         'context': {'form_view_ref': 'cni_travel_request.travel_request_transport_form'}
    #     }
    #
    # def submit_claim(self):
    #     return {
    #         'name': _('Submit Claim'),
    #         'view_mode': 'form',
    #         'res_model': self._name,
    #         'type': 'ir.actions.act_window',
    #         'res_id': self.id,
    #         'target': 'new',
    #         'context': {'form_view_ref': 'cni_travel_request.travel_submit_claim_form'}
    #     }

    # def write(self, vals):
    #     res = super(TravelRequest, self).write(vals)
    #     # print(vals)
    #     if vals.get('ticket_ids'):
    #         self.action_notif_ticket_traveller()
    #     if vals.get('accom_ids'):
    #         self.action_notif_accom_traveller()
    #     if vals.get('transport_ids'):
    #         self.action_notif_transport_traveller()
    #     return res

    # @api.constrains('ticket_ids','accom_ids','transport_ids')
    # def action_notif_ticket_traveller(self):
    #     for rec in self:
    #         for ticket in rec.ticket_ids:
    #             base_url = self.env['ir.config_parameter'].get_param('web.base.url')
    #             url_attachment = f"{base_url}/web/image?model={ticket._name}&id={ticket.id}&field=attachment_id"
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                 "cni_travel_request.message_wa_travel_ticket")
    #             params_message_wa = params_message_wa.replace("{traveller}", rec.user_id.name)
    #             params_message_wa = params_message_wa.replace("{from}", rec.location_from.name)
    #             params_message_wa = params_message_wa.replace("{to}", rec.location_to.name)
    #             params_message_wa = params_message_wa.replace("{airline}", ticket.airline_id.name)
    #             params_message_wa = params_message_wa.replace("{time}", str(ticket.departure_date))
    #             params_message_wa = params_message_wa.replace("{description}", ticket.desc)
    #             params_message_wa = params_message_wa.replace("{contact}", ticket.contact)
    #             params_message_wa = params_message_wa.replace("{url_attachment}", url_attachment)
    #             params_message_wa = params_message_wa.replace("{travel_no}", rec.name)
    #             message_wa = params_message_wa
    #             notifikasi = self.env['send_message.email'].sudo().create({
    #                 'receiver': rec.user_id.id,
    #                 'template': False,
    #                 'is_send': False,
    #                 'is_send_wa': False,
    #                 'message': message_wa,
    #                 # 'company_id'  : rec.company_id.id,
    #                 'company_id': rec.user_id.company_id.id,
    #                 'id_record': rec.id,
    #                 'ref': rec.name
    #             })

    # def action_notif_accom_traveller(self):
    #     for rec in self:
    #         for akomodasi in rec.accom_ids:
    #             base_url = self.env['ir.config_parameter'].get_param('web.base.url')
    #             url_attachment = f"{base_url}/web/image?model={akomodasi._name}&id={akomodasi.id}&field=attachment_id"
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                 "cni_travel_request.message_wa_travel_akomodasi")
    #             params_message_wa = params_message_wa.replace("{traveller}", rec.user_id.name)
    #             params_message_wa = params_message_wa.replace("{akomodasi}", akomodasi.akomodasi_id.name)
    #             params_message_wa = params_message_wa.replace("{description}", akomodasi.desc)
    #             params_message_wa = params_message_wa.replace("{contact}", akomodasi.contact)
    #             params_message_wa = params_message_wa.replace("{url_attachment}", url_attachment)
    #             params_message_wa = params_message_wa.replace("{travel_no}", rec.name)
    #             message_wa = params_message_wa
    #             notifikasi = self.env['send_message.email'].sudo().create({
    #                 'receiver': rec.user_id.id,
    #                 'template': False,
    #                 'is_send': False,
    #                 'is_send_wa': False,
    #                 'message': message_wa,
    #                 # 'company_id'  : rec.company_id.id,
    #                 'company_id': rec.user_id.company_id.id,
    #                 'id_record': rec.id,
    #                 'ref': rec.name
    #             })

    # def action_notif_transport_traveller(self):
    #     for rec in self:
    #         for transport in rec.transport_ids:
    #             base_url = self.env['ir.config_parameter'].get_param('web.base.url')
    #             url_attachment = f"{base_url}/web/image?model={transport._name}&id={transport.id}&field=attachment_id"
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                 "cni_travel_request.message_wa_travel_transport")
    #             params_message_wa = params_message_wa.replace("{traveller}", rec.user_id.name)
    #             params_message_wa = params_message_wa.replace("{vehicle}", transport.vehicle_id.name)
    #             params_message_wa = params_message_wa.replace("{description}", transport.desc)
    #             params_message_wa = params_message_wa.replace("{driver}", transport.driver)
    #             params_message_wa = params_message_wa.replace("{contact}", transport.contact)
    #             params_message_wa = params_message_wa.replace("{url_attachment}", url_attachment)
    #             params_message_wa = params_message_wa.replace("{travel_no}", rec.name)
    #             message_wa = params_message_wa
    #             notifikasi = self.env['send_message.email'].sudo().create({
    #                 'receiver': rec.user_id.id,
    #                 'template': False,
    #                 'is_send': False,
    #                 'is_send_wa': False,
    #                 'message': message_wa,
    #                 # 'company_id'  : rec.company_id.id,
    #                 'company_id': rec.user_id.company_id.id,
    #                 'id_record': rec.id,
    #                 'ref': rec.name
    #             })

    # def action_send_notifikasi(self, user):
    #     for rec in self:
    #         if self.env.context.get('template_email'):
    #             template = self.env.context.get('template_email')
    #         else:
    #             template = self.env.ref('cni_travel_request.travel_approver_mail_template')
    #
    #         # paramater message wa
    #         if self.env.context.get('template_wa'):
    #             params_message_wa = self.env.context.get('template_wa')
    #         else:
    #             params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                 "cni_travel_request.message_wa_travel_approver")
    #         message_wa_cost_control = params_message_wa.replace("{approver}", user.name)
    #         message_wa_cost_control = message_wa_cost_control.replace("{kode}", rec.name)
    #         message_wa_cost_control = message_wa_cost_control.replace("{requester}", rec.user_id.name)
    #         message_wa_cost_control = message_wa_cost_control.replace("{department}",
    #                                                                   rec.department_id.name if rec.department_id else "-")
    #         message_wa_cost_control = message_wa_cost_control.replace("{link}", rec.link_travel)
    #         message_wa = message_wa_cost_control
    #
    #         travel_hc_approval_id = self.env.ref('cni_travel_request.travel_hc_approval')
    #
    #         is_send = False
    #         if user.id in travel_hc_approval_id.users.ids:
    #             is_send = True
    #
    #         notifikasi = self.env['send_message.email'].sudo().create({
    #             'receiver': user.id,
    #             'template': template.id,
    #             'is_send': is_send,
    #             'is_send_wa': False,
    #             'message': message_wa,
    #             # 'company_id'  : rec.company_id.id,
    #             'company_id': user.company_id.id,
    #             'id_record': rec.id,
    #             'ref': rec.name
    #         })

    # def button_final_approve(self):
    #     for rec in self:
    #         if self.user_has_groups('cni_travel_request.super_approver'):
    #             for approval in self.env['travel.approval'].sudo().search(
    #                     [('travel_id', '=', rec.id), ('state', '=', 'waiting')]):
    #                 approval.write({'state': 'approved'})
    #             return 0
    #         else:
    #             employee_id = self.env.user.employee_id
    #             approval = self.env['travel.approval'].sudo().search(
    #                 [('travel_id', '=', rec.id), ('state', '=', 'waiting')], order='seq asc', limit=1)
    #             if employee_id.job_id.id in approval.job_id.ids:
    #                 approval.write({'state': 'approved'})
    #
    #             nik = self.env.context.get('nik')
    #             if nik:
    #                 context_employee = self.env['hr.employee'].search([('nip', '=', nik)])
    #                 if context_employee.job_id.id in approval.job_id.ids:
    #                     approval.write({'state': 'approved'})
    #
    #             self._cr.commit()
    #
    #             next_approval = self.env['travel.approval'].sudo().search(
    #                 [('travel_id', '=', rec.id), ('state', '=', 'waiting')], order='seq asc', limit=1)
    #             if next_approval:
    #                 rec.action_send_notifikasi(next_approval.employee_id.user_id)
    #
    #             approvals = self.env['travel.approval'].sudo().search(
    #                 [('travel_id', '=', rec.id), ('state', '=', 'waiting')])
    #             if not approvals:
    #                 return 0
    #             return 1

    def action_approve(self):
        for rec in self:
            state_before = rec.state
            super(TravelRequest,rec).action_approve()
            if state_before == 'cost_control':
                self.env['approval.audit.log'].create_audit_log(
                    transaction_id=rec.id,
                    transaction_model_name=self._name,
                    user_id=self.env.uid,
                    name='Approval Cost Control',
                    action_type='approve',
                    create_date=fields.Datetime.now(),
                )
            elif state_before == 'hc_approval':
                self.env['approval.audit.log'].create_audit_log(
                    transaction_id=rec.id,
                    transaction_model_name=self._name,
                    user_id=self.env.uid,
                    name='Approval HC',
                    action_type='approve',
                    create_date=fields.Datetime.now(),
                )

            if rec.state in ['submit','cost_control','hc_approval']:
                # setelah approval bila masih dalam kodisi approval update register approval
                rec.register_approval_task()


    # def action_approve(self):
    #     for rec in self:
    #         state = rec.state
    #         if rec.state == 'draft':
    #             if rec.cash_advance == True:
    #                 if not rec.lampiran_formulir or not rec.lampiran_surat:
    #                     raise Warning(
    #                         'Anda wajib melampirkan surat tugas dan formulir perjalanan dinas untuk dapat mengajukan uang muka')
    #             state = 'submit'
    #             if not rec.ticket_pesawat and not rec.akomodasi and not rec.transport:
    #                 raise Warning('Anda wajib memilih salah satu kebutuhan travel')
    #
    #             if rec.leave_request_id:
    #                 state = 'hc_approval'
    #             else:
    #                 # SEND WA TO LIST APPROVER
    #                 approval = self.env['travel.approval'].sudo().search(
    #                     [('travel_id', '=', rec.id), ('state', '=', 'waiting')], order='seq asc', limit=1)
    #                 rec.action_send_notifikasi(approval.employee_id.user_id)
    #         elif rec.state == 'submit':
    #             res = rec.with_context(nik=self.env.context.get('nik')).button_final_approve()
    #             if res == 0:
    #                 if rec.cash_advance == True:
    #                     state = 'cost_control'
    #
    #                     # SEND WA TO PIC HC
    #                     travel_cost_control_id = self.env.ref('cni_travel_request.travel_cost_control').id
    #                     for user in self.env['res.groups'].browse(travel_cost_control_id).users:
    #                         params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                             "cni_travel_request.message_wa_travel_approver_cost_control")
    #                         template = self.env.ref('cni_travel_request.travel_approver_mail_template_cost_control')
    #                         rec.with_context(template_wa=params_message_wa,
    #                                          template_email=template).action_send_notifikasi(user)
    #                 else:
    #                     state = 'hc_approval'
    #
    #                     # SEND WA TO PIC HC
    #                     travel_hc_approval_id = self.env.ref('cni_travel_request.travel_hc_approval').id
    #                     for user in self.env['res.groups'].browse(travel_hc_approval_id).users:
    #                         rec.action_send_notifikasi(user)
    #         elif rec.state == 'cost_control':
    #             state = 'hc_approval'
    #
    #             # SEND WA TO PIC HC
    #             travel_hc_approval_id = self.env.ref('cni_travel_request.travel_hc_approval').id
    #             for user in self.env['res.groups'].browse(travel_hc_approval_id).users:
    #                 rec.action_send_notifikasi(user)
    #         elif rec.state == 'hc_approval':
    #             state = 'approve_hrga'
    #
    #             # SEND WA TO PIC Ticket
    #             travel_ticket_pic_id = self.env.ref('cni_travel_request.travel_ticket_pic').id
    #             for user in self.env['res.groups'].browse(travel_ticket_pic_id).users:
    #                 # if rec.ticket_pesawat and rec.company_id in user.company_ids.ids:
    #                 if rec.ticket_pesawat:
    #                     params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                         "cni_travel_request.message_wa_travel_approver_ticket")
    #                     template = self.env.ref('cni_travel_request.travel_approver_mail_template_ticket')
    #                     rec.with_context(template_wa=params_message_wa, template_email=template).action_send_notifikasi(
    #                         user)
    #
    #             # SEND WA TO PIC Accomodation
    #             travel_accom_pic_id = self.env.ref('cni_travel_request.travel_accom_pic').id
    #             for user in self.env['res.groups'].browse(travel_accom_pic_id).users:
    #                 # if rec.akomodasi and rec.company_id in user.company_ids.ids:
    #                 if rec.akomodasi:
    #                     params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                         "cni_travel_request.message_wa_travel_approver_accom")
    #                     template = self.env.ref('cni_travel_request.travel_approver_mail_template_accom')
    #                     rec.with_context(template_wa=params_message_wa, template_email=template).action_send_notifikasi(
    #                         user)
    #
    #             # SEND WA TO PIC Transport
    #             travel_transport_pic_id = self.env.ref('cni_travel_request.travel_transport_pic').id
    #             for user in self.env['res.groups'].browse(travel_transport_pic_id).users:
    #                 # if rec.transport and rec.company_id in user.company_ids.ids:
    #                 if rec.transport:
    #                     params_message_wa = self.env["ir.config_parameter"].sudo().get_param(
    #                         "cni_travel_request.message_wa_travel_approver_transport")
    #                     template = self.env.ref('cni_travel_request.travel_approver_mail_template_transport')
    #                     rec.with_context(template_wa=params_message_wa, template_email=template).action_send_notifikasi(
    #                         user)
    #
    #         elif rec.state == 'claimed':
    #             state = 'done'
    #
    #         rec.write({'state': state})

    # def action_reject(self):
    #     context = self.env.context.copy()
    #     return {
    #         'name': _('Reject'),
    #         'view_mode': 'form',
    #         'res_model': 'reject.wizard',
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #         'context': context,
    #     }

    # def approve_department(self):
    #     for rec in self:
    #         # rec.write({'state': 'wait_hrga'})
    #         if rec.env.user.employee_ids.job_id == rec.dept_manager_job_id:
    #             rec.write({'state': 'wait_hrga'})
    #         else:
    #             raise AccessDenied(("You can't do this action."))

    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('travel.request')
    #     result = super(TravelRequest, self).create(vals)
    #     if result.leave_request_id:
    #         if result.pulang:
    #             result.leave_request_id.write({'travel_pulang': True})
    #         elif result.berangkat:
    #             result.leave_request_id.write({'travel_berangkat': True})
    #     return result

    # @api.onchange('route_id')
    # @api.constrains('route_id')
    # def _onchange_route_id(self):
    #     for rec in self:
    #         rec.approval_ids = False
    #         approval = []
    #         if rec.route_id:
    #             for approver in rec.route_id.final_approver_ids:
    #                 approval.append((0,0, {
    #                   'seq': approver.seq,
    #                   'job_id': approver.job_id.id
    #                 }))
    #             rec.approval_ids = approval

    # @api.constrains('state')
    # def _onchange_accom(self):
    #     for rec in self:
    #         if rec.state == 'done':
    #             for accom in rec.accom_ids:
    #                 accom.akomodasi_id.available = True
    #
    # @api.onchange('leave_request_id', 'pulang', 'berangkat')
    # def _onchange_leave_request(self):
    #     for rec in self:
    #         if rec.leave_request_id:
    #             rec.category = "fb"
    #         if rec.pulang:
    #             rec.location_from = rec.leave_request_id.location_from_id.id
    #             rec.location_to = rec.leave_request_id.location_to_id.id
    #         elif rec.berangkat:
    #             rec.location_to = rec.leave_request_id.location_from_id.id
    #             rec.location_from = rec.leave_request_id.location_to_id.id

    # def write(self, vals):
    #     result = super(TravelRequest, self).write(vals)
    #     for rec in self:
    #         if rec.leave_request_id:
    #             if rec.pulang:
    #                 rec.leave_request_id.write({'travel_pulang': True})
    #             elif rec.berangkat:
    #                 rec.leave_request_id.write({'travel_berangkat': True})
    #
    #     return result

    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'draft':
    #             raise ValidationError(_("Cannot delete. Only delete in state Draft"))
    #         if rec.leave_request_id:
    #             if rec.pulang == True:
    #                 rec.leave_request_id.write({
    #                     'travel_pulang': False
    #                 })
    #
    #             if rec.berangkat == True:
    #                 rec.leave_request_id.write({
    #                     'travel_berangkat': False
    #                 })
    #     result = super(TravelRequest, self).unlink()
    #     action = {
    #         'type': 'ir.actions.act_url',
    #         'name': 'Travel Request',
    #         'target': 'self',
    #         'url': '/web#action=%s&model=travel.request&view_type=list&cids=&menu_id=%s' % (
    #         self.env.ref('cni_travel_request.travel_request_action').id,
    #         self.env.ref('cni_travel_request.travel_management_root_menu').id)
    #     }
    #
    #     return action

    # @api.depends('employee_id')
    # def _compute_dynamic_approver(self):
    #     for rec in self:
    #         rec.dynamic_approver = False
    #         groups = self.env.ref('cni_travel_request.dynamic_travel_approvers')
    #         if rec.employee_id:
    #             if self.env.user.id in groups.users.ids:
    #                 rec.dynamic_approver = True

