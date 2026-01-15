from odoo import _, api, fields, models
import requests
import json
import base64
import logging
from datetime import datetime, timedelta, date
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
        _inherit = 'hr.employee'

        _sql_constraints = [
                ('hr_employee_user_uniq', 'unique (user_id,company_id,active)', 'User already exists!')
        ]


        birthday = fields.Date(index=True)
        date_of_join = fields.Date(string='Date of join')
        exp_date_contract = fields.Date(string='Date End Contract')
        no_bpjs_kesehatan = fields.Char(string='NO.BPJS')
        no_bpjstk = fields.Char(string='NO.KPJ-BPJSTK')
        grade = fields.Char(string='Grade')
        job_class_external = fields.Char(string='Job Class External')
        day_month_employee  = fields.Integer(string='For Sequence Birthday')
        bank_name = fields.Char(string='Bank Name')
        nama_rekening = fields.Char(string='Account Name')
        no_rekening = fields.Char(string='Account No')
        acting = fields.Boolean('Acting')
        job_position = fields.Char('Job Position', compute='_compute_acting', compute_sudo=True)
        approver_id = fields.Many2one('hr.employee', string='Approver')
        employee_category = fields.Char(string='Employee Category')
        previous_employee_id = fields.Many2one('hr.employee', string='Previous ID')
        is_cancel_terminate = fields.Boolean(string="Is Cancel Terminate", default=False)
        termination_date = fields.Date(string="Date of Termination")
        dummy = fields.Boolean(string='Dummy')
        hide_birthday = fields.Boolean('Hide Birthday', default=False)
        no_ktp = fields.Char(string='NO.KTP')
        no_npwp = fields.Char(string='NO.NPWP')
        ptkp = fields.Char(string='PTKP')
        classification_job = fields.Char(string='Classification Job')
        spl_admin = fields.Boolean(string='SPL Admin')
        directorate_id = fields.Many2one(
                'hr.department',
                string='Directorate',
                compute='_compute_directorate_id',
                store=True,
                index=True
        )

        @api.depends('department_id')
        def _compute_directorate_id(self):
                for emp in self:
                        directorate = False
                        dept = emp.department_id

                        while dept:
                                if dept.category_id and dept.category_id.name == 'DIRECTORATE':
                                        directorate = dept
                                        break
                                dept = dept.parent_id

                        emp.directorate_id = directorate

        @api.model
        def check_birthday_user(self,uid,date,month):
                query = """
                select id from hr_employee where user_id = %s and DATE_PART('day',birthday) = %s AND
DATE_PART('month', birthday) = %s
"""%(uid,date,month)
                self.env.cr.execute(query)
                if self.env.cr.fetchone():
                        return 1
                return 0
        
        @api.depends('acting', 'job_id')
        def _compute_acting(self):
            """For concat job position if have acting"""
            for rec in self:
                if rec.acting and rec.job_id:
                    rec.job_position = f"[Acting] - {rec.job_id.name}"
                elif rec.job_id:
                    rec.job_position = rec.job_id.name
                else:
                    rec.job_position = False

