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
]
