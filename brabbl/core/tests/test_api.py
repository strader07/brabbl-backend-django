import json
from django.core import mail
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status

from brabbl.accounts.tests.factories import add_staff_permissions_to_user
from brabbl.utils import test
from .. import models
from . import factories


class PermissionTestMixin(object):
    editable_by_user = True
    deletable_by_user = True

    def test_permission_flags_user(self):
        self.client.as_user(self.user)
        obj = self.get_object()

        response = self.retrieve(obj=obj)
        self.assertEqual(response.data['is_editable'], self.editable_by_user)
        self.assertEqual(response.data['is_deletable'], self.deletable_by_user)

        obj.last_related_activity = now()
        obj.save()

        response = self.retrieve(obj=obj)
        self.assertEqual(response.data['is_editable'], False)
        self.assertEqual(response.data['is_deletable'], False)

    def test_permission_flags_admin(self):
        add_staff_permissions_to_user(self.user)
        self.client.as_user(self.user)
        obj = self.get_object()

        response = self.retrieve(obj=obj)
        self.assertEqual(response.data['is_editable'], True)
        self.assertEqual(response.data['is_deletable'], True)

        obj.last_related_activity = now()
        obj.save()

        response = self.retrieve(obj=obj)
        self.assertEqual(response.data['is_editable'], True)
        self.assertEqual(response.data['is_deletable'], True)


class TagAPITest(test.CreateTestMixin,
                 test.ListTestMixin,
                 test.BrabblAPITestCase):
    base_name = 'tag'
    create_required_fields = ['name']

    def get_create_data(self):
        return {'name': 'test'}

    def get_object(self, **properties):
        return factories.TagFactory(
            customer=self.customer
        )

    def create(self, *args, **kwargs):
        add_staff_permissions_to_user(self.user)
        response = super().create(*args, **kwargs)
        add_staff_permissions_to_user(self.user)
        return response


class WordingAPITest(test.RetrieveTestMixin,
                     test.ListTestMixin,
                     test.BrabblAPITestCase):
    base_name = 'wording'

    def get_object(self, **properties):
        return factories.WordingFactory()


