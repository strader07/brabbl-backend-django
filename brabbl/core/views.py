from rest_framework import mixins, viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import detail_route
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _

from brabbl.accounts.models import Customer, EmailGroup, EmailTemplate
from brabbl.utils.serializers import MultipleSerializersViewMixin
from brabbl.utils.language_utils import frontend_interface_messages
from . import serializers, models, permissions


class TagViewSet(mixins.CreateModelMixin,
                 mixins.ListModelMixin,
                 viewsets.GenericViewSet):
    serializer_class = serializers.TagSerializer
    permission_classes = [permissions.StaffOnlyWritePermission]

    def get_queryset(self):
        return models.Tag.objects.for_customer(self.request.customer)


class WordingViewSet(mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    serializer_class = serializers.WordingSerializer

    def get_queryset(self):
        return models.Wording.objects.for_customer(self.request.customer).order_by('name')


class NotificationWordingViewSet(mixins.RetrieveModelMixin,
                                 viewsets.GenericViewSet):
    serializer_class = serializers.NotificationWordingSerializer

    def get_queryset(self):
        return models.NotificationWording.objects.filter(pk=self.request.customer.notification_wording)


class DiscussionListViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin,
                            viewsets.GenericViewSet):
    permission_classes = [permissions.StaffOnlyWritePermission]
    serializer_class = serializers.DiscussionListSerializer
    queryset = models.DiscussionList.objects.all()
    lookup_field = 'url'

    def get_object(self):
        """
        Gets the discussion by the external id passed in through the `external_id`
        request parameter.
        """
        queryset = self.filter_queryset(self.get_queryset())

        obj = get_object_or_404(
            queryset, url=self.request.GET.get('url'))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def retrieve(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        try:
            instance = queryset.get(url=self.request.GET.get('url'))
        except models.DiscussionList.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DiscussionViewSet(MultipleSerializersViewMixin,
                        viewsets.ModelViewSet):
    permission_classes = [permissions.StaffOnlyWritePermission]
    serializer_class = serializers.DiscussionSerializer
    list_serializer_class = serializers.ListDiscussionSerializer
    update_serializer_class = serializers.UpdateDiscussionSerializer

    def get_object(self):
        """
        Gets the discussion by the external id passed in through the `external_id`
        request parameter.
        """
        queryset = self.filter_queryset(self.get_queryset())

        obj = get_object_or_404(
            queryset, external_id=self.request.GET.get('external_id'))

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        return models.Discussion.objects.for_customer(self.request.customer).visible()

    def partial_update(self, request, pk=None):
        current_multiple = request.data.get('multiple_statements_allowed')
        obj = self.get_object()
        if obj.multiple_statements_allowed and not current_multiple:
            models.Statement.objects.create(
                discussion=obj, created_by=request.user,
            )
        elif not obj.multiple_statements_allowed and current_multiple:
            statements = obj.statements.filter(statement='')
            if statements:
                statements[0].delete()
        return super().partial_update(request, pk=pk)


class StatementViewSet(MultipleSerializersViewMixin,
                       viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly,
                          permissions.ActivityBasedObjectPermission,
                          permissions.OwnershipObjectPermission]
    serializer_class = serializers.StatementSerializer
    update_serializer_class = serializers.UpdateStatementSerializer

    def get_queryset(self):
        return models.Statement.objects.for_customer(self.request.customer).visible()

    def perform_create(self, serializer):
        # we need to verify that it is allowed to create a new statement
        external_id = serializer.validated_data['discussion']['external_id']
        discussion = models.Discussion.objects.get(
            customer=self.request.customer, external_id=external_id)
        # check that only staff can add suggestions if user_can_add_replies is False
        if not discussion.multiple_statements_allowed:
            raise PermissionDenied()
        if not discussion.user_can_add_replies:
            if not (self.request.user.is_active and self.request.user.has_perm('core.add_statement')):
                raise PermissionDenied()
        super().perform_create(serializer)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def vote(self, request, **kwargs):
        serializer = serializers.VoteSerializer(
            data=request.data,
            context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        statement = self.get_object()
        if not statement.discussion.has_barometer:
            raise PermissionDenied(_("Discussion has no barometer."))

        user = request.user

        try:
            vote = statement.barometer_votes.get(user=user)
        except models.BarometerVote.DoesNotExist:
            vote = models.BarometerVote.objects.create(
                statement=statement,
                user=user,
                value=serializer.validated_data['rating']
            )
        else:
            vote.value = serializer.validated_data['rating']
            vote.save()

        # refresh current statement
        statement = models.Statement.objects.get(id=statement.id)

        return Response(
            serializers.BarometerSerializer(
                statement, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @detail_route(
        methods=['post'],
        permission_classes=[permissions.StaffOnlyWritePermission]
    )
    def change_status(self, request, **kwargs):
        serializer = serializers.StatusSerializer(
            data=request.data, context={'request': request}
        )
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        statement = self.get_object()
        statement.status = serializer.validated_data['status']
        statement.save()

        return Response(
            {"status": statement.status}, status=status.HTTP_200_OK
        )


class ArgumentViewSet(MultipleSerializersViewMixin,
                      viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly,
                          permissions.ActivityBasedObjectPermission,
                          permissions.OwnershipObjectPermission]
    serializer_class = serializers.ArgumentSerializer
    update_serializer_class = serializers.UpdateArgumentSerializer

    def get_queryset(self):
        qs = models.Argument.objects.for_customer(self.request.customer)
        if self.request.method not in ['DELETE', 'PATCH', 'POST']:
            qs = qs.without_replies().visible()
        return qs

    @detail_route(methods=['get'])
    def replies(self, request, **kwargs):
        argument = self.get_object()
        serializer = serializers.ArgumentSerializer(argument.replies.visible(), many=True,
                                                    context=self.get_serializer_context())
        return Response(serializer.data)

    @detail_route(methods=['post'], permission_classes=[IsAuthenticatedOrReadOnly])
    def rate(self, request, **kwargs):
        serializer = serializers.RatingSerializer(
            data=request.data,
            context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        argument = self.get_object()
        if not argument.statement.discussion.has_arguments:
            raise PermissionDenied(_("Discussion has no arguments."))

        if argument.status == models.Argument.STATUS_HIDDEN:
            raise ValidationError(_("You can not rate hidden argument"))

        user = request.user

        models.Rating.objects.update_or_create(
            user=user, argument=argument,
            defaults={'value': serializer.validated_data['rating']}
        )

        # refresh current Argument
        argument = models.Argument.objects.get(id=argument.id)

        return Response(
            serializers.ArgumentRatingSerializer(
                argument, context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @detail_route(methods=['post'], permission_classes=[permissions.StaffOnlyWritePermission])
    def change_status(self, request, **kwargs):
        serializer = serializers.StatusSerializer(
            data=request.data,
            context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        argument = self.get_object()
        argument.status = serializer.validated_data['status']
        argument.save()

        return Response(
            {"status": argument.status},
            status=status.HTTP_200_OK,
        )


class FlagAPIView(mixins.CreateModelMixin,
                  viewsets.GenericViewSet):
    model = models.Flag
    serializer_class = serializers.FlaggingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        # this method is identical to `CreateModelMixin.create`
        # except for an empty response
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TranslationAPIView(APIView):
    """
    View for frontend i18n.
    """

    def get(self, request):
        """
        Return frontend's interface messages with translations.
        """
        return Response(frontend_interface_messages())


class CustomerAPIView(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = serializers.CustomerSerializer
    model = Customer

    def get_object(self):
        """
        Returns customer object
        It is available in request for authenticated frontend application
        """
        return self.request.customer


class DuplicateObject(View):
    """
    Duplicate Object View. Only staff allowed (see urls config)
    """

    def get(self, request, model, pk):
        """
        Get request.
        :param request: request
        :param model: name of model
        :param pk: pk of duplicated object
        """
        if model == 'wording':
            obj = get_object_or_404(models.Wording, pk=pk)
            words = obj.words.all()
            obj.pk = None
            obj.name = "{} New".format(obj.name)
            obj.save()
            words_copy = []
            for word in words:
                word.pk = None
                word.wording = obj
                words_copy.append(word)
            models.WordingValue.objects.bulk_create(words_copy)
            redirect_url = "/admin/core/wording/%s/"
        elif model == 'notificationwording':
            obj = get_object_or_404(models.NotificationWording, pk=pk)
            messages = obj.model_properties.all()
            markdown_messages = obj.model_markdown_properties.all()
            obj.pk = None
            obj.name = "{} New".format(obj.name)
            obj.save()
            # delete automaticaly added properties
            models.NotificationWordingMessage.objects.filter(property_model=obj.pk).delete()
            models.MarkdownWordingMessage.objects.filter(property_model=obj.pk).delete()
            messages_copy = []
            for message in messages:
                message.pk = None
                message.property_model = obj
                messages_copy.append(message)
            models.NotificationWordingMessage.objects.bulk_create(messages_copy)
            markdown_messages_copy = []
            for message in markdown_messages:
                message.pk = None
                message.property_model = obj
                markdown_messages_copy.append(message)
            models.MarkdownWordingMessage.objects.bulk_create(markdown_messages_copy)
            redirect_url = "/admin/core/notificationwording/%s/"
        elif model == 'emailgroup':
            obj = get_object_or_404(EmailGroup, pk=pk)
            emails = obj.emailtemplate_set.all()
            obj.pk = None
            obj.name = "{} New".format(obj.name)
            obj.save()
            emails_copy = []
            for email in emails:
                email.pk = None
                email.email_group = obj
                emails_copy.append(email)
            EmailTemplate.objects.bulk_create(emails_copy)
            redirect_url = "/admin/accounts/emailgroup/%s/"

        return redirect(redirect_url % obj.pk)
