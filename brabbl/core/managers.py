from django.db.models import Q
from django.db.models.query import QuerySet


class CustomerQuerySetMixin(object):
    def for_customer(self, customer):
        return self.filter(customer=customer)


class TagQuerySet(CustomerQuerySetMixin, QuerySet):
    pass


class WordingQuerySet(QuerySet):
    def for_customer(self, customer):
        return self.filter(Q(customer=customer) | Q(customer__isnull=True))


class DiscussionQuerySet(CustomerQuerySetMixin,
                         QuerySet):
    def visible(self):
        return self.filter(deleted_at__isnull=True)


class StatementQuerySet(QuerySet):
    def for_customer(self, customer):
        return self.filter(discussion__customer=customer)

    def visible(self):
        qs = self.filter(deleted_at__isnull=True)
        qs = qs.filter(discussion__deleted_at__isnull=True)
        return qs


class ArgumentQuerySet(QuerySet):
    def for_customer(self, customer):
        return self.filter(statement__discussion__customer=customer)

    def without_replies(self):
        return self.filter(reply_to__isnull=True)

    def active(self):
        return self.exclude(status=2)  # Argument.STATUS_HIDDEN

    def visible(self):
        qs = self.filter(deleted_at__isnull=True)
        qs = qs.filter(statement__deleted_at__isnull=True)
        qs = qs.filter(statement__discussion__deleted_at__isnull=True)
        return qs
