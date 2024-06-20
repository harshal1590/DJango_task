from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SignupView, SearchUserView, FriendRequestViewSet

router = DefaultRouter()
router.register(r'friend-requests', FriendRequestViewSet, basename='friendrequest')

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('search/', SearchUserView.as_view(), name='search-users'),
    path('', include(router.urls)),
]
