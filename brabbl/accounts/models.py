import six
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group
from django.urls import reverse
from django.core.validators import MaxLengthValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404

from social_django.models import USER_MODEL, UID_LENGTH
from social_django.storage import DjangoUserMixin
from social_django.fields import JSONField

from brabbl.utils import logger
from brabbl.utils import mail
from brabbl.utils.models import TimestampedModelMixin, SetOfPropertiesMixin
from brabbl.utils.string import random_string
from brabbl.accounts import managers


class SocialAuthMixin(object):
    @classmethod
    def get_social_auth(cls, provider, uid, customer):
        if isinstance(customer, (str, bytes,)):
            customer = get_object_or_404(Customer, embed_token=customer)
        try:
            return cls.objects.select_related('user').get(
                provider=provider, uid=uid, customer=customer
            )
        except UserSocialAuth.DoesNotExist:
            return None

    @classmethod
    def create_social_auth(cls, user, uid, provider):
        if not isinstance(uid, six.string_types):
            uid = str(uid)
        return cls.objects.create(
            user=user, uid=uid, provider=provider, customer=user.customer
        )

    @classmethod
    def username_max_length(cls):
        username_field = cls.username_field()
        field = UserSocialAuth.user_model()._meta.get_field(username_field)
        return field.max_length

    @classmethod
    def user_model(cls):
        user_model = UserSocialAuth._meta.get_field('user').related_model
        if isinstance(user_model, six.string_types):
            app_label, model_name = user_model.split('.')
            return models.get_model(app_label, model_name)
        return user_model

    @classmethod
    def get_social_auth_for_user(cls, user, provider=None, id=None):
        qs = user.custom_social_auth.all()
        if provider:
            qs = qs.filter(provider=provider)
        if id:
            qs = qs.filter(id=id)
        return qs

    @classmethod
    def get_users_by_email(cls, email, customer):
        """Return users instances for given email address"""
        return User.objects.filter(email=email, customer=customer)


class UserSocialAuth(models.Model, SocialAuthMixin, DjangoUserMixin):
    """Social Auth association model"""
    user = models.ForeignKey(
        USER_MODEL, related_name='custom_social_auth', on_delete=models.CASCADE)
    customer = models.ForeignKey(
        'Customer', related_name='customer_social_auth', on_delete=models.CASCADE)
    provider = models.CharField(max_length=32)
    uid = models.CharField(max_length=UID_LENGTH)
    extra_data = JSONField()

    def __str__(self):
        return str(self.user)

    class Meta:
        unique_together = ('provider', 'uid', 'customer')
        db_table = 'accounts_usersocialauth'


class CustomerUserInfoSettings(models.Model):
    FIELD_LIST = [
        ('first_name', _("First Name")),
        ('last_name', _("Last Name")),
        ('year_of_birth', _("Year of birth")),
        ('gender', _("Gender")),
        ('postcode', _("Postcode")),
        ('country', _("Country")),
        ('city', _("City")),
        ('organization', _("Organization")),
        ('position', _("Position")),
        ('bundesland', _("Bundesland")),
    ]
    key = models.CharField(max_length=64, db_index=True)
    property_model = models.ForeignKey(
        "Customer", related_name='model_properties', on_delete=models.CASCADE)
    show_in_profile = models.BooleanField(default=False)
    show_in_welcome = models.BooleanField(default=False)
    is_required = models.BooleanField(default=False)

    def __str__(self):
        return str(dict(CustomerUserInfoSettings.FIELD_LIST).get(self.key, 'None'))


class DataPolicy(models.Model):
    title = models.CharField(max_length=600)
    text = models.TextField(null=True, blank=True)
    link = models.URLField(blank=True)
    version_number = models.DecimalField(default=1.0, decimal_places=2, max_digits=6,
                                         unique=True)

    class Meta:
        verbose_name = 'Datenschutz-Richtlinie'
        verbose_name_plural = 'Datenschutz-Richtlinien'

    def __str__(self):
        return '{}_{}'.format(self.version_number, self.link)


class DataPolicyAgreement(models.Model):
    user = models.ForeignKey(
        'accounts.User', related_name='datapolicyagreements', on_delete=models.CASCADE)
    data_policy = models.ForeignKey(DataPolicy, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name='IP-Adresse')
    date_accepted = models.DateTimeField(verbose_name='Zustimmung am')

    class Meta:
        get_latest_by = 'date_accepted'
        verbose_name = 'Datenschutz-Zustimmung'
        verbose_name_plural = 'Datenschutz-Zustimmungen'
        unique_together = ('user', 'data_policy',)

    def __str__(self):
        return '{}_{}_{}'.format(
            self.data_policy.version_number, self.user, self.user.customer)


