from odoo import models, fields, api

# nip aslinya di definisikan di cni_employee_intra
# Tapi untuk menghindari cycle dependency di modul tersebut maka definisi nip di lakukan di sini
# maka
class HREmployee(models.Model):
    _inherit = 'hr.employee'

    nip = fields.Char()

class SnipeUser(models.Model):
    _name = "snipe.user"
    _description = "User from Snipe-IT"

    name = fields.Char(required=True)
    email = fields.Char()
    username = fields.Char()
    employee_num = fields.Char(
        string="Employee Number",
        help="employee_num akan berelasi dengan  hr.employee nip saat penarikan data"
    )
    employee_id = fields.Many2one("hr.employee", string="Mapped Employee")
    snipe_hardware_ids = fields.One2many(
        'snipe.hardware',
        'assigned_to_id'
    )
    def _map_employee_by_num(self, vals):
        """
        Utility function untuk mencari employee berdasarkan employee_num (nip)
        dan menambahkan ke dalam vals["employee_id"]
        """
        employee_num = vals.get("employee_num")
        if employee_num:
            employee = self.env["hr.employee"].search([("nip", "=", employee_num)], limit=1)
            if employee:
                vals["employee_id"] = employee.id
        return vals
    def search_or_create(self,assigned):
        employee_num = assigned.get("employee_number")
        snipe_user = None
        if employee_num:
            snipe_user = self.env["snipe.user"].search([
                ("employee_num", "=", employee_num)
            ], limit=1)

        if not snipe_user and assigned.get("username"):
            snipe_user = self.env["snipe.user"].search([
                ("username", "=", assigned.get("username"))
            ], limit=1)

        if not snipe_user and assigned.get("email"):
            snipe_user = self.env["snipe.user"].search([
                ("email", "=", assigned.get("email"))
            ], limit=1)

        # Jika tidak ditemukan, bisa buat baru jika perlu
        if not snipe_user:
            snipe_user = self.env["snipe.user"].create({
                "name": assigned.get("name"),
                "email": assigned.get("email"),
                "username": assigned.get("username"),
                "employee_num": assigned.get("employee_number"),
            })
        return snipe_user

    @api.model
    def create(self, vals):
        vals = self._map_employee_by_num(vals)
        return super().create(vals)

    def write(self, vals):
        vals = self._map_employee_by_num(vals)
        return super().write(vals)

    def api_output_dict(self):
        """
        Return dict representation for API output
        """
        self.ensure_one()
        employee = {
            #"id": self.id,
            "name": self.name,
            "email": self.email,
            "username": self.username,
            "employee_num": self.employee_num,
        }
        if self.employee_id:
            user = self.employee_id.user_id
            if user:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                image_url = f"{base_url}/web/image?model=res.users&field=image_1920&id={user.id}"
            else:
                image_url = self.employee_id.image_url
            employee.update(
                employee_id=self.employee_id.name,
                image_url = image_url,
                job_position = self.employee_id.job_position,
                department = self.employee_id.department_id.name,
                point_allocation= self.employee_id.point_allocation
            )
        return employee

    def api_output_hardware_dict(self):
        """
        Return data user yang dan hardware yang di assigned pada user ini
        """
        output_dict = self.api_output_dict()
        output_dict['hardware_list'] = [hardware.api_output_dict() for hardware in self.snipe_hardware_ids]

        return output_dict
