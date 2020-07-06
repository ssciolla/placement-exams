# standard libraries
import logging, os
from smtplib import SMTPException
from typing import Any, Dict, List, Tuple

# third-party libraries
from django.core.mail import send_mail
from django.db.models import QuerySet
from django.forms.models import model_to_dict
from django.template.loader import render_to_string

# local libraries
from pe.models import Report


LOGGER = logging.getLogger(__name__)


class Reporter:
    """Utility class for collecting metadata, preparing report data, rendering templates, and sending email."""

    report_sub_fields: Tuple[str, ...] = ('submission_id', 'student_uniqname', 'score', 'submitted_timestamp')

    def __init__(self, report) -> None:
        """
        Assigns report and initializes other instance variables set externally or via prepare_context.

        :return: None
        :rtype: None
        """
        self.report: Report = report
        self.exams_time_metadata: Dict[int, Dict[str, Any]] = dict()
        self.total_successes: int = 0
        self.total_failures: int = 0
        self.total_new: int = 0
        self.context: Dict[str, Any] = dict()

    def prepare_context(self) -> None:
        """
        Prepares the context in a dictionary structure that can be passed to the template via render_to_string.

        :return: None
        :rtype: None
        """
        exam_dicts: List[Dict[str, Any]] = []
        for exam in self.report.exams.all():
            exam_dict: Dict[str, Any] = model_to_dict(exam)

            exam_dict['time'] = self.exams_time_metadata[exam.id]
            
            success_sub_qs: QuerySet = exam.submissions.filter(
                transmitted=True, transmitted_timestamp__gte=exam_dict['time']['start_time']
            )
            num_successes: int = len(success_sub_qs)

            # ScoresOrchestration tries to send everything that is un-transmitted,
            # so anything left un-transmitted after a run is a failure.
            failure_sub_qs: QuerySet = exam.submissions.filter(transmitted=False)
            num_failures: int = len(failure_sub_qs)

            new_sub_qs: QuerySet = exam.submissions.filter(graded_timestamp__gte=exam_dict['time']['datetime_filter'])
            num_new: int = len(new_sub_qs)

            exam_dict['summary'] = {'success_count': num_successes, 'failure_count': num_failures, 'new_count': num_new}

            exam_dict['successes'] = list(success_sub_qs.values(*self.report_sub_fields))
            exam_dict['failures'] = list(failure_sub_qs.values(*self.report_sub_fields))
            exam_dicts.append(exam_dict)

            self.total_successes += num_successes
            self.total_failures += num_failures
            self.total_new += num_new

        report_dict: Dict[str, Any] = model_to_dict(self.report)
        report_dict['summary'] = {
            'success_count': self.total_successes,
            'failure_count': self.total_failures,
            'new_count': self.total_new
        }

        support_email: str = os.getenv('SUPPORT_EMAIL', 'its.tl.staff@umich.edu')
        self.context = {'report': report_dict, 'exams': exam_dicts, 'support_email': support_email}
        LOGGER.debug(self.context)

    def get_subject(self) -> str:
        """
        Creates and returns subject message based on reports, exams, and accounts generated by prepare_context.

        :return: Email subject line referencing the report name, summary counts, and exams covered.
        :rtype: str
        """
        subject: str = (
            f'Placement Exams Report - {self.report.name} - ' +
            f'Success: {self.total_successes}, Failure: {self.total_failures}, New: {self.total_new} - ' +
            ', '.join([exam.name for exam in self.report.exams.all()])
        )
        LOGGER.debug(subject)
        return subject

    def send_email(self) -> None:
        """
        Uses the context to render email text (plain and HTML) and then sends a multi-part email.

        :return: None
        :rtype: None
        """
        plain_text_email: str = render_to_string('email.txt', self.context)
        html_email: str = render_to_string('email.html', self.context)

        try:
            result = send_mail(
                subject=self.get_subject(),
                message=plain_text_email,
                from_email=os.getenv('SMTP_FROM', ''),
                recipient_list=[self.report.contact],
                html_message=html_email
            )
            LOGGER.debug(result)
            LOGGER.info('Successfully sent email')
        except SMTPException as e:
            LOGGER.error(f'Error: unable to send email due to {e}')
