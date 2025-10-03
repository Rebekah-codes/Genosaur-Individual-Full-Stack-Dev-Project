# Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.crypto import get_random_string
from django.contrib import messages  # for toast notifications
from .models import Egg, Dinosaur, RaiseAction, Trait

# Dashboard page for logged-in users
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')
# Landing page for unauthenticated users
def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'landing.html')
from django.contrib.auth import logout as auth_logout
# Logout view
def logout_view(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
# Login view
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.crypto import get_random_string
from django.contrib import messages  # for toast notifications
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .models import Egg, Dinosaur, RaiseAction, Trait
# Registration view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

# Homepage: show all eggs
# Optionally filter: eggs = Egg.objects.filter(is_hatched=False)
def home(request):
    try:
        eggs = Egg.objects.all().select_related('dinosaur')
        return render(request, 'home.html', {'eggs': eggs})
    except Exception as e:
        import logging
        logging.error(f"Error in home view: {e}")
        return render(request, 'home.html', {'eggs': [], 'error': str(e)})

# Hatch egg view
def hatch_egg(request, egg_id):
    egg = get_object_or_404(Egg, id=egg_id)
    if not egg.is_hatched:
        egg.is_hatched = True
        egg.save()
        # Auto-create a Dinosaur from this egg
        dino_name = f"{egg.species_name}-{get_random_string(4)}"
        Dinosaur.objects.create(
            name=dino_name,
            species_name=egg.species_name,
            stage="hatchling",
            mood="happy",
            egg=egg,
            owner=egg.owner
        )
    return redirect('home')

# Dino profile view
def dinosaur_detail(request, dino_id):
    dino = get_object_or_404(Dinosaur, id=dino_id)
    actions = dino.actions.order_by('-timestamp')
    total_actions = dino.actions.count()
    feed_actions = dino.actions.filter(action_type="feed").count()
    feeds_needed = 3
    actions_needed = 5
    feed_progress = min(feed_actions, feeds_needed)
    action_progress = min(total_actions, actions_needed)
    # Calculate percent for progress bars
    feed_percent = int((feed_progress / feeds_needed) * 100) if feeds_needed else 0
    action_percent = int((action_progress / actions_needed) * 100) if actions_needed else 0
    feed_complete = feed_progress >= feeds_needed
    action_complete = action_progress >= actions_needed
    level_percent = int((dino.level / 100) * 100)
    return render(request, 'dinosaur_detail.html', {
        'dino': dino,
        'actions': actions,
        'feed_progress': feed_progress,
        'feeds_needed': feeds_needed,
        'action_progress': action_progress,
        'actions_needed': actions_needed,
        'feed_percent': feed_percent,
        'action_percent': action_percent,
        'feed_complete': feed_complete,
        'action_complete': action_complete,
        'level_percent': level_percent,
    })

# Perform feed/play/train action
def perform_action(request, dino_id):
    dino = get_object_or_404(Dinosaur, id=dino_id)
    if request.method == "POST":
        action_type = request.POST.get("action_type")
        outcome = "Nothing happened."
        total_actions = dino.actions.count()
        feed_actions = dino.actions.filter(action_type="feed").count()

        if action_type == "feed":
            outcome = f"{dino.name} enjoyed a tasty meal!"
            dino.mood = "happy"
            if dino.stage == "hatchling" and feed_actions + 1 >= 3:
                dino.stage = "juvenile"
                outcome += f" 🌱 {dino.name} has grown into a Juvenile!"
                messages.success(request, f"{dino.name} evolved into a Juvenile!")
        elif action_type == "play":
            outcome = f"{dino.name} had fun playing!"
            dino.mood = "playful"
        elif action_type == "train":
            outcome = f"{dino.name} trained hard and grew stronger!"
            dino.mood = "tired"
            dino.level_up()  # training increases level
            if dino.level == 100:
                messages.success(request, f"{dino.name} reached the max level 100!")
        dino.save()
        RaiseAction.objects.create(
            dinosaur=dino,
            action_type=action_type,
            outcome=outcome
        )
        if total_actions + 1 == 5:
            trait = Trait.objects.first()
            if trait:
                dino.traits.add(trait)
                dino.save()
                RaiseAction.objects.create(
                    dinosaur=dino,
                    action_type="train",
                    outcome=f"{dino.name} unlocked a new trait: {trait.name}!"
                )
                messages.success(request, f"{dino.name} unlocked a new trait: {trait.name}!")
    return redirect("dinosaur_detail", dino_id=dino.id)
