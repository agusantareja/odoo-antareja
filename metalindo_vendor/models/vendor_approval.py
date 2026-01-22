from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import datetime
from odoo.exceptions import UserError, AccessError, ValidationError


class VendorAction(models.Model):
    _name = 'vendor.action'
    _description = 'Vendor Action'
    _inherit = ['mail.thread']
    _check_company_auto = True

    vendor_id = fields.Many2one('res.partner', string='Vendor ID')            
    state_action = fields.Selection([
        ('blackwait','Waiting For Blacklist'),
        ('blacklist', 'Blacklist'),
        ('whitewait','Waiting For Whitelist'),
        ('whitelist', 'Whitelist'),
        ('changewait', 'Waiting for Change'),
    ], string='Action Status')
    action_list = fields.Selection([
        ('request', 'Request Approve'),
        ('approve','Approve'),
        ('reject', 'Reject Approve'),
        ('cancel', 'Cancel Approve'),
        ('blackreq', 'Request Blacklist'),
        ('blacklist', 'Approve Blacklist'),
        ('blackreject', 'Reject Blacklist'),
        ('blackcancel', 'Cancel Blacklist'),
        ('whitereq', 'Request Whitelist'),
        ('whitelist', 'Approve Whitelist'),
        ('whitereject', 'Reject Whitelist'),
        ('whitecancel', 'Cancel Whitelist'),
        ('changereq', 'Request Change'),
        ('change', 'Approve Change'),
        ('changereject', 'Reject Change'),
    ], string='Action', tracking=True)
    action_by = fields.Many2one('res.users', string="Action By")
    action_date = fields.Datetime(string="Action Date")
    reason = fields.Text(string="Reason")
    changelist = fields.Text(string="Change")

    def button_approve(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            if not self.code_id and self.is_company:
                raise UserError(_("Location harus diisi."))
                return False
            self.write({
                'state': 'approved',
                'approve_by': self.env.uid,
                'approve_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menyetujui vendor ini."))
        return True
    
    def button_reject(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            self.write({
                'state': 'reject',
                'reject_by': self.env.uid,
                'reject_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menolak vendor ini."))
        return True
    
    def button_cancel(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            self.write({
                'state': 'waiting',
                'state_action': False,
                'cancel_by': self.env.uid,
                'cancel_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak membatalkan vendor ini."))
        return True

    def button_request_blacklist(self):
        
        # self.write({
        #     'state_action': 'blackwait',
        #     'request_blacklist_by': self.env.uid,
        #     'request_blacklist_date': datetime.now(),
        #     })
        action = self.env.ref('metalindo_approval.cni_vendor_blacklist_wizard_action').read()[0]
        action.update({
            'context' : {'default_vendor_id': self.id},
        })
        return action

    def button_blacklist(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            self.write({
                'state': 'blacklist',
                'state_action': False,
                'blacklist_by': self.env.uid,
                'blacklist_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak mem-blacklist vendor ini."))
        return True

    def button_reject_blacklist(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            self.write({
                'state_action': False,
                'reject_blacklist_by': self.env.uid,
                'reject_blacklist_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menolak blacklist vendor ini."))
        return True

    def button_request_whitelist(self):
        # self.write({
        #     'state_action': 'whitewait',
        #     'request_whitelist_by': self.env.uid,
        #     'request_whitelist_date': datetime.now(),
        #     })
        action = self.env.ref('metalindo_approval.cni_vendor_whitelist_wizard_action').read()[0]
        action.update({
            'context' : {'default_vendor_id': self.id},
        })
        return action

    def button_whitelist(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            self.write({
                'state': 'approved',
                'state_action': False,
                'whitelist_by': self.env.uid,
                'whitelist_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak me-whitelist vendor ini."))
        return True

    def button_reject_whitelist(self):
        if self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            self.write({
                'state': 'blacklist',
                'state_action': False,
                'reject_whitelist_by': self.env.uid,
                'reject_whitelist_date': datetime.now(),
                })
        else:
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menolak whitelist vendor ini."))
        return True

    def write(self, vals):
        # import pdb;pdb.set_trace()
        if vals.get('active') is False and self.state == 'approved' and not self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menon-aktifkan vendor ini."))
        else:
            res = super(CniVendorApproval, self).write(vals)
        return res

    def unlink(self):
        # import pdb;pdb.set_trace()
        if self.state == 'approved' and not self.env.user.has_group('metalindo_vendor.group_metalindo_vendor_approval'):
            raise UserError(_("Anda tidak termasuk dalam grup Vendor Approval. Anda tidak berhak menghapus vendor ini."))
        else:
            res = super(CniVendorApproval, self).unlink()
        return res