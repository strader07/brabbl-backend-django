from embed_video.backends import YoutubeBackend
from rest_framework import exceptions, serializers

from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from brabbl.accounts.models import Customer, CustomerUserInfoSettings
from brabbl.utils.models import get_thumbnail_url
from brabbl.utils.serializers import (
    Base64ImageField, NonNullSerializerMixin, PermissionSerializerMixin
)
from . import models


class TagListField(serializers.ListField):
    child = serializers.CharField()

    def to_representation(self, qs):
        return [tag.name for tag in qs.all()]

    def to_internal_value(self, data):
        customer = self.context['request'].customer
        tags = []
        for tag in data:
            tag, __ = models.Tag.objects.get_or_create(
                customer=customer,
                name=tag)
            tags.append(tag)
        return tags


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('id', 'name')
        read_only_fields = ('id',)

    def create(self, validated_data):
        validated_data.update({
            'customer': self.context['request'].customer,
        })
        return super().create(validated_data)


class WordingValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.WordingValue
        fields = ('name', 'value')


class WordingSerializer(serializers.ModelSerializer):
    words = WordingValueSerializer(many=True)

    class Meta:
        model = models.Wording
        exclude = ('language', 'customer')


class NotificationWordingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.NotificationWordingMessage
        fields = ('key', 'value')


class MarkdownWordingMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.MarkdownWordingMessage
        fields = ('key', 'value')


class NotificationWordingSerializer(serializers.ModelSerializer):
    notification_wording_messages = NotificationWordingMessageSerializer(
        many=True, source='model_properties'
    )
    markdown_wording_messages = MarkdownWordingMessageSerializer(
        many=True, source='model_markdown_properties'
    )

    class Meta:
        model = models.NotificationWording
        fields = '__all__'


class RatingSerializer(serializers.Serializer):
    rating = serializers.FloatField(min_value=1, max_value=5)

    def validate_rating(self, rating):
        decimal = rating * 10 % 10
        if decimal != 0 and decimal != 5:
            raise serializers.ValidationError(
                _("There are only whole or half numbers allowed."))

        return rating


class StatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=models.Argument.LIST_OF_STATUSES)


class ArgumentRatingSerializer(NonNullSerializerMixin, serializers.ModelSerializer):
    count = serializers.IntegerField(source='rating_count')
    rating = serializers.FloatField(source='rating_value')
    user_rating = serializers.SerializerMethodField()

    class Meta:
        model = models.BarometerVote
        fields = ('count', 'rating', 'user_rating')
        read_only_fields = ('count', 'rating', 'user_rating')

    def get_user_rating(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return None

        try:
            rating = obj.ratings.get(user=user)
        except models.Rating.DoesNotExist:
            return None
        return rating.value


class ArgumentSerializer(PermissionSerializerMixin, serializers.ModelSerializer):
    statement_id = serializers.IntegerField(source='statement.id', required=True)
    created_by = serializers.CharField(source='created_by.display_name', read_only=True)
    rating = serializers.FloatField(source='rating_value', read_only=True)
    is_pro = serializers.BooleanField(required=True)
    # NOTE: queryset will be restricted in `get_fields`
    reply_to = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=models.Argument.objects.visible())
    rating = serializers.SerializerMethodField()

    class Meta:
        model = models.Argument
        fields = (
            'id', 'created_at', 'created_by', 'is_pro', 'title', 'statement_id',
            'text', 'rating', 'reply_count', 'reply_to', 'is_editable', 'is_deletable', 'status')
        read_only_fields = (
            'id', 'created_at', 'created_by', 'rating', 'reply_count')

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        # PrimaryKeyRelatedField requires a queryset
        # But since we have no access to the customer while constructing,
        # we have to override the queryset here.
        customer = self.context['request'].customer
        qs = models.Argument.objects.for_customer(customer).visible()
        fields['reply_to'].queryset = qs
        return fields

    def get_rating(self, obj):
        return ArgumentRatingSerializer(obj, context=self.context).data

    def get_reply_count(self, obj):
        return obj.replies.visible().count()

    def validate_reply_to(self, reply_to):
        return reply_to

    def validate_statement_id(self, statement_id):
        customer = self.context['request'].customer

        try:
            models.Statement.objects.for_customer(customer).get(id=statement_id)
        except models.Statement.DoesNotExist:
            raise exceptions.ValidationError(_("Statement not found"))

        return statement_id

    def create(self, validated_data):
        customer = self.context['request'].customer
        user = self.context['request'].user
        statement_id = validated_data['statement']['id']
        del validated_data['statement']

        statement = models.Statement.objects.for_customer(customer).get(
            id=statement_id)

        if not statement.discussion.has_arguments:
            raise exceptions.PermissionDenied(
                _("Arguments are not allowed in this discussion."))

        if 'reply_to' in validated_data and not statement.discussion.has_replies:
            raise exceptions.PermissionDenied(
                _("Replies are not allowed in this discussion."))

        return models.Argument.objects.create(
            statement=statement,
            created_by=user,
            **validated_data
        )


class UpdateArgumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Argument
        fields = ('title', 'text', 'is_pro')


class VoteSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=-3, max_value=3)


class BarometerSerializer(NonNullSerializerMixin, serializers.ModelSerializer):
    wording = WordingValueSerializer(
        source='discussion.barometer_wording.words', many=True
    )
    count = serializers.IntegerField(source='barometer_count')
    rating = serializers.FloatField(source='barometer_value')
    user_rating = serializers.SerializerMethodField()
    count_ratings = serializers.SerializerMethodField()

    class Meta:
        model = models.BarometerVote
        fields = ('count', 'rating', 'user_rating', 'count_ratings', 'wording')
        read_only_fields = (
            'count', 'rating', 'user_rating', 'count_ratings', 'wording'
        )

    def get_user_rating(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return None

        try:
            rating = obj.barometer_votes.get(user=user)
        except models.BarometerVote.DoesNotExist:
            return None
        return rating.value

    def get_count_ratings(self, obj):
        ratings = list(obj.barometer_votes.order_by('value').values_list(
            'value', flat=True
        ))
        return {value: ratings.count(value) for value in range(-3, 4)}


class StatementSerializer(NonNullSerializerMixin,
                          PermissionSerializerMixin,
                          serializers.ModelSerializer):
    created_by = serializers.CharField(source='created_by.display_name', read_only=True)
    discussion_id = serializers.CharField(source='discussion.external_id', required=True)
    statement = serializers.CharField(required=True)
    arguments = serializers.SerializerMethodField()
    barometer = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)

    class Meta:
        model = models.Statement
        fields = ('id', 'discussion_id', 'created_by', 'statement', 'created_at',
                  'arguments', 'barometer', 'is_editable', 'image', 'video',
                  'thumbnail', 'is_deletable', 'status', )
        read_only_fields = ('id', 'created_by', 'created_at', 'discussion_id',
                            'arguments', 'barometer')

    def get_arguments(self, statement):
        arguments = statement.arguments.visible().without_replies()
        serializer = ArgumentSerializer(arguments, many=True, context=self.context)
        return serializer.data

    def get_barometer(self, statement):
        if statement.discussion.has_barometer:
            return BarometerSerializer(statement, context=self.context).data
        return None

    def validate_discussion_id(self, discussion_id):
        customer = self.context['request'].customer

        try:
            models.Discussion.objects.get(
                customer=customer, external_id=discussion_id)
        except models.Discussion.DoesNotExist:
            raise exceptions.ValidationError(_("Discussion not found﻿"))

        return discussion_id

    def create(self, validated_data):
        customer = self.context['request'].customer
        user = self.context['request'].user
        discussion_id = validated_data['discussion']['external_id']
        del validated_data['discussion']

        discussion = models.Discussion.objects.get(
            customer=customer, external_id=discussion_id)

        return models.Statement.objects.create(
            discussion=discussion,
            created_by=user,
            **validated_data
        )

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'video' in ret and ret['video']:
            ret['video'] = YoutubeBackend(ret['video']).get_code()
        return ret


class UpdateStatementSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False)

    class Meta:
        model = models.Statement
        fields = ('statement', 'image', 'video')


class DiscussionListSerializer(PermissionSerializerMixin, serializers.ModelSerializer):
    tags = TagListField()

    class Meta:
        exclude = ('created_at', 'modified_at', 'deleted_at')
        model = models.DiscussionList


class BaseDiscussionSerializer(PermissionSerializerMixin, serializers.Serializer):
    url = serializers.URLField(source='source_url')
    created_by = serializers.CharField(source='created_by.display_name', read_only=True)
    tags = TagListField()

    def get_image_url(self, discussion):
        url = discussion.image_url
        if discussion.image and discussion.image.size > 2000:
            url = get_thumbnail_url(discussion.image, {'size': (300, 200), 'crop': True})
        return url


class ListDiscussionSerializer(NonNullSerializerMixin,
                               BaseDiscussionSerializer,
                               serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    barometer = serializers.SerializerMethodField()

    class Meta:
        model = models.Discussion
        fields = ('external_id', 'url', 'created_by', 'created_at', 'image_url',
                  'last_activity', 'tags', 'multiple_statements_allowed', 'statement',
                  'has_barometer', 'has_arguments', 'has_replies', 'barometer_wording',
                  'user_can_add_replies', 'argument_count', 'statement_count',
                  'is_editable', 'is_deletable', 'barometer', 'start_time',
                  'end_time', 'statements', )
        read_only_fields = fields

    def get_barometer(self, discussion):
        if discussion.has_barometer and not discussion.multiple_statements_allowed:
            statement = discussion.statements.first()
            if statement:
                return BarometerSerializer(statement, context=self.context).data
        return None


class DiscussionSerializer(BaseDiscussionSerializer, serializers.ModelSerializer):
    statements = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)
    image_url = serializers.SerializerMethodField()

    # NOTE: queryset will be restricted in `get_fields`
    wording = serializers.PrimaryKeyRelatedField(
        queryset=models.Wording.objects.all(),
        required=False, write_only=True,
        source='barometer_wording')

    class Meta:
        model = models.Discussion
        fields = ('external_id', 'created_by', 'created_at',
                  'url', 'tags',
                  'statement', 'statements', 'wording',
                  'multiple_statements_allowed', 'user_can_add_replies',
                  'has_barometer', 'has_arguments', 'has_replies', 'barometer_wording',
                  'is_editable', 'is_deletable', 'start_time', 'image', 'image_url',
                  'end_time')
        read_only_fields = ('created_by', 'statements')

    def get_fields(self, *args, **kwargs):
        fields = super().get_fields(*args, **kwargs)
        # PrimaryKeyRelatedField requires a queryset
        # But since we have no access to the customer while constructing,
        # we have to override the queryset here.
        customer = self.context['request'].customer
        qs = models.Wording.objects.for_customer(customer)
        fields['wording'].queryset = qs
        return fields

    def get_statements(self, discussion):
        statements = discussion.statements.visible()
        serializer = StatementSerializer(statements, many=True, context=self.context)
        return serializer.data

    def validate_external_id(self, external_id):
        customer = self.context['request'].customer

        if external_id:
            external_id = external_id.split("#")[0]
            try:
                models.Discussion.objects.get(
                    customer=customer, external_id=external_id)
            except models.Discussion.DoesNotExist:
                pass
            except:
                raise exceptions.ValidationError(_("ID is already in use."))

        return external_id

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Validate barometer required
        if attrs['has_barometer'] and not attrs.get('barometer_wording'):
            raise exceptions.ValidationError(_("`Wording` needed for Barometer."))

        # Validate date range
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")
        if start_time and end_time:
            if end_time < start_time:
                raise exceptions.ValidationError(
                    {'start_time': "End time cannot be earlier than start time!"}
                )
        return attrs

    def create(self, validated_data):
        customer = self.context['request'].customer
        user = self.context['request'].user
        tags = validated_data['tags']
        del validated_data['tags']

        discussion = models.Discussion.objects.create(
            customer=customer,
            created_by=user,
            **validated_data
        )

        # add tags
        for tag in tags:
            discussion.tags.add(tag)

        # create corresponding Statement
        if not discussion.multiple_statements_allowed:
            models.Statement.objects.create(
                discussion=discussion,
                created_by=user,
            )

        return discussion