class DiscussionListAPITest(test.RetrieveTestMixin,
                            test.UpdateTestMixin,
                            test.CreateTestMixin,
                            PermissionTestMixin,
                            test.BrabblAPITestCase):
    base_name = 'discussion_list'
    lookup_param = 'url'

    editable_by_user = False
    deletable_by_user = False
    create_customer_required = True

    def get_create_data(self):
        return {
            'name': 'Test',
            'url': 'http://example.com',
            'tags': ['foo', 'bar'],
            'search_by': models.DiscussionList.SEARCH_BY_ALL_TAGS
        }

    def get_update_data(self):
        return {
            'name': 'New Test',
            'url': 'http://new-example.com',
            'tags': ['foo', 'bar'],
            'search_by': models.DiscussionList.SEARCH_BY_ANY_TAG
        }

    def create(self, *args, **kwargs):
        add_staff_permissions_to_user(self.user)
        response = super().create(*args, **kwargs)
        self.user.user_permissions.clear()
        return response

    def update(self, *args, **kwargs):
        add_staff_permissions_to_user(self.user)
        response = super().update(*args, **kwargs)
        self.user.user_permissions.clear()
        return response

    def get_object(self, **properties):
        return factories.DiscussionListFactory()

    def test_204_instead_of_404(self):
        url = self.get_retrieve_url() + 'appendix'
        self.client.as_customer(self.customer)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class DiscussionAPITest(test.ViewSetTestMixin,
                        PermissionTestMixin,
                        test.BrabblAPITestCase):
    base_name = 'discussion'
    lookup_param = 'external_id'

    create_required_fields = [
        'external_id', 'url', 'statement']

    editable_by_user = False
    deletable_by_user = False

    def setUp(self):
        super().setUp()
        self.wording = factories.WordingFactory.create()

    def get_object(self, **properties):
        return factories.SimpleDiscussionFactory(
            customer=self.customer,
            barometer_wording=self.wording,
            image_url='http://example.com/image.png',
            **properties
        )

    def get_create_data(self):
        return {
            'external_id': 'df34d342l',
            'url': 'http://example.com/test3',
            'statement': 'Pigs are creators',
            'tags': ['hallo', 'Hallo Beta'],
            'wording': self.wording.pk,
            'multiple_statements_allowed': False,
            'user_can_add_replies': False,
            'has_barometer': True,
            'has_arguments': True,
        }

    def get_update_data(self):
        return {
            'url': 'http://example.com/changed',
            'statement': 'Pigs are creators (changed)',
            # TODO
            # 'tags': ['hallo', 'Hallo Beta'],
            # 'wording': new_wording.pk,
            'multiple_statements_allowed': True,
            'user_can_add_replies': True,
            'has_barometer': False,
            'has_arguments': False,
        }

    def create(self, *args, **kwargs):
        add_staff_permissions_to_user(self.user)
        response = super().create(*args, **kwargs)
        self.user.user_permissions.clear()
        return response

    def update(self, *args, **kwargs):
        add_staff_permissions_to_user(self.user)
        response = super().update(*args, **kwargs)
        self.user.user_permissions.clear()
        return response

    def destroy(self, *args, **kwargs):
        add_staff_permissions_to_user(self.user)
        response = super().destroy(*args, **kwargs)
        self.user.user_permissions.clear()
        return response

    def test_list_attributes(self):
        factories.ComplexDiscussionFactory.create(customer=self.customer)
        factories.SimpleDiscussionFactory.create(customer=self.customer)
        response = self.get_list()
        self.assertEqual(len(response.data), 2)

        complex_discussion, simple_discussion = response.data
        if not complex_discussion['multiple_statements_allowed']:
            complex_discussion, simple_discussion = simple_discussion, complex_discussion

        self.assertTrue('barometer' in simple_discussion)
        self.assertTrue('argument_count' in simple_discussion)
        self.assertFalse('barometer' in complex_discussion)
        self.assertTrue('statement_count' in complex_discussion)

    def test_create(self):
        response = super().test_create()
        self.assertEqual(response.data['created_by'], self.user.username)

        # object is created
        self.assertEqual(
            models.Discussion.objects.filter(
                external_id=self.get_create_data()['external_id']
            ).count(),
            1
        )

        discussion = models.Discussion.objects.get(
            external_id=self.get_create_data()['external_id'])

        # test attributes
        self.assertEqual(discussion.customer, self.customer)
        self.assertEqual(discussion.created_by, self.user)
        self.assertEqual(discussion.tags.count(), 2)
        self.assertTrue(discussion.tags.filter(name='Hallo Beta').exists())
        self.assertTrue(discussion.tags.filter(name='hallo').exists())

        # there should be one statement with empty `statement`
        self.assertEqual(
            models.Statement.objects.filter(
                discussion=discussion,
                created_by=self.user,
                statement='',
            ).count(),
            1
        )

    def test_create_admin_required(self):
        self.set_create_headers()
        response = self.client.post(self.get_create_url(), data=self.get_create_data())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_admin_required(self):
        self.set_update_headers()
        response = self.client.patch(self.get_update_url(),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_admin_required(self):
        self.set_destroy_headers()
        response = self.client.patch(self.get_destroy_url())
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_complex_create(self):
        data = self.get_create_data()
        data['multiple_statements_allowed'] = True

        self.create(data=data)

        discussion = models.Discussion.objects.get(
            external_id=self.get_create_data()['external_id'])

        # there should be no associated statement
        self.assertEqual(
            models.Statement.objects.filter(
                discussion=discussion,
            ).count(),
            0
        )

    def test_create_duplicate(self):
        discussion = self.get_object()
        data = self.get_create_data()
        data['external_id'] = discussion.external_id

        self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)

    def test_create_with_wrong_time_limit(self):
        data = self.get_create_data()
        data['start_time'] = '2016-10-10 12:00:12.000000'
        data['end_time'] = '2016-09-10 12:00:12.000000'
        self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)

    def test_update_with_wrong_time_limit(self):
        data = self.get_update_data()
        data['start_time'] = '2016-10-10 12:00:12.000000'
        data['end_time'] = '2016-09-10 12:00:12.000000'
        self.update(data=data, status_code=status.HTTP_400_BAD_REQUEST)

    def test_barometer_requires_wording(self):
        data = self.get_create_data()
        del data['wording']

        response = self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)
        self.assertTrue('non_field_errors' in response.data)
        self.assertTrue('Wording' in response.data['non_field_errors'][0])

        data = self.get_create_data()
        del data['wording']
        data['has_barometer'] = False
        self.create(data=data)

    def test_invalid_wording(self):
        data = self.get_create_data()
        data['wording'] = 4499999

        response = self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)
        self.assertTrue('wording' in response.data)

    def test_include_only_visible_statements(self):
        discussion = factories.ComplexDiscussionFactory.create(customer=self.customer)
        statement1, statement2 = factories.StatementFactory.create_batch(
            2, discussion=discussion)

        response = self.retrieve(obj=discussion)
        self.assertEqual(len(response.data['statements']), 2)

        statement2.delete()
        response = self.retrieve(obj=discussion)
        self.assertEqual(len(response.data['statements']), 1)
        self.assertEqual(response.data['statements'][0]['id'], statement1.id)


