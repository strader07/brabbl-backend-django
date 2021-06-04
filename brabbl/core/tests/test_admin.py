from django.test import TestCase
from django.utils.translation import ugettext as _
from django.forms.forms import NON_FIELD_ERRORS

from brabbl.accounts.tests import factories
from brabbl.core.forms import DiscussionForm


class DiscussionAdminTestCase(TestCase):
    def test_send_news_mail(self):
        customer = factories.CustomerFactory.create()
        user = factories.UserFactory.create(customer=customer)

        form_data = {
            'customer': customer.pk,
            'created_by': user.pk,
            'external_id': '123',
            'source_url': 'http://test.com',
            'statement': 'test',
            'language': 'en',
            'start_time': '2016-09-10 12:00:12.000000',
            'end_time': '2016-10-10 12:00:12.000000',
        }
        form = DiscussionForm(data=form_data)
        self.assertTrue(form.is_valid())

        form_data['start_time'] = '2016-10-10 12:00:12.000000'
        form_data['end_time'] = '2016-09-10 12:00:12.000000'
        form = DiscussionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn(_("End time cannot be earlier than start time!"), form._errors[NON_FIELD_ERRORS])
