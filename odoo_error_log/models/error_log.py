from odoo import models, fields, api
from odoo.http import request


class ErrorLog(models.Model):
    _name = 'error.log'
    _description = 'Error Log'

    name = fields.Char(string="Name")
    message = fields.Text(string="Message")
    traceback = fields.Html(string="Traceback")
    db_name = fields.Char(string="Database Name")
    user_id = fields.Many2one('res.users', string="User")
    user_name = fields.Char(string="User Name")
    user_ip = fields.Char(string="User IP")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company)
    date_time = fields.Datetime(string="Login Date And Time", default=lambda self: fields.datetime.now())
    email_sent = fields.Boolean(string="Email Sent", default=False)  # 跟踪邮件是否已发送

    @api.model
    def get_error_info(self):
        """获取当前会话的用户信息和数据库名称"""
        user_id = False
        user_name = "Unknown"
        db_name = "Unknown"
        user_ip = "Unknown"
        try:
            user_id = request.env.user.id
            user_name = request.env.user.name
            db_name = request.env.cr.dbname
            user_ip = request.httprequest.environ.get('HTTP_X_REAL_IP', '') + " --- " + request.httprequest.environ['REMOTE_ADDR']
        except Exception as e:
            pass

        return {
            'db_name': db_name,
            'user_id': user_id,
            'user_name': user_name,
            'user_ip': user_ip
        }

    @api.model
    def create_and_send_email(self, error_data):
        """创建错误记录并发送邮件通知"""
        # 创建错误日志
        error_info = self.get_error_info()
        error_data.update(error_info)
        if 'traceback' in error_data:
            error_data['traceback'] = error_data['traceback'].replace('\n', '<br>').replace(' ', '&nbsp;')
        error_log = self.create(error_data)
        
        # 如果邮件尚未发送，发送邮件
        if not error_log.email_sent:
            self.send_error_email(error_log)
        return error_log

    def send_error_email(self, error_log):
        error_log = error_log.sudo()
        """发送错误邮件"""
        body = f"""
<p style="text-align:center">A new error occurred in Odoo instance.</p>
<p>User Name: {error_log.user_name}</p>
<p>Database: {error_log.db_name}</p>
<p>IP Address: {error_log.user_ip}</p>
<p>Error Message: {error_log.message}</p>
<p>Traceback: {error_log.traceback}</p>
        """
        mail_server = self.env['ir.mail_server'].sudo().search([], limit=1)
        email_to = self.env['ir.config_parameter'].sudo().get_param('odoo_error_log.notice_email')
        if not mail_server or not mail_server.smtp_user or not email_to:
            return
        companys= error_log.company_id.name if error_log.company_id else ' '
        mail = self.env['mail.mail'].sudo().create({
            'body_html': body,
            'email_from': f'"{companys}" <{mail_server.smtp_user}>',
            'email_to': email_to,
            'subject': f"{error_log.name}-{error_log.user_name}",
        })
        mail.send()
        error_log.write({'email_sent': True})