class Customer(TimestampedModelMixin, SetOfPropertiesMixin, models.Model):
    def __init__(self, *args, **kwargs):
        from brabbl.core.models import Wording, NotificationWording
        super(Customer, self).__init__(*args, **kwargs)
        choices = [(0, '---------')]
        for wording in Wording.objects.filter(Q(customer_id=None) | Q(customer=self)):
            choices.append((wording.pk, wording.name))
        self._meta.get_field('default_wording')._choices = choices
        notification_choices = [(0, '---------')]
        for n_wording in NotificationWording.objects.all():
            notification_choices.append((n_wording.pk, n_wording.name))
        self._meta.get_field('notification_wording')._choices = notification_choices

    name = models.CharField(max_length=1024)
    embed_token = models.CharField(max_length=64, unique=True)
    flag_count_notification = models.IntegerField(default=10)

    allowed_domains = models.TextField(
        help_text=_("One domain per line."))
    moderator_email = models.EmailField()
    _replyto_email = models.EmailField(
        _("ReplyTo email"),
        blank=True,
        help_text=_(
            "If left empty, the address of the moderator will be used."
        )
    )
    user_groups = models.ManyToManyField(Group, blank=True)
    default_wording = models.IntegerField(default=0)
    notification_wording = models.IntegerField(default=0)
    language = models.CharField(
        max_length=2,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE
    )
    email_group = models.ForeignKey(
        "EmailGroup", blank=True, null=True, default=None, on_delete=models.CASCADE)
    default_back_link = models.URLField(max_length=128, blank=True, default='')
    default_back_title = models.CharField(max_length=64, blank=True, default='')

    default_has_replies = models.BooleanField(default=True)
    # User Info Settings
    DISPLAY_USERNAME = 1
    DISPLAY_NAME_LAST_NAME = 2
    displayed_username = models.IntegerField(
        default=DISPLAY_USERNAME, choices=(
            (DISPLAY_USERNAME, _("Username")),
            (DISPLAY_NAME_LAST_NAME, _("First name + Last name"))
        )
    )
    THEME_BJV = 'bjv'
    THEME_BRABBL = 'brabbl'
    THEME_EYP = 'eyp'
    THEME_VORWAERTS = 'vorwaerts'
    THEME_JUGENDINFO = 'jugendinfo'
    THEME_LIST = [
        (THEME_BJV, THEME_BJV.title()),
        (THEME_BRABBL, THEME_BRABBL.title()),
        (THEME_EYP, THEME_EYP.title()),
        (THEME_VORWAERTS, THEME_VORWAERTS.title()),
        (THEME_JUGENDINFO, THEME_JUGENDINFO.title()),
    ]
    theme = models.CharField(max_length=24, default=THEME_BRABBL, choices=THEME_LIST)

    objects = managers.CustomerQuerySet.as_manager()
    property_model = CustomerUserInfoSettings
    data_policy_version = models.ForeignKey(
        DataPolicy, blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.embed_token:
            self.embed_token = random_string(size=32)
        super().save(**kwargs)

    @property
    def domain(self):
        return self.allowed_domains.splitlines()[0]

    @property
    def replyto_email(self):
        return self._replyto_email or self.moderator_email

    def send_flag_notification(self, obj):
        title = ''
        try:
            title = obj.title
        except AttributeError:
            try:
                title = obj.statement
            except AttributeError:  # pragma: no cover
                logger.error('Could not find `title` for object %s with id %s',
                             obj.__class__.__name__, obj.pk)

        mail.send_template(self.moderator_email, self, mail.TYPE_FLAGGING,
                           context={'customer': self,
                                    'type': obj.__class__.__name__,
                                    'obj': obj,
                                    'title': title,
                                    'flag_count': obj.flags.count()})


class User(AbstractUser):

    NEVER = 0
    DAILY = 1
    WEEKLY = 7
    NEWSMAIL_OPTIONS = (
        (NEVER, 'never'),
        (DAILY, 'daily'),
        (WEEKLY, 'weekly'),
    )
    GENDER_WHATEVER = 0
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_LIST = (
        (GENDER_WHATEVER, _("Whatever")),
        (GENDER_MALE, _("Male")),
        (GENDER_FEMALE, _("Female"))
    )
    BUNDESLAND_LIST = (
        ("AT-1", "Burgenland"),
        ("AT-2", "Kärnten"),
        ("AT-3", "Niederösterreich"),
        ("AT-4", "Oberösterreich"),
        ("AT-5", "Salzburg"),
        ("AT-6", "Steiermark"),
        ("AT-7", "Tirol"),
        ("AT-8", "Vorarlberg"),
        ("AT-9", "Wien"),
        ("-", "Anders Land"),
    )

    newsmail_schedule = models.IntegerField(choices=NEWSMAIL_OPTIONS,
                                            default=NEVER)
    last_sent = models.DateTimeField(_("Latest news mail delivery"), null=True,
                                     auto_now_add=True, )
    activated_at = models.DateTimeField(
        _("Date of activation"), blank=True, null=True, editable=False
    )
    deleted_at = models.DateTimeField(
        _("Deletion date"), blank=True, null=True, editable=False
    )
    customer = models.ForeignKey(
        Customer, blank=True, null=True, on_delete=models.CASCADE)
    image = models.ImageField(_("Profile picture"), null=True, blank=True,
                              upload_to='images/profiles/')
    # Additional info
    year_of_birth = models.PositiveSmallIntegerField(
        blank=True, null=True, default=None
    )
    postcode = models.CharField(
        max_length=128, blank=True, null=True, default=''
    )
    city = models.CharField(max_length=128, blank=True, null=True, default='')
    country = models.CharField(
        max_length=128, blank=True, null=True, default=''
    )
    organization = models.CharField(
        max_length=128, blank=True, null=True, default=''
    )
    gender = models.PositiveSmallIntegerField(choices=GENDER_LIST, default=0)
    position = models.CharField(max_length=128, blank=True, null=True, default='')
    bundesland = models.CharField(
        max_length=5, choices=BUNDESLAND_LIST, blank=True, default=''
    )

    is_confirmed = models.BooleanField(default=True)

    objects = managers.UserManager()

    REQUIRED_FIELDS = ['email']

    def __init__(self, *args, **kwargs):
        self._meta.get_field('username').max_length = 94
        self._meta.get_field('username').validators[1] = MaxLengthValidator(94)
        return super().__init__(*args, **kwargs)

    @property
    def receives_email_notifications(self):
        return self.newsmail_schedule != 0

    @property
    def just_username(self):
        return self.username.rsplit('+', 1)[0]

    @property
    def display_name(self):
        if self.customer and self.customer.displayed_username == Customer.DISPLAY_NAME_LAST_NAME:
            return "{} {}".format(self.first_name, self.last_name)
        else:
            return self.just_username

    @property
    def unique_token(self):
        return User.objects.get_token_for(self)

    def activate(self, save=True):
        self.is_active = True
        self.activated_at = timezone.now()
        if save:
            self.save()

    def disable(self, save=True):
        self.is_active = False
        self.deleted_at = timezone.now()
        if save:
            self.save()

    def send_verification_mail(self, customer, source_url=None):
        mail.send_template(
            self.email, customer, mail.TYPE_CONFIRM,
            sender=customer.moderator_email, context={
                'user': self,
                'url': reverse(
                    'verify-registration', kwargs={'token': self.unique_token}
                ),
                'next': source_url
            }
        )

    def send_password_reset_mail(self, customer, source_url=None):
        mail.send_template(
            self.email, customer, mail.TYPE_FORGOT,
            sender=customer.moderator_email, context={
                'user': self,
                'url': reverse(
                    'reset-password', kwargs={'token': self.unique_token}
                ),
                'next': source_url
            }
        )

    def send_newsmail(self, force=False):
        from brabbl.core.models import Argument, Statement, Discussion
        offset = timezone.now() - timedelta(days=self.newsmail_schedule)
        arguments = Argument.objects.for_customer(self.customer).visible()
        statements = Statement.objects.for_customer(self.customer).visible()
        discussions = Discussion.objects.for_customer(self.customer).visible()

        def in_timerange(qs):
            return qs.filter(created_at__range=[offset, timezone.now()])

        if self.last_sent and self.last_sent <= offset or not self.last_sent or force:
            mail.send_template(
                self.email, self.customer, mail.TYPE_DAILY,
                context={
                    'user': self,
                    'arguments': in_timerange(arguments),
                    'statements': in_timerange(statements),
                    'discussions': in_timerange(discussions),
                    'latest_discussions': discussions.order_by('-created_at')[:3]
                })
            self.last_sent = timezone.now()
            self.save()

    def __str__(self):
        return self.display_name

    def has_accepted_current_data_policy(self):
        if not self.customer:
            return True
        customer_policy = self.customer.data_policy_version
        if not customer_policy:
            return True
        accepted_agreement = self.datapolicyagreements.order_by(
            '-data_policy__version_number').first()
        if not accepted_agreement:
            return False
        return accepted_agreement.data_policy.version_number == customer_policy.version_number


class EmailGroup(models.Model):
    name = models.CharField(max_length=1024)
    language = models.CharField(
        max_length=2,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE
    )
    email_sign = models.TextField(
        help_text=_("Allowed parameters: {{domain}}")
    )

    def __str__(self):
        return self.name


class EmailTemplate(models.Model):
    EMAIL_TYPES = (
        (mail.TYPE_CONFIRM, _("Email asking for confirmation of account.")),
        # (mail.TYPE_WELCOME, _("Welcome email after successful confirmation.")),
        (mail.TYPE_DAILY, _("Daily Summary.")),
        (mail.TYPE_FORGOT, _("Forgot Password.")),
        (mail.TYPE_FLAGGING, _("Argument flagging.")),
        (mail.TYPE_NON_ACTIVE_USER_WARNING, _("Non active user warning.")),
    )

    key = models.CharField(max_length=64, choices=EMAIL_TYPES)

    subject = models.CharField(
        max_length=1024,
        help_text=_("Allowed parameters: {{domain}}, and {{username}}, {{firstname}}, "
                    "{{lastname}} if type is not Argument flagging.")
    )
    text = models.TextField(
        help_text=_("Allowed parameters: {{domain}}, and {{username}}, {{firstname}}, "
                    "{{lastname}} if type is not Argument flagging.")
    )
    email_group = models.ForeignKey(EmailGroup, on_delete=models.CASCADE)

    def __str__(self):
        return self.get_key_display()
