from django.urls import path

from .views import (
    DiningTableDetailView,
    DiningTableListCreateView,
    FloorPlanDetailView,
    FloorPlanListCreateView,
    ReservationArrivedView,
    ReservationCancelView,
    ReservationDetailView,
    ReservationListCreateView,
    WaitlistEntryCallView,
    WaitlistEntryCancelView,
    WaitlistEntryDetailView,
    WaitlistEntryListCreateView,
    WaitlistEntrySeatView,
)

urlpatterns = [
    path("floor-plans", FloorPlanListCreateView.as_view(), name="floor-plans-list-create"),
    path("floor-plans/<int:pk>", FloorPlanDetailView.as_view(), name="floor-plans-detail"),
    path("tables", DiningTableListCreateView.as_view(), name="tables-list-create"),
    path("tables/<int:pk>", DiningTableDetailView.as_view(), name="tables-detail"),
    path("reservations", ReservationListCreateView.as_view(), name="reservations-list-create"),
    path("reservations/<int:pk>", ReservationDetailView.as_view(), name="reservations-detail"),
    path("reservations/<int:pk>/arrived", ReservationArrivedView.as_view(), name="reservations-arrived"),
    path("reservations/<int:pk>/cancel", ReservationCancelView.as_view(), name="reservations-cancel"),
    path("waitlist", WaitlistEntryListCreateView.as_view(), name="waitlist-list-create"),
    path("waitlist/<int:pk>", WaitlistEntryDetailView.as_view(), name="waitlist-detail"),
    path("waitlist/<int:pk>/call", WaitlistEntryCallView.as_view(), name="waitlist-call"),
    path("waitlist/<int:pk>/seat", WaitlistEntrySeatView.as_view(), name="waitlist-seat"),
    path("waitlist/<int:pk>/cancel", WaitlistEntryCancelView.as_view(), name="waitlist-cancel"),
]
