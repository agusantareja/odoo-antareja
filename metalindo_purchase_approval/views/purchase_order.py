# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

REVISION_NAME_TEMPLATE = 'Rev %i'


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(selection_add=[('revision','In Revision'), ('waiting_revision','Waiting Revision Approval')])
    revision_reason = fields.Text('Revision Reason', copy=False)
    previous_revision_reason = fields.Text('Previous Revision Reason')
    previous_amount = fields.Float('Amount Total Before Revision')
    revision_count = fields.Integer('Revision Count', copy=False)
    no_revision = fields.Boolean(compute='_compute_no_revision')
    revision_line_ids = fields.One2many('purchase.order.line', 'order_id', string='Revision Lines', 
        compute='_compute_revision_line_ids', inverse='_inverse_revision_line_ids',)
    rev_history_ids = fields.One2many('po.version','order_id','Revision History')
    revision_ribbon_html = fields.Html(compute="_compute_revision_ribbon_html")

    def _compute_revision_line_ids(self):
        for rec in self:
            rec.revision_line_ids = rec.order_line

    def _inverse_revision_line_ids(self):
        for rec in self:
            rec.order_line = rec.revision_line_ids

    def _compute_no_revision(self):
        for rec in self:
            list_gr_done = []
            for line in rec.order_line:
                move = self.env['stock.move'].sudo().search([
                    ('purchase_line_id', '=', line.id),
                    ('picking_id.picking_type_id', '=', line.order_id.picking_type_id.id)])
                if 'done' in move.mapped('state'):
                    list_gr_done.append(True)
                else:
                    list_gr_done.append(False)

            rec.no_revision = all(list_gr_done)
            # # PO tidak bisa revisi jika barang sudah diterima
            # for move in self.env['stock.move'].sudo().search([('purchase_line_id', 'in', [l.id for l in rec.order_line])]):
            #     if move.picking_id.state == 'done':
            #         rec.no_revision = True
            #         break
            # else:
            #     rec.no_revision = False

    @api.depends('revision_count')
    def _compute_revision_ribbon_html(self):
        for rec in self:
            rec.revision_ribbon_html = f"""
                <span class="bg-warning" title="">
                    Rev {rec.revision_count}
                </span>
            """

    # Override the default value for po_report_filename
    def generate_po_slip(self, po_report_filename=None):
        self.ensure_one()
        if not po_report_filename:
            po_report_filename = f"Purchase Order %s {REVISION_NAME_TEMPLATE}.pdf" % (self.name, self.revision_count)
        return super().generate_po_slip(po_report_filename)

    # Stop resetting reports upon changing to 'purchase' state, since we don't want to reset them
    # just because we cancelled a revision request.
    def _delete_attachment(self):
        pass

    # Override button_approve_approval() to do additional housekeeping
    # def button_approve_approval(self):
    #     approval_sts = super().button_approve_approval()
    #     if approval_sts == 0:

    def event_approval_done(self, **kwargs):
        order = self.ensure_one()
        last_state = order.state
        super().event_approval_done(**kwargs)
        if last_state == 'waiting_revision':
            if kwargs.get('is_approved'):
                # Remove previous versions of PO and vendor acknowledgement
                self.env['ir.attachment'].search([
                    ('res_id', '=', self.id),
                    ('res_model', '=', self._name),
                    ('res_field', '=', False),
                    '|',
                    # Using str() here to prevent a `TypeError` when self.po_report_filename is `False`
                    # (i.e., not set). No files should have a name ending with "False", so this should
                    # not cause accidental deletion of important attachments.
                    ('name', '=like', '%' + str(self.po_report_filename)),
                    # Using str() here to prevent a `TypeError` when self.vendor_acknowledge_report_filename
                    # is `False` (i.e., not set). No files should have a name ending with "False", so
                    # this should not cause accidental deletion of important attachments.
                    ('name', '=like', '%' + str(self.vendor_acknowledge_report_filename)),
                ]).unlink()
                self.write({
                    'po_report': False,
                    'po_report_filename': False,
                    'vendor_acknowledge_report': False,
                    'vendor_acknowledge_report_filename': False,
                    'print_po_date': False,
                })
            elif kwargs.get('is_rejected'):
                self.write({
                    'state':'revision'
                })


    def notifikasi_diganti_dengan_cara_baru(self, **kwargs):
        if kwargs.get('is_approved'):
            # Send PO revision notification to all users that have previously approved this PO (only
            # needed when `amount_total` <= `previous_amount`, where only Procurement Engineer
            # approval is needed).
            if self.amount_total <= self.previous_amount:
                email = self.env['send_message.email']
                template = self.env.ref('metalindo_purchase_revision.mail_template_revision_notification')
                message_wa_template = self.env['ir.config_parameter'].sudo().get_param('metalindo_purchase_revision.param_message_wa_revision_notification')
                link = self.link if self.link else '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
                    self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                    self.id,
                    self._name,
                    self.company_id.id,
                    self.env.ref('purchase.menu_purchase_root').id
                )
                sent_users = self.env['res.users']
                for user in self.rev_history_ids.approval_ids.pelaksana_id:
                    if user not in sent_users:
                        message_wa = message_wa_template.replace(
                            "{approver}", user.name
                        ).replace(
                            "{no_po}", self.name
                        ).replace(
                            "{no_revisi_po}", str(self.revision_count)
                        ).replace(
                            "{link}", link
                        )
                        email.create({
                            'receiver'    : user.id,
                            'template'    : template.id,
                            'is_send'     : False,
                            'is_send_wa'  : False,
                            'message'     : message_wa,
                            'company_id'  : self.company_id.id,
                            'model_record': self._name,
                            'id_record'   : self.id,
                            'ref'         : self.name
                        })
                        sent_users += user
        # return approval_sts

    def button_reject_approval(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "metalindo_approval.cni_reject_approval_wizard_action"
        )
        # Reject to PO state 'revision' if this is a revision approval
        if self.revision_count > 0:
            updated_context = {'update_value': self.env.context['update_value']}
            updated_context['update_value']['state'] = 'revision'
            action['context'] = str(updated_context)
        return action

    def button_request_revision(self):
        if self.no_revision:
            raise ValidationError('Revisions are not allowed because the items have already been received')
        view = self.env.ref('metalindo_purchase_revision.request_revision_form')
        return {
            'name': _('Request for Revision'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'request.revision',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, default_purchase_id=self.id),
        }

    def button_approve_revision(self):
        current_pdf = self.po_report
        if not current_pdf:
            self.generate_po_slip()

        attachment_id = self.env['ir.attachment'].sudo().search([
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('res_field', '=', 'po_report'),
            ('name', '=', 'po_report'),
        ])
        rev_history_id = self.env['po.version'].create({
            'name': REVISION_NAME_TEMPLATE % self.revision_count,
            'po_pdf_filename': self.po_report_filename,
            'order_id': self.id,
            'amount': self.amount_total,
            'currency_id': self.currency_id.id,
            'reason': self.previous_revision_reason,
            'approval_ids': self.approval_ids,
        })
        if attachment_id:
            attachment_id.write({
                'res_id': rev_history_id.id,
                'res_model': 'po.version',
                'res_field': 'po_pdf',
                'name': 'po_pdf',
            })
        self.write({
            'state': 'revision', 
            'revision_count': self.revision_count + 1,
            'previous_amount': self.amount_total,
            'previous_revision_reason': False,
            'flag_reject': False,
        })

    def button_reject_revision(self):
        view = self.env.ref('metalindo_purchase_revision.reject_revision_form')
        return {
            'name': _('Reject Revision'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'reject.revision',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': dict(self.env.context, default_purchase_id=self.id),
        }


    def button_confirm_revision(self):
        if self.previous_amount < self.amount_total:
            self.button_submit()
            # definisi fungsi waiting_approval ada di system parameter
            # waiting_approval_method = self.env['ir.config_parameter'].sudo().get_param('metalindo_purchase_revision.waiting_approval_method')
            # if waiting_approval_method:
                # eval_context = {'model': self}
                # result = safe_eval(waiting_approval_method.strip(), eval_context, mode='exec', nocopy=True)
            
            # else:
                # raise ValidationError('Konfigurasi "Waiting Approval Method" harus diisi')
        else:
            # Approval cukup sampai Superintendent Procurement saja
            self.write({
                'state': 'waiting_for_approval',
                'approval_state': 'rf',
                'flag_reject': False,
            })
            for line in self.order_line:
                line.mr_id.write({
                    'mr_status': 'purchased'
                })
            self.approval_ids = False
            self.env['cni.matrix.approval.line'].request_by_value(self, 0, self.currency_id, 'purchase order', self.user_id.id)

            param = self.env['ir.config_parameter'].sudo().get_param('metalindo_approval.param_message_approval_purchase_order')
            approver = self.env['cni.approval.transaction'].sudo().search([('transaction_id', '=', self.id), ('sts', 'in', ['1', '3']), ('view_name', '=', 'purchase order')], limit=1, order='seq asc')
            link = self.link if self.link else '%s/web#id=%s&model=%s&view_type=form&cids=%s&menu_id=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                self.id,
                self._name,
                self.company_id.id,
                self.env.ref('purchase.menu_purchase_root').id
            )
            email = self.env['send_message.email']
            template = self.env.ref('metalindo_approval.purchase_approver_mail_template')
            if approver:
                for user in approver.group_id.users:
                    message_wa = param.replace("{approver}", user.name).replace("{no_po}", self.name).replace("{link}", link)
                    email.create({
                        'receiver'    : user.id,
                        'template'    : template.id,
                        'is_send'     : False,
                        'is_send_wa'  : False,
                        'message'     : message_wa,
                        'company_id'  : self.company_id.id,
                        'model_record': self._name,
                        'id_record'   : self.id,
                        'ref'         : self.name
                    })

    def _create_picking(self):
        StockPicking = self.env['stock.picking']
        for order in self.filtered(lambda po: po.state in ('purchase', 'done')):
            if any(product.type in ['product', 'consu'] for product in order.order_line.product_id):
                order = order.with_company(order.company_id)
                # pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel')) original code
                pickings = order.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel')\
                    and x.picking_type_id == order.picking_type_id)

                if not pickings:
                    res = order._prepare_picking()
                    picking = StockPicking.with_user(SUPERUSER_ID).create(res)
                    pickings = picking
                else:
                    picking = pickings[0]
                moves = order.order_line._create_stock_moves(picking)
                # moves = moves.filtered(lambda x: x.state not in ('done', 'cancel'))._action_confirm() original code
                moves = moves.filtered(lambda x: x.state not in ('done', 'cancel')\
                    and x.picking_id.picking_type_id == order.picking_type_id)._action_confirm()
                seq = 0
                for move in sorted(moves, key=lambda move: move.date):
                    seq += 5
                    move.sequence = seq
                moves._action_assign()
                # Get following pickings (created by push rules) to confirm them as well.
                forward_pickings = self.env['stock.picking']._get_impacted_pickings(moves)
                (pickings | forward_pickings).action_confirm()
                picking.message_post_with_view('mail.message_origin_link',
                    values={'self': picking, 'origin': order},
                    subtype_id=self.env.ref('mail.mt_note').id)
        return True


class po_version(models.Model):
    _name = 'po.version'
    _description = 'PO Version'

    name = fields.Char('Version')
    po_pdf = fields.Binary('PO Slip', attachment=True)
    order_id = fields.Many2one('purchase.order', 'Purchase Order')
    po_pdf_filename = fields.Char('PO Slip Filename')
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one(comodel_name='res.currency')
    reason = fields.Text('Reason')
    approval_ids = fields.One2many(comodel_name='cni.approval.transaction', inverse_name='po_version_id')
    # Helper field to show `approval_ids` tersely on a list view
    approved_by = fields.Char(compute='_compute_approved_by')

    @api.depends('approval_ids.pelaksana_id')
    def _compute_approved_by(self):
        for rec in self:
            # Manually looping through each approver's name to avoid duplicates while also
            # preserving the order of approvals
            approver_names = []
            for approver in rec.approval_ids.pelaksana_id:
                if approver.name not in approver_names:
                    approver_names.append(approver.name)
            rec.approved_by = ', '.join(approver_names)
