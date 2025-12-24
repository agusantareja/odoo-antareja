from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)

from bs4 import BeautifulSoup


def convert_html_to_text(html_content):
    if not html_content or html_content.strip() == "":
        return ""  # Kosong
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

class MinuteMeeting(models.Model):

    _inherit = "minute.meeting"

    attachment_extracted_status = fields.Selection([
        ('not_extracted', 'Not Extracted'),
        ('in_progress', 'In Progress'),
        ('no_data', 'No Data'),
        ('no_data_for_ocr', 'No Data for OCR'),
        ('extracted', 'Extracted'),
        ('can_not_extracted', 'Can Not Extracted'),], string='OCR Status', default='not_extracted',
    )
    attachment_extracted_text = fields.Text(string="OCR Text", help="The text extracted from the pdf using OCR.")
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'minute_attachment_rel',
        string='Attachments',
        states={'draft': [('readonly', False)]},
        readonly=True
    )

    def write(self, vals):
        super(MinuteMeeting, self).write(vals)
        __ignore_attachment_extracted_status = self.env.context.get('__ignore_attachment_extracted_status', False)
        if {'conclusion_note','attachment_ids'} & (vals or {}).keys():
            for rec in self:
                if self.get_using_queue_for_call_api():
                    # Use queue job to process the OCR extraction
                    rec.with_delay().do_attachment_extracted_text(
                        force_extracted=self.env.context.get('__force_extracted', False))
                elif rec.attachment_extracted_status != 'in_progress':
                    # akan di ekeskusi di cron
                    rec.attachment_extracted_status = 'not_extracted'

        return True

    def cron_ocr_pdf_attachments(self):
        self.search([('attachment_extracted_status', '=', 'not_extracted')]).action_ocr_pdf_attachments()

    def action_ocr_pdf_attachments(self):
        for rec in self:
            rec.write(
                {'attachment_extracted_status': 'in_progress'}
            )
            force_extracted = self.env.context.get('__force_extracted', False)
            if self.get_using_queue_for_call_api():
                # Use queue job to process the OCR extraction
                _logger.info("Run in queue %s", rec.name)
                rec=rec.with_delay()
            rec.do_attachment_extracted_text(force_extracted=force_extracted)

    def do_attachment_extracted_text(self,force_extracted=None):
        """ Call the OCR API to extract text from the attachment's PDF file. """
        self.ensure_one()
        prepare_text =[]

        text = convert_html_to_text(self.conclusion_note)  # Check if conclusion_note is empty
        if text:
            prepare_text.append("#Discussion Notes\n--------------------\n%s\n" % text)

        if self.attachment_ids and any(attachment.get_extract_able() for attachment in self.attachment_ids):
            force_extracted = force_extracted or self.env.context.get('__force_extracted', False)
            force_extracted and _logger.info("Force proses ekstraksi attachment pada %s", self.name)
            # Call the OCR API
            self.attachment_ids.call_ocr_extract_text(force_extracted=force_extracted)
            if any(attachment.ocr_status == 'extracted' for attachment in self.attachment_ids):
                _logger.info("Attachment pada %s berhasil di extract", self.name)
                # Update the extracted text field
                prepare_text.extend([
                     "\n#%s\n--------------------\n%s\n" %(attachment.name,attachment.ocr_extracted_text)
                     for attachment in self.attachment_ids if attachment.ocr_status == 'extracted'])
                self.write(
                    {'attachment_extracted_status': 'extracted'}
                )
            elif self.attachment_extracted_status !='extracted':
                # Jika tidak ada yang di extract
                _logger.info("Tidak ada attachment yang di extract pada %s", self.name)
                self.write(
                    {'attachment_extracted_status': 'can_not_extracted'}
                )
        else:
            _logger.info("Tidak ada attachment yang di extract pada %s", self.name)
            self.write(
                {'attachment_extracted_status': 'no_data_for_ocr'}
            )

        if prepare_text:
            attachment_extracted_text = "\n".join(prepare_text)
            self.write(
                {'attachment_extracted_text': attachment_extracted_text}
            )
        else:
            _logger.info("Tidak ada attachment yang di extract pada %s", self.name)
            self.write(
                {'attachment_extracted_status': 'no_data','attachment_extracted_text': ''}
            )
