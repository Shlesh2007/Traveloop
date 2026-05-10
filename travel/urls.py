from django.urls import path

from . import views

app_name = "travel"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
path("contact/", views.contact, name="contact"),
path("newsletter/", views.newsletter_subscribe, name="newsletter_subscribe"),
path("package/<int:package_id>/book/", views.package_book, name="package_book"),
    path("destinations/", views.destination_list, name="destination_list"),
    path("packages/", views.package_list, name="package_list"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("trips/create/", views.trip_create, name="trip_create"),
    path("trips/", views.trip_list, name="my_trips"),
    path("trips/<int:trip_id>/", views.trip_detail, name="trip_detail"),
    path("trips/<int:trip_id>/edit/", views.trip_edit, name="trip_edit"),
    path("trips/<int:trip_id>/delete/", views.trip_delete, name="trip_delete"),
    path("trips/<int:trip_id>/itinerary/", views.itinerary_builder, name="itinerary_builder"),
    path(
        "trips/<int:trip_id>/city-stop/<int:stop_id>/<str:direction>/",
        views.city_stop_move,
        name="city_stop_move",
    ),
    path("trips/<int:trip_id>/timeline/", views.itinerary_timeline, name="itinerary_timeline"),
    path("city-search/", views.city_search, name="city_search"),
    path("activity-search/", views.activity_search, name="activity_search"),
    path("trips/<int:trip_id>/budget/", views.budget_breakdown, name="budget_breakdown"),
    path("trips/<int:trip_id>/packing/", views.packing_checklist, name="packing_checklist"),
    path(
        "trips/<int:trip_id>/packing/<int:item_id>/toggle/",
        views.packing_toggle,
        name="packing_toggle",
    ),
    path(
        "trips/<int:trip_id>/packing/<int:item_id>/delete/",
        views.packing_delete,
        name="packing_delete",
    ),
    path("trips/<int:trip_id>/notes/", views.notes_page, name="notes_page"),
    path("trips/<int:trip_id>/notes/<int:note_id>/edit/", views.note_edit, name="note_edit"),
    path(
        "trips/<int:trip_id>/notes/<int:note_id>/delete/",
        views.note_delete,
        name="note_delete",
    ),
    path("profile/", views.profile_page, name="profile"),
    path("share/<uuid:slug>/", views.public_itinerary, name="public_itinerary"),
]
