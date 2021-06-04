from rest_framework import routers
from django.conf.urls import url

from . import views

router = routers.SimpleRouter()
router.register(r'tags', views.TagViewSet, base_name='tag')
router.register(r'wordings', views.WordingViewSet, base_name='wording')
router.register(r'notification_wording',
                views.NotificationWordingViewSet,
                base_name='notification_wording')
router.register(r'discussion_list', views.DiscussionListViewSet, base_name='discussion_list')
router.register(r'discussions', views.DiscussionViewSet, base_name='discussion')
router.register(r'statements', views.StatementViewSet, base_name='statement')
router.register(r'arguments', views.ArgumentViewSet, base_name='argument')
router.register(r'flag', views.FlagAPIView, base_name='flag')

urlpatterns = router.urls
urlpatterns += (
    url(r'^translation/$', views.TranslationAPIView.as_view(),
        name='translation'),
    url(r'^customer/$', views.CustomerAPIView.as_view({'get': 'retrieve'}),
        name='customer')
)