class hr_employee_base(models.AbstractModel):
        _inherit = 'hr.employee.base'

        nip = fields.Char('NIP')
        compute_field = fields.Boolean(compute="init_compute")
        image_url = fields.Char()
        image_html = fields.Html(sanitize = False,compute="get_url_image")
        point_allocation = fields.Char('Point of Allocation')
        filter_birthday_month = fields.Boolean(compute=True,search="search_birthday_this_month")
        birthday_state = fields.Char(compute="get_birthday_state")
        date_of_join = fields.Date(string='Date of join')
        filter_new_month = fields.Boolean(compute=True,search="search_new_employee_this_month")
        exp_date_contract = fields.Date(string='Date End Contract')
        no_bpjs_kesehatan = fields.Char(string='NO.BPJS')
        no_bpjstk = fields.Char(string='NO.KPJ-BPJSTK')
        grade = fields.Char(string='Grade')
        job_class_external = fields.Char(string='Job Class External')
        bank_name = fields.Char(string='Bank Name')
        nama_rekening = fields.Char(string='Account Name')
        no_rekening = fields.Char(string='Account No')
        filter_my_profile = fields.Boolean(compute=True, search='search_filter_my_profile')
        acting = fields.Boolean('Acting')
        job_position = fields.Char('Job Position', compute='_compute_acting', compute_sudo=True)
        approver_id = fields.Many2one('hr.employee', string='Approver')
        employee_category = fields.Char(string='Employee Category')
        dummy = fields.Boolean(string='Dummy')

        def search_new_employee_this_month(self,operator,operand):
                ids = [x['id'] for x in self.get_new_employees()]
                return [('id','in',ids)]
        


        def get_birthday_state(self):
                for rec in self:
                        if rec.birthday:
                                if rec.birthday == datetime.today().date():
                                        rec.birthday_state = 'today'
                                elif rec.birthday == datetime.today().date() + timedelta(days=1):
                                        rec.birthday_state = 'tomorrow'
                                else:
                                        rec.birthday_state = rec.birthday.strftime('%d %b')
                        else:
                                rec.birthday_state = False


        def search_birthday_this_month(self,operator,operand):
                ids = [x['id'] for x in self.get_employees_with_birthdays_this_month()]
                return [('id','in',ids)]
        
        @api.depends('acting', 'job_id')
        def _compute_acting(self):
            """For concat job position if have acting"""
            for rec in self:
                if rec.acting and rec.job_id:
                    rec.job_position = f"[Acting] - {rec.job_id.name}"
                elif rec.job_id:
                    rec.job_position = rec.job_id.name
                else:
                    rec.job_position = False


        @api.model
        def get_employees_with_birthdays_this_month(self, limit=None):
                self.env.cr.execute("""
                select
        hr_employee.id,
        hr_employee.name,
        case
                when DATE_PART('week', hr_employee.birthday) = DATE_PART('week', CURRENT_DATE)
                AND DATE_PART('day', hr_employee.birthday) = DATE_PART('day', CURRENT_DATE) then 'today'
                when DATE_PART('week', hr_employee.birthday) = DATE_PART('week', CURRENT_DATE)
                AND DATE_PART('day', hr_employee.birthday) = DATE_PART('day', CURRENT_DATE)+1 then 'tomorrow'
                else to_char(hr_employee.birthday, 'DD Mon')
        end as birthday,
        hr_employee.image_url,
        hr_department.name AS department,
        CASE 
            WHEN hr_employee.acting = true AND hr_job.name IS NOT NULL 
            THEN CONCAT('[Acting] - ', hr_job.name)
            ELSE hr_job.name
        END as job,
        hr_employee.point_allocation as point_allocation,
        res_company.color_code as color_code,
        res_company.code as company_code
        FROM
        hr_employee
        LEFT JOIN hr_department ON hr_employee.department_id = hr_department.id
        LEFT JOIN hr_job ON hr_employee.job_id = hr_job.id
        LEFT JOIN res_company ON hr_employee.company_id = res_company.id
        WHERE
        hr_employee.birthday IS NOT NULL
        AND DATE_PART('week', hr_employee.birthday) = DATE_PART('week', CURRENT_DATE)
        AND DATE_PART('day', hr_employee.birthday) >= DATE_PART('day', CURRENT_DATE)
        AND hr_employee.active=true
        AND (hr_employee.termination_date >= CURRENT_DATE OR hr_employee.termination_date IS NULL)
        AND hr_employee.hide_birthday IS NOT TRUE
        ORDER BY
        DATE_PART('day', hr_employee.birthday) ASC,
        hr_employee.birthday ASC,
        hr_employee.name asc
                LIMIT %s;
                """, (limit,))
                return self.env.cr.dictfetchall()



        @api.model
        def get_new_employees(self, limit=None):
                query = """
                select
        hr_employee.id,
        hr_employee.name,
        to_char(hr_employee.date_of_join, 'DD Mon YYYY') as date_of_join,
        hr_employee.image_url,
        hr_department.name AS department,
        CASE 
            WHEN hr_employee.acting = true AND hr_job.name IS NOT NULL 
            THEN CONCAT('[Acting] - ', hr_job.name)
            ELSE hr_job.name
        END as job,
        res_company.code as company_code,
        res_company.color_code as color_code,
        hr_employee.point_allocation as point_allocation
        FROM
        hr_employee
        LEFT JOIN hr_department ON hr_employee.department_id = hr_department.id
        LEFT JOIN hr_job ON hr_employee.job_id = hr_job.id
        LEFT JOIN res_company ON hr_employee.company_id = res_company.id
        WHERE
        hr_employee.date_of_join IS NOT NULL
        AND hr_employee.date_of_join > CURRENT_DATE - INTERVAL '3 months'
        AND DATE_PART('year', hr_employee.date_of_join) <= DATE_PART('year', CURRENT_DATE)
        AND DATE_PART('month', hr_employee.date_of_join) <= DATE_PART('month', CURRENT_DATE)
        AND hr_employee.active = True
        ORDER BY
        hr_employee.date_of_join desc,
        hr_employee.name asc"""
                if limit:
                        query += """
                        LIMIT %s"""%limit
                self.env.cr.execute(query)
                return self.env.cr.dictfetchall()

        def create_user(self):
                template_user = self.env.ref('base.default_user')
                for rec in self:
                        if rec.nip or rec.work_email:
                                company_ids = set()

                                # cari parent
                                parent = rec.parent_id
                                while parent:
                                        if parent.company_id:
                                                company_ids.add(parent.company_id.id)
                                        parent = parent.parent_id

                                # cari bawahan
                                children = self.env['hr.employee'].sudo().search([('parent_id','=',rec.id)])
                                for child in children:
                                        company_ids.add(child.company_id.id)

                                if company_ids:
                                        rec.user_id.write({
                                                'company_ids': [(4, cid, 0) for cid in company_ids]
                                        })

                                if rec.user_id and rec.user_id.login not in [rec.work_email,rec.nip]:
                                        rec.user_id.login = rec.nip or rec.work_email
                                
                                if rec.user_id.name != rec.name:
                                    rec.user_id.name = rec.name

                                new_image = False
                                if rec.image_url:
                                    try:
                                        response = requests.get(rec.image_url)
                                        if response.status_code == 200:
                                            new_image = base64.b64encode(response.content)
                                    except Exception as e:
                                        _logger.error(f"Failed to fetch image from URL {rec.image_url}: {e}")
                                
                                # Update image if it exists and is different
                                if rec.user_id and new_image:
                                    # Compare images properly - convert both to the same format for comparison
                                    current_image = rec.user_id.image_1920
                                    if not current_image or current_image != new_image:
                                        rec.user_id.image_1920 = new_image

                                group = self.env.ref('cni_overtime.group_spl_manager')
                                if rec.user_id and rec.spl_admin:
                                        rec.user_id.groups_id = [(4, group.id)]
                                else:
                                        rec.user_id.groups_id = [(3, group.id)]

                                if not rec.user_id:
                                        previous_employee = self.env['hr.employee'].sudo().search([('previous_employee_id','=',rec.id),('work_email','=',rec.work_email)], order="id desc", limit=1)
                                        if (rec.nip or rec.work_email) and not previous_employee:
                                                if rec.previous_employee_id:
                                                        old_employee = self.env['hr.employee'].sudo().with_context(active_test=False).search([('id', '=', rec.previous_employee_id.id)], order="id desc", limit=1)
                                                        if old_employee and old_employee.exp_date_contract and old_employee.exp_date_contract + timedelta(days=1) <= date.today():
                                                                user = old_employee.user_id
                                                                if user:
                                                                        old_employee.user_id = False
                                                                        rec.user_id = user
                                                                        rec.user_id.login = rec.nip or rec.work_email
                                                                else:
                                                                        values = {
                                                                        'name' : rec.name,
                                                                        'login' : rec.nip or rec.work_email,
                                                                        'active' : True,
                                                                        'image_1920' : base64.b64encode(requests.get(rec.image_url)._content),
                                                                        'company_id' : rec.company_id.id,
                                                                        'company_ids' : [(4, rec.company_id.id)],
                                                                        }
                                                                        user = self.env['res.users'].sudo().search([('active','=', True),('login','=',values['login'])],limit=1)
                                                                        if user:
                                                                                rec.user_id = user

                                                                        else:
                                                                                partner_id = self.env['res.partner'].search([('email', '=', rec.work_email), ('active', '=', True)], limit=1)
                                                                                if partner_id:
                                                                                        user_active = user.search([('partner_id','=',partner_id.id)],limit=1)
                                                                                        if user_active:
                                                                                                rec.user_id = user_active
                                                                                                rec.user_id.login = rec.nip or rec.work_email
                                                                                        else:
                                                                                                user = template_user.with_context(no_reset_password=True).copy(values)
                                                                                                rec.user_id = user 

                                                else:
                                                        values = {
                                                                'name' : rec.name,
                                                                'login' : rec.nip or rec.work_email,
                                                                'active' : True,
                                                                'image_1920' : base64.b64encode(requests.get(rec.image_url)._content),
                                                                'company_id' : rec.company_id.id,
                                                                'company_ids' : [(4, rec.company_id.id)],
                                                                }
                                                        with self.env.cr.savepoint():
                                                                user = self.env['res.users'].sudo().search([('active','in',[False,True]),('login','=',values['login'])],limit=1)
                                                                if user:
                                                                        employee_id = self.search([('id','!=',rec.id),('user_id','=',user.id)])
                                                                        if employee_id.active:
                                                                                raise Warning('Duplicate user login (new:%s,old:%s)'%(values['login'],rec.name))
                                                                        else:
                                                                                employee_id.user_id = False

                                                                if not user:
                                                                        user = template_user.with_context(no_reset_password=True).copy(values)
                                                                else:
                                                                        user.write(values)
                                                                user.groups_id += rec.job_id.group_ids
                                                                user.partner_id.email = rec.work_email
                                                                rec.user_id = user.id
                                                              
                                        elif (rec.nip or rec.work_email) and previous_employee:
                                                if rec.exp_date_contract and rec.exp_date_contract + timedelta(days=1) > date.today():
                                                        new_employee = self.env['hr.employee'].sudo().search([('previous_employee_id', '=', rec.id)], order="id desc", limit=1)
                                                        if new_employee:
                                                            user = new_employee.user_id
                                                            if user:
                                                                new_employee.user_id = False
                                                                rec.user_id = user
                                                                rec.user_id.login = rec.nip or rec.work_email
                                                            else:
                                                                values = {
                                                                'name' : rec.name,
                                                                'login' : rec.nip or rec.work_email,
                                                                'active' : True,
                                                                'image_1920' : base64.b64encode(requests.get(rec.image_url)._content),
                                                                'company_id' : rec.company_id.id,
                                                                'company_ids' : [(4, rec.company_id.id)],
                                                                }
                                                                user = self.env['res.users'].sudo().search([('active','=', True),('login','=',values['login'])],limit=1)
                                                                if user:
                                                                        rec.user_id = user

                                                                else:
                                                                        partner_id = self.env['res.partner'].search([('email', '=', rec.work_email), ('active', '=', True)], limit=1)
                                                                        if partner_id:
                                                                                user_active = user.search([('partner_id','=',partner_id.id)],limit=1)
                                                                                if user_active:
                                                                                        rec.user_id = user_active
                                                                                        rec.user_id.login = rec.nip or rec.work_email
                                                                                else:
                                                                                        user = template_user.with_context(no_reset_password=True).copy(values)
                                                                                        rec.user_id = user

                                        

        @api.depends('image_url')
        def get_url_image(self):
                # host, token = self.env['ir.config_parameter'].search(
                # [('key', '=', 'employee_source_api_host')]).value.split(';')
                for rec in self:
                        if rec.image_url:
                                rec.image_html = """
                                <img src="%s" class="oe_avatar"/>"""%rec.image_url

        def init_compute(self):
                for rec in self:
                        rec.compute_field = False

        @api.depends('coach', 'parent', 'department', 'job')
        def get_relation_employee(self):
                for rec in self:
                        rec.update({
                                'coach_id' : self.browse(rec.coach),
                                'parent_id' : self.browse(rec.parent),
                                'department_id' : self.env['hr.department'].browse(rec.department),
                                'job' : self.env['hr.job'].browse(rec.job),
                        })

        def sync_employee(self):
            pass

        @api.model
        def sync_employee_old(self):
                host, token = self.env['ir.config_parameter'].search(
                [('key', '=', 'employee_source_api_host')]).value.split(';')
                data = {}
                # try:
                resource_data = requests.get(host+'/api/cni/get_resource',
                                        headers={"token": token}).json()
                json_data = json.dumps(resource_data).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::resource_resource,'%s'))
        insert into resource_resource (select * from json_data where id not in (select id from resource_resource));
        """ % (json_data)
                self.env.cr.execute(query)
                self.env.cr.commit()

                job_deleted_data = requests.get(host+'/api/cni/get_job_deleted',
                                        headers={"token": token}).json()
                json_data = json.dumps(job_deleted_data).replace("\'", "''")

                query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
                DELETE FROM hr_job a
                USING json_data j
                WHERE a.id = j.id;
                """ % (json_data)
                self.env.cr.execute(query)

                job_data = requests.get(host+'/api/cni/get_job',
                                        headers={"token": token}).json()
                json_data = json.dumps(job_data).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
        insert into hr_job (select * from json_data where id not in (select id from hr_job));
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
        insert into res_groups (select 100+id,name,id as job_id from json_data where 100+id not in (select id from res_groups));
        
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
        update hr_job b 
        set 
        name = a.name,
        state = a.state,
        parent_id = a.parent_id,
        company_id = a.company_id,
        active = a.active
        from json_data a where b.id=a.id;

        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
        update res_groups b 
        set 
        name = a.name,
        job_id = a.id
        from json_data a where b.id=a.id+100;
        """ % (json_data,json_data,json_data,json_data)
                self.env.cr.execute(query)

                dept_category_data = requests.get(
                host+'/api/cni/get_dept_category', headers={"token": token}).json()
                json_data = json.dumps(dept_category_data).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::cni_hr_category_departement,'%s'))
        update cni_hr_category_departement b 
        set 
        name = a.name,
        tingkatan = a.tingkatan
        from json_data a where b.id=a.id;
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::cni_hr_category_departement,'%s'))
        insert into cni_hr_category_departement (select * from json_data where id not in (select id from cni_hr_category_departement));
        """ % (json_data, json_data)
                self.env.cr.execute(query)

                dept_deleted_data = requests.get(host+'/api/cni/get_department_deleted',
                                        headers={"token": token}).json()
                json_data = json.dumps(dept_deleted_data).replace("\'", "''")

                query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_department,'%s'))
                DELETE FROM hr_department a
                USING json_data j
                WHERE a.id = j.id;
                """ % (json_data)
                self.env.cr.execute(query)

                department_data = requests.get(
                host+'/api/cni/get_department', headers={"token": token}).json()
                json_data = json.dumps(department_data).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_department,'%s'))
        update hr_department b 
        set 
        name = a.name,
        complete_name = a.complete_name,
        kode = a.kode,
        active = a.active,
        category_id = a.category_id,
        company_id = a.company_id
        from json_data a where b.id=a.id;
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_department,'%s'))
        insert into hr_department (select * from json_data where id not in (select id from hr_department));
        """ % (json_data, json_data)
                self.env.cr.execute(query)

                emp_deleted_data = requests.get(host+'/api/cni/get_employee_deleted',
                                        headers={"token": token}).json()
                json_data = json.dumps(emp_deleted_data).replace("\'", "''")

                query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
                DELETE FROM hr_employee a
                USING json_data j
                WHERE a.id = j.id;
                """ % (json_data)
                self.env.cr.execute(query)

                datenow = datetime.now() + timedelta(hours=7)
                datenow = datenow.date()
                employee_data = requests.get(
                host+'/api/cni/get_employee', headers={"token": token}).json()
                json_data = json.dumps(employee_data).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
        update hr_employee b 
        set 
        name = a.name,
        nip = a.nip,
        birthday = a.birthday,
        day_month_employee = a.day_month_employee,
        work_email = a.work_email,
        department_id = a.department_id,
        job_id = a.job_id,
        mobile_phone = a.mobile_phone,
        image_url = a.image_url,
        active = a.active,
        no_bpjs_kesehatan = a.no_bpjs_kesehatan,
        no_bpjstk = a.no_bpjstk,
        date_of_join = a.date_of_join,
        company_id = a.company_id,
        point_allocation = a.point_allocation,
        exp_date_contract= a.exp_date_contract,
        employee_category = a.employee_category,
        termination_date = a.termination_date,
        hide_birthday = a.hide_birthday,
        acting = a.acting,
        previous_employee_id = a.previous_employee_id,
        departure_reason = a.departure_reason,
        is_cancel_terminate = a.is_cancel_terminate,
        dummy = a.dummy,
        no_ktp = a.no_ktp,
        no_npwp = a.no_npwp,
        ptkp = a.ptkp,
        classification_job = a.classification_job,
        spl_admin = a.spl_admin
        from json_data a where b.id=a.id;
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
        --insert into resource_resource (select resource_id,name,resource_type from json_data where id not in (select id from hr_employee));
        insert into hr_employee (select * from json_data where id not in (select id from hr_employee));

        update res_users set active=false where id in (select user_id from hr_employee where active = false);
        update res_users set active=false where id in (select user_id from hr_employee where active = true and exp_date_contract + INTERVAL '1 Day' <= '%s' and departure_reason != 'mutation');
        update res_users set active=true where id in (select user_id from hr_employee where active = true and exp_date_contract + INTERVAL '1 Day' > '%s' or is_cancel_terminate = true);
        --with json_data as (
        --SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
        --update res_users b
        --set active = a.active 
        --from json_data a where b.login=a.nip;
        update res_partner a set email = c.work_email 
        from res_users b
        left join hr_employee c on b.id = c.user_id 
        where b.partner_id = a.id
        and a.email != c.work_email;
        update res_users a set login = c.work_email 
        from hr_employee c where a.id = c.user_id 
        and c.nip is null
        and a.login != c.work_email and a.id not in (1,2);
        WITH json_data AS (
            SELECT * FROM json_populate_recordset(NULL::hr_employee, '%s')
        )
        SELECT id FROM json_data WHERE active = TRUE and id != 1;
        """ % (json_data, json_data, datenow, datenow, json_data, json_data)
                self.env.cr.execute(query)

                ids = [x[0] for x in self.env.cr.fetchall()]
                employee_ids = self.env['hr.employee'].sudo().browse(ids)
                for employee_id in employee_ids:
                    # Search for active employees with the same NIP
                    if not employee_id.nip:
                        continue
                    
                    employees = self.env['hr.employee'].sudo().search([('nip', '=', employee_id.nip), ('active', '=', True), ('company_id', '!=', 5)])
                    if len(employees) > 1:
                        # Two or more employees with the same NIP should have been linked to the same user.
                        common_user = employees.mapped('user_id').filtered_domain([('id', 'not in', [1, 2])])
                        # Archive some of these employees that no longer exist in HCIS and unlink them from their users
                        for employee in employees:
                            if employee.id not in ids:
                                employee.write({'active': False, 'user_id': False})
                        # Exclude employees archived from the previous step
                        employees = employees.filtered_domain([('active', '=', True)])
                        # Skip further processing of these employees if `common_user` is an empty recordset
                        if not common_user:
                            # All records in `employees` might get archived from the previous step
                            if employees:
                                warn_messages = ['Found active employees not linked to any users:']
                                for employee in employees:
                                    warn_messages.append(f'- ID: {employee.id}, NIP: {employee.nip}, Name: {employee.name}')
                                _logger.warn('\n'.join(warn_messages))
                            continue
                        # Unfortunately, we found a case where `common_user` contains more than one record, hence this assertion.
                        if len(common_user) == 1:
                            employees.write({'user_id': common_user.id})
                            # This is to handle dummy employees (same `nip`, different `company_id`), although
                            # there shouldn't be new dummy employees anymore.
                            common_user.company_ids |= employees.mapped('company_id')
                            continue
                        # For the case where `common_user` contains more than one record:
                        for user in common_user:
                            if not user.employee_ids:
                                # This user is not linked to any employees, let's archive it.
                                _logger.warn(f"User '{user.name}' (login: {user.login}, id: {user.id}) is not linked to any employees. Archiving...")
                                user.active = False
                                # The other users in `common_user` might have their `login` fields updated that conflict with this
                                # user's `login` field in the next invocation of `sync_employee()`. Let's avoid that by prefixing
                                # this user's `login` field with 'archived_by_sync_employee-'.
                                user.login = 'archived_by_sync_employee-' + user.login
                                continue
                            # This user still has some employees linked to it.
                            warn_message = f"User '{user.name}' (login: {user.login}, id: {user.id}) is linked to a duplicated employee:\n"
                            warn_message += '\n'.join(user.employee_ids.mapped(lambda r: f'- ID: {r.id}, NIP: {r.nip}, Name: {r.name}'))
                            _logger.warn(warn_message)
                    else:
                        # Check if employee_id still exists and create user
                        if employee_id.exists():
                            employee_id.create_user()
                            employee_id.create_tapping()

                        if employee_id.previous_employee_id:
                              self.data_emp_transfer(employee_id.previous_employee_id, employee_id)

                #this for data user have 2 employee but different nip
                employees_to_unlink = self.env['hr.employee'].sudo()
                for employee_id in employee_ids:
                    login = []
                    if employee_id.nip:
                        login.append(employee_id.nip)
                    if employee_id.work_email:
                        login.append(employee_id.work_email)
                    #check if employee have user and user login is not same with employee_id or email
                    should_unlink_user = employee_id.user_id and employee_id.user_id.login not in login

                    if should_unlink_user:
                        employees_to_unlink |= employee_id
                
                if employees_to_unlink:
                    employees_to_unlink.write({'user_id': False})
                    

                employee_hierarchy = requests.get(
                host+'/api/cni/get_employee_hierarchy', headers={"token": token}).json()
                json_data = json.dumps(employee_hierarchy).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
        update hr_employee b 
        set 
        coach_id = a.coach_id,
        parent_id = a.parent_id,
        job_class_external = a.job_class_external,
        grade = a.grade
        from json_data a where b.id=a.id;
        """ % (json_data)
                self.env.cr.execute(query)

                department_hierarchy = requests.get(
                host+'/api/cni/get_department_hierarchy', headers={"token": token}).json()
                json_data = json.dumps(department_hierarchy).replace("\'", "''")
                query = """
        with json_data as (
        SELECT * FROM json_populate_recordset (NULL::hr_department,'%s'))
        update hr_department b 
        set 
        manager_id = a.manager_id,
        parent_id = a.parent_id
        from json_data a where b.id=a.id;
        """ % (json_data)
                self.env.cr.execute(query)
        #         query = """
        # update res_company_users_rel a set cid = d.id
        # from res_users b 
        # left join hr_employee c on b.id = c.user_id
        # left join res_company d on d.id = b.company_id 
        # where b.company_id != c.company_id
        # and a.user_id = b.id and b.id not in (1,2);
        # update res_users a set company_id = b.company_id 
        # from hr_employee b 
        # where b.user_id = a.id 
        # and a.company_id != b.company_id;
        # """
        #         self.env.cr.execute(query)

        @api.model
        def sync_employee_cjtp(self):
            host, token = self.env['ir.config_parameter'].search(
                [('key', '=', 'employee_source_api_host_cjtp')]).value.split(';')
            resource_data = requests.get(host+'/api/cjtp/get_resource',
                                        headers={"token": token}).json()
            json_data = json.dumps(resource_data).replace("\'", "''")
            query = """
              with json_data as (
              SELECT * FROM json_populate_recordset (NULL::resource_resource,'%s'))
              insert into resource_resource (select id+10000, name, active, company_id, resource_type, null,time_efficiency, calendar_id, tz from json_data where id+10000 not in (select id from resource_resource));
              """%(json_data)
            self.env.cr.execute(query)
            self.env.cr.commit()

            job_data = requests.get(host+'/api/cjtp/get_job',
                                        headers={"token": token}).json()
            json_data = json.dumps(job_data).replace("\'", "''")
            query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
                insert into hr_job (select id+1000,name,null,null,null,null,null,null,null,company_id,state,null from json_data where id+1000 not in (select id from hr_job));
                
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_job,'%s'))
                update hr_job b 
                set 
                name = a.name,
                state = a.state,
                company_id = a.company_id
                from json_data a where b.id=a.id+1000;
                """ % (json_data,json_data)
            self.env.cr.execute(query)
            self.env.cr.commit()

            department_data = requests.get(host+'/api/cjtp/get_department', headers={"token": token}).json()
            json_data = json.dumps(department_data).replace("\'", "''")
            query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_department,'%s'))
                update hr_department b 
                set 
                name = a.name,
                complete_name = a.complete_name,
                active = a.active,
                company_id = a.company_id
                from json_data a where b.id=a.id+1000;
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_department,'%s'))
                insert into hr_department (select id+1000,name,complete_name,active,company_id,null from json_data where id+1000 not in (select id from hr_department));
                """ % (json_data, json_data)
            self.env.cr.execute(query)
            self.env.cr.commit()


            employee_data = requests.get(host+'/api/cjtp/get_employee', headers={"token": token}).json()
            json_data = json.dumps(employee_data).replace("\'", "''")
            query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
                update hr_employee b 
                set 
                name = a.name,
                nip = a.permit_no,
                work_email = a.work_email,
                mobile_phone = a.mobile_phone,
                image_url = a.image_url,
                department_id = a.department_id+1000,
                job_id = a.job_id+1000,
                active = a.active,
                company_id = a.company_id
                from json_data a where b.id=a.id+10000;
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
                --insert into resource_resource (select resource_id+10000,name,resource_type from json_data where id not in (select id from hr_employee));
                insert into hr_employee (select id+10000, name, null, active,null,null,gender,null,null,null,null,null,null,null,null,null,null,null,null,
                null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,null,department_id+1000,job_id+1000,null,company_id,null,null,mobile_phone,
                work_email,null,resource_id+10000,null,null,null,null,null,1,null,permit_no as nip,image_url as image_url
                from json_data where id+10000 not in (select id from hr_employee));

                update res_users set active=false where id in (select user_id from hr_employee where active = false);
                update res_partner a set email = c.work_email 
                from res_users b
                left join hr_employee c on b.id = c.user_id 
                where b.partner_id = a.id
                and a.email != c.work_email;
                update res_users a set login = c.work_email 
                from hr_employee c where a.id = c.user_id 
                and c.nip is null
                and a.login != c.work_email and a.id not in (1,2);
                select id from hr_employee where user_id is null and active = true;
                """ % (json_data, json_data)
            self.env.cr.execute(query)
            ids = [(x[0] for x in self.env.cr.fetchall())]
            for id in ids:
                employee_id = self.env['hr.employee'].sudo().browse(id)
                try:
                    employee_id.create_user()
                    employee_id.create_tapping()
                except:
                    pass

        def search_filter_my_profile(self, operator, operand):
            employee = self.env["hr.employee"].sudo().search([('user_id', '=', self.env.user.id)]).ids
            return [('id', 'in', employee)]

        def sync_approver_employee(self):
            host = self.env['ir.config_parameter'].search(
                [('key', '=', 'hr.cerindocorp.id')]).value
            token = self.env['ir.config_parameter'].search(
                [('key', '=', 'leave.token_hr')]).value
            url = self.env['ir.config_parameter'].search(
                [('key', '=', 'cni_employee_intra.rest_api_approver_employee')]).value
            approver_data = requests.get(host+url, headers={"token": token}).json()
            data = approver_data.get('data', [])
            json_data = json.dumps(data).replace("\'", "''")
            query = """
                with json_data as (
                SELECT * FROM json_populate_recordset (NULL::hr_employee,'%s'))
                update hr_employee b 
                SET approver_id = CASE 
                    WHEN a.approver_id IS NOT NULL THEN a.approver_id
                    ELSE b.approver_id
                END 
                from json_data a where b.id=a.id;
                """ % (json_data)   
            self.env.cr.execute(query)

        def data_emp_transfer(self, employee, new_employee):
            search_lb = self.env['leave.leave_balance'].sudo().search([('employee_id','=',employee.id)])
            if search_lb:
                search_lb.write({
                    'employee_id': new_employee.id,
                    'company_id': new_employee.company_id.id
                })
            search_lr = self.env['leave.leave_request'].sudo().search([('employee_id','=',employee.id)])
            if search_lr:
                query = "UPDATE leave_leave_request SET employee_id = %s, company_id = %s WHERE id IN %s"
                params = (new_employee.id, new_employee.company_id.id, tuple(search_lr.ids))
                self._cr.execute(query, params)
            search_lcr = self.env['leave.compensatory_request'].sudo().search([('employee_id','=',employee.id)])
            if search_lcr:    
                search_lcr.write({
                    'employee_id': new_employee.id,
                    'company_id': new_employee.company_id.id
                })
            search_att = self.env['web.attendance'].sudo().search([('employee_id','=',employee.id)])
            if search_att:
                search_att.write({
                    'employee_id': new_employee.id,
                    'company_id': new_employee.company_id.id
                })
            search_att_cor = self.env['cni.attendance.correction'].sudo().search([('employee_id','=',employee.id)])
            if search_att_cor:
                search_att_cor.write({
                    'employee_id': new_employee.id,
                })

class HREmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    day_month_employee  = fields.Integer(string='For Sequence Birthday')
    dummy = fields.Boolean(string='Dummy')
