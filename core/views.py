# Imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.crypto import get_random_string
from django.contrib import messages  # for toast notifications
from .models import Egg, Dinosaur, RaiseAction, Trait
from django.contrib.auth import get_user_model

# Dashboard page for logged-in users
@login_required
def dashboard(request):
    import logging
    try:
        has_egg = Egg.objects.filter(owner=request.user).exists()
        juvenile_dinos = Dinosaur.objects.filter(owner=request.user, stage='juvenile')
        for dino in juvenile_dinos:
            color = dino.species_name.split()[0].lower()
            image_map = {
                'green': 'green_rex_juvie.png',
                'blue': 'blue_spino_juvie.png',
                'orange': 'orange_trike_juvie.png',
            }
            dino.image_path = f"images/juvenile dinos/{image_map.get(color, 'green_rex_juvie.png')}"
        return render(request, 'dashboard.html', {'has_egg': has_egg, 'juvenile_dinos': juvenile_dinos})
    except Exception as e:
        logging.error(f"Dashboard error: {e}")
        return render(request, 'dashboard.html', {'has_egg': False, 'juvenile_dinos': [], 'error': str(e)})

# Claim egg page for new users
from django.views.decorators.csrf import csrf_protect
@login_required
@csrf_protect
def claim_egg(request):
    if request.method == 'POST':
        color = request.POST.get('egg_color')
        # Map color to species/element/rarity
        egg_data = {
            'green': {'species_name': 'Green Egg', 'element_type': 'Earth', 'rarity': 'Common'},
            'orange': {'species_name': 'Orange Egg', 'element_type': 'Fire', 'rarity': 'Common'},
            'blue': {'species_name': 'Blue Egg', 'element_type': 'Water', 'rarity': 'Common'},
        }
        if color in egg_data:
            Egg.objects.create(
                species_name=egg_data[color]['species_name'],
                element_type=egg_data[color]['element_type'],
                rarity=egg_data[color]['rarity'],
                owner=request.user
            )
            messages.success(request, f"You claimed a {egg_data[color]['species_name']}!")
            return redirect('active_nests')
        else:
            messages.error(request, 'Invalid egg selection.')
    return render(request, 'claim_egg.html')

# Active nests page stub
@login_required
def active_nests(request):
    eggs = Egg.objects.filter(owner=request.user, is_hatched=False)

    return render(request, 'active_nests.html', {'eggs': eggs})

# Egg detail page with wilderness search
import random
@login_required
def egg_detail(request, egg_id):
    egg = get_object_or_404(Egg, id=egg_id, owner=request.user)
    message = None
    if not egg.is_hatched:
        if egg.twigs >= 5 and egg.leaves >= 5:
            egg.is_hatched = True
            egg.save()
            return redirect('hatching_page', egg_id=egg.id)
        elif request.method == 'POST':
            if 'set_egg_name' in request.POST:
                new_name = request.POST.get('egg_name', '').strip()
                if new_name:
                    egg.name = new_name
                    egg.save()
                    message = f"Egg named '{new_name}'!"
                else:
                    message = "Egg name cannot be empty."
            elif 'search_wilderness' in request.POST:
                found = random.choice(['twig', 'leaf', None, None])  # 50% chance
                if found == 'twig':
                    egg.twigs += 1
                    egg.save()
                    message = 'You found a twig!'
                elif found == 'leaf':
                    egg.leaves += 1
                    egg.save()
                    message = 'You found a leaf!'
                else:
                    message = 'You searched but found nothing this time.'
            elif 'turn_egg' in request.POST:
                if random.random() < 0.3:
                    message = 'You turned the egg. It feels warmer!'
                else:
                    message = 'You turned the egg. Nothing happened.'
            elif 'sing_egg' in request.POST:
                if random.random() < 0.3:
                    message = 'You sang to the egg. It glows softly!'
                else:
                    message = 'You sang to the egg. No change.'
    else:
        message = 'Your egg has already hatched!'
    return render(request, 'egg_detail.html', {'egg': egg, 'message': message})
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
    return redirect('landing')
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
            return redirect('dashboard')
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

# Hatching page view
from django.conf import settings
@login_required
def hatching_page(request, egg_id):
    egg = get_object_or_404(Egg, id=egg_id, owner=request.user)
    # Determine image path based on egg color/species
    color = egg.species_name.split()[0].lower()  # e.g., 'green', 'blue', 'orange', 'purple'
    image_path = f"images/hatching egg/{color} egg.png"
    message = "Congratulations! Your egg is hatching!"
    return render(request, "hatching_page.html", {"egg": egg, "image_path": image_path, "message": message})
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