class StatementAPITest(test.ViewSetTestMixin,
                       PermissionTestMixin,
                       test.BrabblAPITestCase):
    base_name = 'statement'

    create_required_fields = [
        'discussion_id', 'statement']

    def setUp(self):
        super().setUp()
        self.wording = factories.WordingFactory.create()
        self.discussion = factories.ComplexDiscussionFactory(
            customer=self.customer,
            barometer_wording=self.wording,
        )

    def get_object(self):
        return factories.StatementFactory.create(discussion=self.discussion,
                                                 created_by=self.user)

    def get_create_data(self):
        return {
            'discussion_id': self.discussion.external_id,
            'statement': 'Dogs are creators',
            'video': 'https://www.youtube.com/watch?v=TKukepIA34w'
        }

    def get_update_data(self):
        return {
            'statement': 'Dogs are creators (changed)',
        }

    def test_create(self):
        self.assertEqual(self.discussion.statements.all().count(), 0)
        response = super().test_create()
        self.assertEqual(self.discussion.statements.all().count(), 1)
        self.assertEqual(response.data['created_by'], self.user.username)

    def test_multiple_statements_allowed(self):
        # create first statement
        self.create()

        # add another statement
        data = self.get_create_data()
        data['statement'] = 'Ducks are evil!'

        self.create(data=data)
        self.assertEqual(self.discussion.statements.all().count(), 2)

    def test_disallow_statement_creation_by_user(self):
        self.discussion.user_can_add_replies = False
        self.discussion.save()

        self.create(status_code=status.HTTP_403_FORBIDDEN)

    def test_creation_for_non_existing_discussion(self):
        data = self.get_create_data()
        data['discussion_id'] = 'non_existing'

        self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)

    def test_disallow_statement_creation_for_simple_discussion(self):
        discussion = factories.SimpleDiscussionFactory.create(customer=self.customer)
        data = self.get_create_data()
        data['discussion_id'] = discussion.external_id

        self.create(data=data, status_code=status.HTTP_403_FORBIDDEN)

    def test_foreign_discussion(self):
        foreign_discussion = factories.ComplexDiscussionFactory.create()
        data = self.get_create_data()
        data['discussion_id'] = foreign_discussion.id

        response = self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)
        self.assertTrue('discussion_id' in response.data)

    def test_initial_vote_values(self):
        response = self.retrieve()
        self.assertTrue('barometer' in response.data)
        self.assertEqual(response.data['barometer']['count'], 0)
        self.assertEqual(response.data['barometer']['rating'], 0)
        self.assertTrue('wording' in response.data['barometer'])
        self.assertEqual(len(response.data['barometer']['wording']),
                         self.wording.words.count())

    def test_attach_barometer_only_if_has_barometer(self):
        response = self.retrieve()
        self.assertTrue('barometer' in response.data)
        self.discussion.has_barometer = False
        self.discussion.save()

        response = self.retrieve()
        self.assertFalse('barometer' in response.data)

    def test_update_not_allowed_by_foreign_user(self):
        self.set_update_headers()
        foreign_user = factories.UserFactory.create()
        self.update(status_code=status.HTTP_403_FORBIDDEN, as_user=foreign_user)

    def test_update_only_if_not_changed(self):
        self.set_update_headers()
        statement = self.get_object()
        statement.last_related_activity = now()
        statement.save()

        response = self.client.patch(self.get_update_url(statement),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_allowed_by_admin(self):
        self.set_update_headers()
        user = factories.UserFactory.create()
        add_staff_permissions_to_user(user)
        self.client.as_user(user)
        statement = self.get_object()

        response = self.client.patch(self.get_update_url(statement),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # editing is even allowed after an related object has changed
        statement.last_related_activity = now()
        statement.save()
        response = self.client.patch(self.get_update_url(statement),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destroy_not_allowed_by_foreign_user(self):
        foreign_user = factories.UserFactory.create()
        self.destroy(status_code=status.HTTP_403_FORBIDDEN, as_user=foreign_user)

    def test_destroy_only_if_not_changed(self):
        self.set_destroy_headers()
        statement = self.get_object()
        statement.last_related_activity = now()
        statement.save()

        response = self.client.delete(self.get_destroy_url(statement))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_allowed_by_admin(self):
        self.set_destroy_headers()
        user = factories.UserFactory.create()
        add_staff_permissions_to_user(user)
        self.client.as_user(user)
        statement = self.get_object()

        response = self.client.delete(self.get_destroy_url(statement))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_include_only_visible_arguments(self):
        statement = factories.StatementFactory.create(discussion=self.discussion)
        argument1, argument2 = factories.ArgumentFactory.create_batch(
            2, statement=statement)

        response = self.retrieve(obj=statement)
        self.assertEqual(len(response.data['arguments']), 2)

        argument2.delete()
        response = self.retrieve(obj=statement)
        self.assertEqual(len(response.data['arguments']), 1)
        self.assertEqual(response.data['arguments'][0]['id'], argument1.id)


class StatementVoteAPITest(test.CreateTestMixin,
                           test.BrabblAPITestCase):
    base_name = 'statement'
    create_required_fields = [
        'rating']

    def setUp(self):
        super().setUp()
        self.discussion = factories.SimpleDiscussionFactory(customer=self.customer)

    def get_object(self):
        return self.discussion.statements.all()[0]

    def get_vote(self):
        return models.BarometerVote.objects.create(
            statement=self.get_object(),
            user=self.user,
            value=2,
        )

    def get_create_url(self, statement=None):
        if not statement:
            statement = self.get_object()

        url = reverse('v1:{0}-detail'.format(self.base_name),
                      args=(statement.pk,))
        return '{0}vote/'.format(url)

    def get_create_data(self):
        return {
            'rating': 3,
        }

    def test_create(self):
        response = super().test_create()
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['rating'], 3)
        self.assertEqual(response.data['user_rating'], 3)

    def test_vote_must_be_natural_within_range(self):
        # invalid
        self.create(data={'rating': 4}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': -4}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 1.5}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 1.2}, status_code=status.HTTP_400_BAD_REQUEST)

        # valid
        self.create(data={'rating': -3}, status_code=status.HTTP_201_CREATED)
        self.create(data={'rating': -1}, status_code=status.HTTP_201_CREATED)
        self.create(data={'rating': 0}, status_code=status.HTTP_201_CREATED)
        self.create(data={'rating': 3}, status_code=status.HTTP_201_CREATED)

    def test_update_existing_vote(self):
        self.get_vote()
        response = self.create(data={'rating': 2})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['rating'], 2)
        self.assertEqual(response.data['user_rating'], 2)

    def test_allowed_only_if_has_barometer(self):
        self.discussion.has_barometer = False
        self.discussion.save()
        self.create(data={'rating': 2}, status_code=status.HTTP_403_FORBIDDEN)

    def test_mean_and_count(self):
        self.create(data={'rating': 3}, as_user=factories.UserFactory.create())
        self.create(data={'rating': -2}, as_user=factories.UserFactory.create())
        self.create(data={'rating': 0}, as_user=factories.UserFactory.create())
        response = self.create(
            data={'rating': -2}, as_user=factories.UserFactory.create())

        self.assertEqual(response.data['count'], 4)
        self.assertAlmostEqual(response.data['rating'], -0.25, 1)
        self.assertEqual(response.data['user_rating'], -2)  # value of last response


class ArgumentAPITest(test.ViewSetTestMixin,
                      PermissionTestMixin,
                      test.BrabblAPITestCase):
    base_name = 'argument'

    create_required_fields = [
        'statement_id', 'title', 'text']  # TODO 'is_pro' should be required

    def setUp(self):
        super().setUp()
        self.discussion = factories.SimpleDiscussionFactory(customer=self.customer)
        self.statement = self.discussion.statements.all()[0]

    def get_object(self):
        return factories.ArgumentFactory.create(statement=self.statement,
                                                created_by=self.user,
                                                is_pro=True)

    def get_create_data(self):
        return {
            'statement_id': self.statement.id,
            'title': 'Dogs are creators',
            'text': 'Fusce egestas elit eget. Fusce egestas elit eget.',
            'is_pro': True
        }

    def get_update_data(self):
        return {
            'title': 'changed title',
            'text': 'changed text',
            'is_pro': False,
        }

    def test_create(self):
        response = super().test_create()
        self.assertEqual(response.data['created_by'], self.user.username)
        self.assertEqual(response.data['rating']['rating'], 3)  # default value

    def test_invalid_statement_id(self):
        data = self.get_create_data()
        data['statement_id'] = 999999999

        response = self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)
        self.assertTrue('statement_id' in response.data)

    def test_foreign_discussion(self):
        foreign_discussion = factories.SimpleDiscussionFactory.create()
        statement = foreign_discussion.statements.all()[0]
        data = self.get_create_data()
        data['statement_id'] = statement.id

        response = self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)
        self.assertTrue('statement_id' in response.data)

    def test_allowed_only_if_has_arguments(self):
        self.discussion.has_arguments = False
        self.discussion.save()

        data = self.get_create_data()
        self.create(data=data, status_code=status.HTTP_403_FORBIDDEN)

    def test_update_not_allowed_by_foreign_user(self):
        self.set_update_headers()
        foreign_user = factories.UserFactory.create()
        self.update(status_code=status.HTTP_403_FORBIDDEN, as_user=foreign_user)

    def test_update_only_if_not_changed(self):
        self.set_update_headers()
        argument = self.get_object()
        argument.last_related_activity = now()
        argument.save()

        response = self.client.patch(self.get_update_url(argument),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_allowed_by_admin(self):
        self.set_update_headers()
        user = factories.UserFactory.create()
        add_staff_permissions_to_user(user)
        self.client.as_user(user)
        argument = self.get_object()

        response = self.client.patch(self.get_update_url(argument),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # editing is even allowed after an related object has changed
        argument.last_related_update = now()
        argument.save()
        response = self.client.patch(self.get_update_url(argument),
                                     data=json.dumps(self.get_update_data()),
                                     content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_destroy_not_allowed_by_foreign_user(self):
        foreign_user = factories.UserFactory.create()
        self.destroy(status_code=status.HTTP_403_FORBIDDEN, as_user=foreign_user)

    def test_destroy_only_if_not_changed(self):
        self.set_destroy_headers()
        argument = self.get_object()
        argument.last_related_activity = now()
        argument.save()

        response = self.client.delete(self.get_destroy_url(argument))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_destroy_allowed_by_admin(self):
        self.set_destroy_headers()
        user = factories.UserFactory.create()
        add_staff_permissions_to_user(user)
        self.client.as_user(user)
        argument = self.get_object()

        response = self.client.delete(self.get_destroy_url(argument))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # editing is even allowed after an related object has changed
        argument.last_related_activity = now()
        argument.save()
        response = self.client.delete(self.get_destroy_url(argument))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ArgumentReplyAPITest(test.CreateTestMixin,
                           test.ListTestMixin,
                           test.BrabblAPITestCase):
    base_name = 'argument'

    create_required_fields = [
        'statement_id', 'title', 'text']  # TODO 'is_pro' should be required

    def setUp(self):
        super().setUp()
        self.discussion = factories.SimpleDiscussionFactory(customer=self.customer)
        self.statement = self.discussion.statements.all()[0]
        self.argument = factories.ArgumentFactory.create(statement=self.statement)

    def get_object(self):
        return factories.ArgumentFactory(
            statement=self.statement,
            reply_to=self.argument,
        )

    def get_create_data(self):
        return {
            'statement_id': self.statement.id,
            'reply_to': self.argument.id,
            'title': 'Dogs are creators',
            'text': 'Fusce egestas elit eget. Fusce egestas elit eget.',
            'is_pro': True
        }

    def get_list_url(self):
        url = self.get_create_url()
        return '{0}{1}/replies/'.format(url, self.argument.pk)

    def test_create(self):  # create reply
        response = self.get_list()
        self.assertEqual(len(response.data), 0)

        super().test_create()

        response = self.get_list()
        self.assertEqual(len(response.data), 1)


class ArgumentRatingAPITest(test.CreateTestMixin,
                            test.BrabblAPITestCase):
    base_name = 'argument'
    create_required_fields = [
        'rating']

    def setUp(self):
        super().setUp()
        self.discussion = factories.SimpleDiscussionFactory(customer=self.customer)
        self.statement = self.discussion.statements.all()[0]
        self.argument = factories.ArgumentFactory.create(
            statement=self.statement,
            created_by=self.statement.created_by,
        )

    def get_object(self):
        return self.argument

    def get_rating(self):
        return models.Rating.objects.create(
            argument=self.get_object(),
            user=self.user,
            value=2,
        )

    def get_create_url(self, argument=None):
        if not argument:
            argument = self.get_object()

        url = reverse('v1:{0}-detail'.format(self.base_name),
                      args=(argument.pk,))
        return '{0}rate/'.format(url)

    def get_create_data(self):
        return {
            'rating': 3,
        }

    def test_create(self):
        response = super().test_create()
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['rating'], 3)
        self.assertEqual(response.data['user_rating'], 3)

    def test_allow_only_valid_ratings(self):
        # invalid
        self.create(data={'rating': -1}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 0}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 0.5}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 1.2}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 5.5}, status_code=status.HTTP_400_BAD_REQUEST)
        self.create(data={'rating': 6}, status_code=status.HTTP_400_BAD_REQUEST)

        # valid
        self.create(data={'rating': 1}, status_code=status.HTTP_201_CREATED)
        self.create(data={'rating': 1.5}, status_code=status.HTTP_201_CREATED)
        self.create(data={'rating': 5}, status_code=status.HTTP_201_CREATED)

    def test_update_existing_rating(self):
        self.get_rating()
        response = self.create(data={'rating': 2})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['rating'], 2)
        self.assertEqual(response.data['user_rating'], 2)

    def test_mean_and_count(self):
        self.create(data={'rating': 3}, as_user=factories.UserFactory.create())
        self.create(data={'rating': 4.5}, as_user=factories.UserFactory.create())
        self.create(data={'rating': 1}, as_user=factories.UserFactory.create())
        response = self.create(
            data={'rating': 5}, as_user=factories.UserFactory.create())

        self.assertEqual(response.data['count'], 4)
        self.assertAlmostEqual(response.data['rating'], 3.4, 1)
        self.assertEqual(response.data['user_rating'], 5)  # value of last response

    def test_allowed_only_if_has_arguments(self):
        self.discussion.has_arguments = False
        self.discussion.save()
        self.create(data={'rating': 2}, status_code=status.HTTP_403_FORBIDDEN)


