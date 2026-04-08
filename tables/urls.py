from django.urls import path

from .views import DiningTableListCreateView, FloorPlanListCreateView, ReservationListCreateView

urlpatterns = [
    path("floor-plans", FloorPlanListCreateView.as_view(), name="floor-plans-list-create"),
    path("tables", DiningTableListCreateView.as_view(), name="tables-list-create"),
    path("reservations", ReservationListCreateView.as_view(), name="reservations-list-create"),
]
