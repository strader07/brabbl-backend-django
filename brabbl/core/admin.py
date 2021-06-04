from ckeditor.widgets import CKEditorWidget
from embed_video.admin import AdminVideoMixin

from django.db import models as db_models
from django.contrib.admin import register, ModelAdmin, TabularInline
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from brabbl.core.forms import DiscussionForm
from brabbl.utils.admin import SetOfPropertiesInline
from brabbl.utils.models import get_thumbnail_url
from . import models


@register(models.Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'customer')
    list_filter = ('customer',)


class WordingValueInline(TabularInline):
    model = models.WordingValue
    verbose_name_plural = _("Barometer Wording")


@register(models.Wording)
class WordingAdmin(ModelAdmin):
    inlines = [WordingValueInline]
    list_display = ('name', 'customer')
    list_filter = ('customer',)

    fieldsets = (
        (None, {'fields': ('customer', 'name')}),

        (_('Statement voting'), {'fields': (
            'rating_1', 'rating_2', 'rating_3', 'rating_4', 'rating_5'
        )}),

        (_('Statement list header'), {'fields': [('list_header_contra', 'list_header_pro')]}),
        (_('Statement header'),
         {'fields': [('header_contra', 'header_pro'),
                     ('statement_header', 'statement_list_header')]}),
        (_('Add button short (top)'), {'fields': [('button_short_new_contra', 'button_short_new_pro')]}),
        (_('Add button (bottom)'), {'fields': [('button_new_contra', 'button_new_pro')]}),
        (_('Survey - list header'), {'fields': [('survey_statement', 'survey_statements')]}),
        (_('Survey - Add answer button'),
         {'fields': [('survey_add_answer_button_top', 'survey_add_answer_button_bottom')]}),
        (_('Reply counter'), {'fields': [('reply_counter', 'reply_counter_plural')]}),
    )


class ArgumentInline(TabularInline):
    model = models.Argument
    extra = 0


@register(models.Argument)
class ArgumentAdmin(ModelAdmin):
    inlines = [ArgumentInline]
    list_display = ('id', 'discussion', 'statement', 'title', 'is_pro',
                    'created_by', 'deleted_at', 'reply_count', 'customer')
    list_filter = ('statement__discussion__customer', 'is_pro')
    raw_id_fields = ('statement', 'created_by')
    search_fields = ('id', 'title')

    def discussion(self, obj):
        return obj.statement.discussion.statement

    discussion.short_description = _("Discussion")
    discussion.admin_order_field = 'statement__discussion__statement'

    def statement(self, obj):
        return obj.statement.statement

    statement.short_description = _("Statement")
    statement.admin_order_field = 'statement__statement'

    def customer(self, obj):
        return obj.statement.discussion.customer

    customer.short_description = _("Customer")
    customer.admin_order_field = "statement__discussion__customer__name"


@register(models.Statement)
class StatementAdmin(AdminVideoMixin, ModelAdmin):
    inlines = [ArgumentInline]
    list_display = ('statement', 'discussion', 'created_by', 'reply_count', 'customer')
    list_filter = ('discussion__customer',)

    def discussion(self, obj):
        return obj.statement.discussion.statement

    discussion.short_description = _("Discussion")
    discussion.admin_order_field = 'statement__discussion__statement'

    def customer(self, obj):
        return obj.discussion.customer

    customer.short_description = _("Customer")
    customer.admin_order_field = "discussion__customer__name"


class StatementInline(TabularInline):
    model = models.Statement
    raw_id_fields = ('created_by',)
    extra = 0


@register(models.DiscussionList)
class DiscussionListAdmin(ModelAdmin):
    readonly_fields = ('url',)


@register(models.Discussion)
class DiscussionAdmin(ModelAdmin):
    form = DiscussionForm
    inlines = [StatementInline]
    raw_id_fields = ('created_by',)
    search_fields = ('statement',)
    list_display = ('id', 'show_image', 'statement', 'external_id', 'created_by',
                    'multiple_statements_allowed', 'customer')
    list_filter = ('customer', 'multiple_statements_allowed')
    fieldsets = (
        (None, {
            'fields': (
                'customer', 'created_by', 'external_id', 'source_url',
                'image', 'image_url', 'statement', 'tags', 'language'
            )
        }),
        (_("Properties"), {
            'fields': (
                'has_barometer', 'has_arguments', 'has_replies', 'multiple_statements_allowed',
                'user_can_add_replies', 'barometer_wording',
            )
        }),
        (_("Time limit"), {
            'fields': ('start_time', 'end_time')
        })
    )

    def show_image(self, obj):
        url = obj.image_url
        if obj.image:
            url = get_thumbnail_url(obj.image, {'size': (100, 70), 'crop': True})
        return format_html('<img style="width:100px" src="{}" />', url)


class NotificationWordingMessageInline(SetOfPropertiesInline):
    model = models.NotificationWordingMessage
    fields = ('value',)


class MarkdownWordingMessageInline(SetOfPropertiesInline):
    formfield_overrides = {
        db_models.TextField: {'widget': CKEditorWidget},
    }
    model = models.MarkdownWordingMessage
    fields = ('value',)


@register(models.NotificationWording)
class NotificationWordingAdmin(ModelAdmin):
    inlines = [NotificationWordingMessageInline, MarkdownWordingMessageInline]