class FlagAPITest(test.CreateTestMixin,
                  test.BrabblAPITestCase):
    base_name = 'flag'
    create_status_code = status.HTTP_204_NO_CONTENT
    create_required_fields = [
        'id', 'type']

    def setUp(self):
        super().setUp()
        self.discussion = factories.SimpleDiscussionFactory(customer=self.customer)
        self.statement = self.discussion.statements.all()[0]
        self.argument = factories.ArgumentFactory.create(
            statement=self.statement,
            created_by=self.statement.created_by,
        )

    def get_create_data(self, ct='statement'):
        if ct == 'statement':
            return {
                'type': 'statement',
                'id': self.statement.id,
            }
        return {
            'type': 'argument',
            'id': self.argument.id,
        }

    def test_create(self):  # test_statement_flagging
        response = super().test_create()
        self.assertFalse(bool(response.data))
        self.assertEqual(self.statement.flags.count(), 1)

    def test_argument_flagging(self):
        data = self.get_create_data(ct='argument')
        self.create(data=data)
        self.assertEqual(self.argument.flags.count(), 1)

    def test_argument_flagging_notification_mail_sended(self):
        self.customer.flag_count_notification = 1
        self.customer.save()

        data = self.get_create_data(ct='argument')
        self.create(data=data)
        self.assertEqual(self.argument.flags.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_only_visible_can_be_flagged(self):
        self.statement.delete()
        self.argument.delete()

        data = self.get_create_data()
        self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)

        data = self.get_create_data(ct='argument')
        self.create(data=data, status_code=status.HTTP_400_BAD_REQUEST)

    def test_flagging_foreign_customer_not_allowed(self):
        customer = factories.CustomerFactory.create()
        self.discussion.customer = customer
        self.discussion.save()
        self.create(status_code=status.HTTP_404_NOT_FOUND)


class CustomerAPITest(test.RetrieveTestMixin, test.BrabblAPITestCase):
    base_name = 'customer'

    def get_retrieve_url(self, obj=None):
        return reverse('v1:customer')


class NotificationWordingAPITest(test.RetrieveTestMixin, test.BrabblAPITestCase):
    base_name = 'notification_wording'

    def setUp(self):
        super().setUp()
        self.wording = factories.NotificationWordingFactory()
        self.customer.notification_wording = self.wording.pk
        self.customer.save()

    def get_object(self, **properties):
        return self.wording
