from rest_framework import exceptions, serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Permission, Group
from django.db.models import Q
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from brabbl.utils.serializers import Base64ImageField


class UserAuthTokenSerializer(AuthTokenSerializer):
    def validate(self, attrs):
        username = attrs.get('username', '')
        password = attrs.get('password')

        if username and password:
            customer = self.context['request'].customer
            customer_username = '{}+{}'.format(username, customer.embed_token)

            user = authenticate(
                customer=customer,
                username=customer_username,
                password=password
            ) or authenticate(
                customer=customer,
                username=username,
                password=password
            )
            if user is None:
                users = get_user_model().objects.filter(
                    customer=customer, email=username
                )
                if users:
                    user = authenticate(
                        customer=customer,
                        username=users[0].username,
                        password=password
                    )
            if user:
                if not user.is_active:
                    msg = _("This account is inactive.")
                    raise exceptions.ValidationError(msg)
            else:
                msg = _("Password or user name is invalid.")
                raise exceptions.ValidationError(msg)
        else:
            msg = _("Username and password must be entered")
            raise exceptions.ValidationError(msg)

        attrs['user'] = user
        return attrs


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        style={'input_type': 'password'}, write_only=True)

    def validate_password(self, value):
        # TODO
        return value


class UserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, email):
        UserModel = get_user_model()
        try:
            user = UserModel._default_manager.get(
                customer=self.context['request'].customer,
                email__iexact=email)
        except UserModel.DoesNotExist:
            raise serializers.ValidationError(_("Unknown e-mail."))
        return email


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()  # define to be required
    permissions = serializers.SerializerMethodField()
    image = Base64ImageField()
    linked = serializers.SerializerMethodField()
    unlinked = serializers.SerializerMethodField()
    has_accepted_current_data_policy = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        exclude = ['password', 'last_login', 'is_superuser', 'is_staff', 'is_active', 'last_sent',
                   'activated_at', 'deleted_at', 'groups', 'user_permissions']
        read_only_fields = ('id', 'permissions', 'display_name', 'date_joined',
                            'has_accepted_current_data_policy')

    def get_field_names(self, declared_fields, info):
        """
        Hide additional fields during the customer user's info settings
        """
        fields = super().get_field_names(declared_fields, info)
        if self.instance:
            hidden_fields = self.instance.customer.model_properties.filter(
                show_in_profile=False
            ).values_list('key', flat=True)
            if len(hidden_fields) > 0:
                fields = list(set(fields) - set(hidden_fields))
        return fields

    def get_permissions(self, user):
        return Permission.objects.filter(
            Q(user=user) | Q(group__in=user.groups.all())
        ).values_list('codename', flat=True)

    def get_linked(self, user):
        return list(user.custom_social_auth.values_list('provider', 'id', 'uid'))

    def get_unlinked(self, user):
        return list(
            set(['twitter', 'google-oauth2', 'facebook']) - set(
                user.custom_social_auth.values_list('provider', flat=True))
        )

    def get_has_accepted_current_data_policy(self, obj):
        return obj.has_accepted_current_data_policy()

    def validate_email(self, value):
        query = get_user_model().objects.all()
        if self.instance:
            # exclude the current user from email duplicate check
            query = query.exclude(pk=self.instance.pk)

        try:
            query.get(
                email__iexact=value, customer=self.context['request'].customer
            )
        except get_user_model().DoesNotExist:
            return value
        except:
            pass

        raise serializers.ValidationError(
            _("This email address is already in use."))

    def validate_username(self, value):
        query = get_user_model().objects.all()
        if self.instance:
            # exclude the current user from email duplicate check
            query = query.exclude(pk=self.instance.pk)

        customer = self.context['request'].customer
        try:
            query.get(
                username__iexact='{}+{}'.format(value, customer.embed_token),
                customer=customer
            )
        except get_user_model().DoesNotExist:
            return value

        raise serializers.ValidationError(_("This username is not available."))

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'username' in ret:
            ret['username'] = ret['username'].rsplit('+', 1)[0]
            ret['display_name'] = instance.display_name
        return ret

    def update(self, instance, validated_data):
        customer = self.context['request'].customer
        for field in validated_data:
            if field == 'username':
                validated_data[field] += '+{}'.format(customer.embed_token)
            if field == 'image' and validated_data['image'].size < 1400:
                continue
            setattr(instance, field, validated_data[field])
        instance.save()
        return instance


class UserCreateSerializer(PasswordSerializer, UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = [
            'username', 'first_name', 'last_name', 'email', 'password',
        ]
        exclude = []

    def validate(self, attrs):
        # validate `unique_together manually to fully customize the error message
        customer = self.context['request'].customer
        User = self.Meta.model
        opts = User._meta
        for field_name in ['username', 'email']:
            field_label = capfirst(opts.get_field(field_name).verbose_name)
            if field_name == 'username' and attrs.get(field_name):
                attrs[field_name] += '+{}'.format(customer.embed_token)
            try:
                User.objects.get(**{'customer': customer,
                                    field_name: attrs[field_name]})
            except User.DoesNotExist:
                pass
            else:
                raise serializers.ValidationError(
                    _("{0} is already in use.").format(field_label))
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        password = validated_data.pop('password')

        # add current customer
        validated_data.update({'customer': request.customer})
        validated_data['is_confirmed'] = False
        User = get_user_model()
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        user.send_verification_mail(
            request.customer,
            source_url=request.META.get('HTTP_REFERER')
        )

        return user


class UserTokenIdentifierSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        User = get_user_model()
        token = attrs['token']

        try:
            attrs['user'] = User.objects.user_from_token(token)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError(
                _("Auth token is not valid."))
        return attrs


class FormToSerializerBooleanField(serializers.BooleanField):
    TRUE_VALUES = set(('t', 'T', 'true', 'True', 'TRUE', '1', 1, True, 'On', 'on', 'ON'))
    FALSE_VALUES = set(('f', 'F', 'false', 'False', 'FALSE', '0', 0, 0.0, False, 'Off', 'off', 'OFF'))


class UserListUpdateSerializer(serializers.Serializer):
    group = serializers.IntegerField(allow_null=True)
    is_confirmed = FormToSerializerBooleanField()
    is_active = FormToSerializerBooleanField()
    user_id = serializers.IntegerField()

    def validate(self, attrs):
        if 'group' in attrs and attrs['group']:
            try:
                attrs['group'] = [Group.objects.get(pk=int(attrs['group']))]
            except Group.DoesNotExist:
                raise serializers.ValidationError(
                    _("Group doesn't exist."))
        else:
            attrs['group'] = []
        return attrs
