from django.urls import path

from .views import (
    DiningTableDetailView,
    DiningTableListCreateView,
    FloorPlanDetailView,
    FloorPlanListCreateView,
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
]
