from django.urls import path

from .views import DeviceHeartbeatView, DeviceRegisterView, SyncPullView, SyncPushView

urlpatterns = [
    path("devices/register", DeviceRegisterView.as_view(), name="device-register"),
    path("devices/heartbeat", DeviceHeartbeatView.as_view(), name="device-heartbeat"),
    path("sync/push", SyncPushView.as_view(), name="sync-push"),
    path("sync/pull", SyncPullView.as_view(), name="sync-pull"),
]
