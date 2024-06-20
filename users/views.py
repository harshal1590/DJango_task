from django.shortcuts import render
from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework import viewsets
from django.db.models import Q
from .models import FriendRequest
from .serializers import UserSerializer, FriendRequestSerializer
import datetime
from rest_framework.pagination import PageNumberPagination

User = get_user_model()

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class UserPagination(PageNumberPagination):
    page_size = 10

class SearchUserView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = UserPagination

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword', '')
        if '@' in keyword:
            return User.objects.filter(email__iexact=keyword)
        return User.objects.filter(Q(username__icontains=keyword) | Q(first_name__icontains=keyword) | Q(last_name__icontains=keyword))

class FriendRequestViewSet(viewsets.ModelViewSet):
    queryset = FriendRequest.objects.all()
    serializer_class = FriendRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        from_user = request.user
        to_user_id = request.data.get('to_user')
        to_user = User.objects.get(id=to_user_id)
        
        if FriendRequest.objects.filter(from_user=from_user, to_user=to_user, status='pending').exists():
            return Response({"detail": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)
        
        last_minute_requests = FriendRequest.objects.filter(from_user=from_user, timestamp__gte=datetime.datetime.now() - datetime.timedelta(minutes=1))
        if last_minute_requests.count() >= 3:
            return Response({"detail": "You can not send more than 3 friend requests within a minute."}, status=status.HTTP_400_BAD_REQUEST)

        friend_request = FriendRequest(from_user=from_user, to_user=to_user)
        friend_request.save()
        return Response(FriendRequestSerializer(friend_request).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        pending_requests = FriendRequest.objects.filter(to_user=request.user, status='pending')
        return Response(FriendRequestSerializer(pending_requests, many=True).data)

    @action(detail=False, methods=['get'])
    def friends(self, request):
        friends = User.objects.filter(Q(sent_requests__to_user=request.user, sent_requests__status='accepted') | Q(received_requests__from_user=request.user, received_requests__status='accepted'))
        return Response(UserSerializer(friends, many=True).data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response({"detail": "Not authorized to accept this request."}, status=status.HTTP_403_FORBIDDEN)
        friend_request.status = 'accepted'
        friend_request.save()
        return Response(FriendRequestSerializer(friend_request).data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        friend_request = self.get_object()
        if friend_request.to_user != request.user:
            return Response({"detail": "Not authorized to reject this request."}, status=status.HTTP_403_FORBIDDEN)
        friend_request.status = 'rejected'
        friend_request.save()
        return Response(FriendRequestSerializer(friend_request).data)