class UpdateDiscussionSerializer(serializers.ModelSerializer):
    url = serializers.URLField(source='source_url')
    tags = TagListField()
    image = Base64ImageField(required=False)

    # TODO limit queryset!
    wording = serializers.PrimaryKeyRelatedField(
        queryset=models.Wording.objects.all(),
        required=False, write_only=True,
        source='barometer_wording')

    class Meta:
        model = models.Discussion
        fields = ('url', 'tags',
                  'statement', 'wording',
                  'multiple_statements_allowed', 'user_can_add_replies',
                  'has_barometer', 'has_arguments', 'has_replies', 'start_time',
                  'end_time', 'image')

    def validate(self, attrs):
        attrs = super().validate(attrs)
        # Validate date range
        start_time = attrs.get("start_time")
        end_time = attrs.get("end_time")

        if start_time and end_time:
            if end_time < start_time:
                raise exceptions.ValidationError(
                    {'start_time': "End time cannot be earlier than start time!"}
                )
        return attrs

    def update(self, instance, validated_data):
        statements = instance.statements
        if validated_data.get('multiple_statements_allowed') \
                and statements.filter(statement='').count() == 1:
            statements.delete()
        elif not validated_data.get('multiple_statements_allowed') \
                and statements.count() == 0:
            models.Statement.objects.create(
                discussion=instance, created_by=self.context['request'].user,
            )
        return super(UpdateDiscussionSerializer, self).update(
            instance, validated_data
        )


class FlaggingSerializer(serializers.Serializer):
    ARGUMENT = 'argument'
    STATEMENT = 'statement'
    TYPE_CHOICES = (
        (ARGUMENT, "Argument"),
        (STATEMENT, "Statement"),
    )

    id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=TYPE_CHOICES)

    class Meta:
        fields = ('id', 'type')

    def validate(self, attrs):
        if attrs['type'] == self.ARGUMENT:
            model = models.Argument
        elif attrs['type'] == self.STATEMENT:
            model = models.Statement
        attrs['model'] = model

        # object should exist
        customer = self.context['request'].customer
        try:
            attrs['to_flag'] = model.objects.for_customer(customer)
            attrs['to_flag'] = attrs['to_flag'].visible().get(id=attrs['id'])
        except model.DoesNotExist:
            raise exceptions.NotFound()

        return attrs

    def create(self, validated_data):
        user = self.context['request'].user

        flag, _ = models.Flag.objects.get_or_create(
            content_type=ContentType.objects.get_for_model(validated_data['model']),
            object_id=validated_data['id'],
            user=user)

        return flag


class CustomerUserInfoSettingsSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomerUserInfoSettings
        exclude = ('id', 'property_model')


class CustomerSerializer(serializers.ModelSerializer):
    user_info_settings = CustomerUserInfoSettingsSerializer(many=True, source='model_properties')
    data_policy_link = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ('language', 'default_back_link', 'default_back_title', 'default_wording', 'default_has_replies',
                  'notification_wording', 'user_info_settings', 'theme', 'displayed_username', 'data_policy_link')

    def get_data_policy_link(self, obj):
        if obj.data_policy_version:
            return obj.data_policy_version.link
        else:
            return ''
