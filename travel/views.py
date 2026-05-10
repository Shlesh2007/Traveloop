"""Main views for Traveloop travel planning flows."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ActivityForm,
    BudgetForm,
    CityStopForm,
    NoteForm,
    PackingItemForm,
    ProfileForm,
    SearchForm,
    TripForm,
)
from .models import (
    Activity,
    Budget,
    CityStop,
    Note,
    PackingItem,
    Trip,
    UserProfile,
    Destination,
    Package,
)

def _user_trip_or_404(user, trip_id):
    return get_object_or_404(Trip, pk=trip_id, user=user)


@login_required
def dashboard(request):
    trips = Trip.objects.filter(user=request.user).prefetch_related("city_stops")[:5]
    now = timezone.localdate()
    upcoming = Trip.objects.filter(user=request.user, start_date__gte=now).order_by("start_date")[:3]
    total_budget = sum([trip.total_budget for trip in Trip.objects.filter(user=request.user)])
    recent_activities = Activity.objects.filter(city_stop__trip__user=request.user).select_related("city_stop")[:5]

    context = {
        "trips_count": Trip.objects.filter(user=request.user).count(),
        "city_count": CityStop.objects.filter(trip__user=request.user).count(),
        "activity_count": Activity.objects.filter(city_stop__trip__user=request.user).count(),
        "total_budget": total_budget,
        "upcoming_trips": upcoming,
        "recent_trips": trips,
        "recent_activities": recent_activities,
        "recommended_destinations": ["Kyoto", "Lisbon", "Bali", "Istanbul", "Cape Town"],
    }
    return render(request, "travel/dashboard.html", context)


@login_required
def trip_create(request):
    if request.method == "POST":
        form = TripForm(request.POST, request.FILES)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.user = request.user
            trip.save()
            Budget.objects.get_or_create(trip=trip)
            messages.success(request, "Trip created successfully.")
            return redirect("travel:trip_detail", trip_id=trip.id)
    else:
        form = TripForm()
    return render(request, "travel/trip_form.html", {"form": form, "page_title": "Create Trip"})


@login_required
def trip_list(request):
    trips = Trip.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "travel/my_trips.html", {"trips": trips})


@login_required
def trip_detail(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    city_stops = trip.city_stops.prefetch_related("activities").all()
    notes = trip.notes.all()[:5]
    return render(
        request,
        "travel/trip_detail.html",
        {"trip": trip, "city_stops": city_stops, "notes": notes},
    )


@login_required
def trip_edit(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    if request.method == "POST":
        form = TripForm(request.POST, request.FILES, instance=trip)
        if form.is_valid():
            form.save()
            messages.success(request, "Trip updated.")
            return redirect("travel:trip_detail", trip_id=trip.id)
    else:
        form = TripForm(instance=trip)
    return render(request, "travel/trip_form.html", {"form": form, "page_title": "Edit Trip"})


@login_required
@require_POST
def trip_delete(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    trip.delete()
    messages.success(request, "Trip deleted.")
    return redirect("travel:my_trips")


@login_required
def itinerary_builder(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    city_form = CityStopForm(prefix="city")
    activity_form = ActivityForm(prefix="activity")
    activity_form.fields["city_stop"].queryset = trip.city_stops.all()

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_city":
            city_form = CityStopForm(request.POST, prefix="city")
            if city_form.is_valid():
                city = city_form.save(commit=False)
                city.trip = trip
                city.save()
                messages.success(request, "City stop added.")
                return redirect("travel:itinerary_builder", trip_id=trip.id)
        elif action == "add_activity":
            activity_form = ActivityForm(request.POST, prefix="activity")
            activity_form.fields["city_stop"].queryset = trip.city_stops.all()
            if activity_form.is_valid():
                activity = activity_form.cleaned_data["city_stop"]
                if activity.trip_id != trip.id:
                    raise Http404("Invalid city stop.")
                activity_form.save()
                messages.success(request, "Activity added.")
                return redirect("travel:itinerary_builder", trip_id=trip.id)

    city_stops = trip.city_stops.prefetch_related("activities")
    return render(
        request,
        "travel/itinerary_builder.html",
        {"trip": trip, "city_form": city_form, "activity_form": activity_form, "city_stops": city_stops},
    )


@login_required
def city_stop_move(request, trip_id, stop_id, direction):
    trip = _user_trip_or_404(request.user, trip_id)
    stop = get_object_or_404(CityStop, pk=stop_id, trip=trip)
    if direction == "up":
        target = CityStop.objects.filter(trip=trip, order__lt=stop.order).order_by("-order").first()
    else:
        target = CityStop.objects.filter(trip=trip, order__gt=stop.order).order_by("order").first()
    if target:
        stop.order, target.order = target.order, stop.order
        stop.save()
        target.save()
    return redirect("travel:itinerary_builder", trip_id=trip.id)


@login_required
def itinerary_timeline(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    city_stops = trip.city_stops.prefetch_related("activities").all()
    activities = Activity.objects.filter(city_stop__trip=trip).order_by("activity_date")

    day_map = {}
    for activity in activities:
        day_map.setdefault(activity.activity_date, []).append(activity)

    return render(
        request,
        "travel/itinerary_timeline.html",
        {"trip": trip, "city_stops": city_stops, "day_map": day_map},
    )


@login_required
def city_search(request):
    form = SearchForm(request.GET or None)
    cities = CityStop.objects.filter(trip__user=request.user)
    if form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        start = form.cleaned_data.get("start")
        end = form.cleaned_data.get("end")
        if q:
            cities = cities.filter(Q(city_name__icontains=q) | Q(country__icontains=q))
        if start:
            cities = cities.filter(arrival_date__gte=start)
        if end:
            cities = cities.filter(departure_date__lte=end)
    return render(request, "travel/city_search.html", {"form": form, "cities": cities})


@login_required
def activity_search(request):
    form = SearchForm(request.GET or None)
    activities = Activity.objects.filter(city_stop__trip__user=request.user).select_related("city_stop")
    if form.is_valid():
        q = (form.cleaned_data.get("q") or "").strip()
        start = form.cleaned_data.get("start")
        end = form.cleaned_data.get("end")
        if q:
            activities = activities.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q)
            )
        if start:
            activities = activities.filter(activity_date__gte=start)
        if end:
            activities = activities.filter(activity_date__lte=end)
    return render(request, "travel/activity_search.html", {"form": form, "activities": activities})


@login_required
def budget_breakdown(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    budget, _ = Budget.objects.get_or_create(trip=trip)
    if request.method == "POST":
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, "Budget updated.")
            return redirect("travel:budget_breakdown", trip_id=trip.id)
    else:
        form = BudgetForm(instance=budget)

    total = budget.total_cost
    avg_daily = total / trip.total_days if trip.total_days else 0
    chart_data = {
        "labels": ["Transport", "Hotel", "Food", "Activities", "Misc"],
        "values": [
            float(budget.transport_cost),
            float(budget.hotel_cost),
            float(budget.food_cost),
            float(budget.activity_cost),
            float(budget.miscellaneous_cost),
        ],
    }
    return render(
        request,
        "travel/budget_breakdown.html",
        {"trip": trip, "form": form, "budget": budget, "total": total, "avg_daily": avg_daily, "chart_data": chart_data},
    )


@login_required
def packing_checklist(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    form = PackingItemForm()
    if request.method == "POST":
        form = PackingItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.trip = trip
            item.save()
            messages.success(request, "Packing item added.")
            return redirect("travel:packing_checklist", trip_id=trip.id)
    category = request.GET.get("category", "")
    items = trip.packing_items.all()
    if category:
        items = items.filter(category=category)
    return render(request, "travel/packing_checklist.html", {"trip": trip, "form": form, "items": items, "category": category})


@login_required
@require_POST
def packing_toggle(request, trip_id, item_id):
    trip = _user_trip_or_404(request.user, trip_id)
    item = get_object_or_404(PackingItem, pk=item_id, trip=trip)
    item.is_packed = not item.is_packed
    item.save()
    return redirect("travel:packing_checklist", trip_id=trip.id)


@login_required
@require_POST
def packing_delete(request, trip_id, item_id):
    trip = _user_trip_or_404(request.user, trip_id)
    item = get_object_or_404(PackingItem, pk=item_id, trip=trip)
    item.delete()
    messages.info(request, "Packing item removed.")
    return redirect("travel:packing_checklist", trip_id=trip.id)


@login_required
def notes_page(request, trip_id):
    trip = _user_trip_or_404(request.user, trip_id)
    form = NoteForm()
    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.trip = trip
            note.save()
            messages.success(request, "Note saved.")
            return redirect("travel:notes_page", trip_id=trip.id)
    notes = trip.notes.all()
    return render(request, "travel/notes.html", {"trip": trip, "notes": notes, "form": form})


@login_required
def note_edit(request, trip_id, note_id):
    trip = _user_trip_or_404(request.user, trip_id)
    note = get_object_or_404(Note, pk=note_id, trip=trip)
    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, "Note updated.")
            return redirect("travel:notes_page", trip_id=trip.id)
    else:
        form = NoteForm(instance=note)
    return render(request, "travel/note_edit.html", {"trip": trip, "note": note, "form": form})


@login_required
@require_POST
def note_delete(request, trip_id, note_id):
    trip = _user_trip_or_404(request.user, trip_id)
    note = get_object_or_404(Note, pk=note_id, trip=trip)
    note.delete()
    messages.info(request, "Note deleted.")
    return redirect("travel:notes_page", trip_id=trip.id)


@login_required
def profile_page(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("travel:profile")
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, "travel/profile.html", {"form": form, "profile": profile})


def public_itinerary(request, slug):
    trip = get_object_or_404(Trip, public_slug=slug, is_public=True)
    city_stops = trip.city_stops.prefetch_related("activities").all()
    return render(request, "travel/public_itinerary.html", {"trip": trip, "city_stops": city_stops})

# Add these functions to travel/views.py

def home(request):
    featured_destinations = Destination.objects.filter(featured=True)[:3]
    popular_packages = Package.objects.filter(featured=True)[:3]
    search_form = SearchForm()
    
    # Mock stats for the hero section
    stats = {
        "destinations": Destination.objects.count() or 12,
        "packages": Package.objects.count() or 45,
        "travelers_booked": 1200,
        "avg_rating": 4.9
    }
    
    return render(request, "travel/home.html", {
        "featured_destinations": featured_destinations,
        "popular_packages": popular_packages,
        "search_form": search_form,
        "stats": stats
    })

def destination_list(request):
    destinations = Destination.objects.all()
    return render(request, "travel/destination_list.html", {"destinations": destinations})

def package_list(request):
    packages = Package.objects.all()
    return render(request, "travel/package_list.html", {"packages": packages})
def search(request):
    query = request.GET.get("q", "")

    destinations = Destination.objects.filter(name__icontains=query)
    packages = Package.objects.filter(name__icontains=query)

    return render(request, "travel/search_results.html", {
        "query": query,
        "destinations": destinations,
        "packages": packages,
    })
    def contact(request):
    return render(request, "travel/contact.html")def newsletter_subscribe(request):
    if request.method == "POST":
        email = request.POST.get("email")

        messages.success(request, "Subscribed successfully.")

    return redirect("travel:home")@login_required
def package_book(request, package_id):
    package = get_object_or_404(Package, id=package_id)

    return render(request, "travel/package_book.html", {
        "package": package
    })

