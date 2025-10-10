from django.contrib.auth.decorators import login_required
@login_required
def cancel_trade(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id, sender=request.user, status='pending')
    trade.status = 'declined'
    trade.save()
    messages.success(request, 'Trade offer cancelled.')
    return redirect('trade_center')
from .models import Trade
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError

# Trade form for 1-for-1 trades
class TradeForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['sender_egg'].queryset = user.eggs.all()
            self.fields['sender_dinosaur'].queryset = user.dinosaurs.all()
        # Dynamically filter receiver's items if receiver is selected
        receiver = None
        if self.data.get('receiver'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                receiver = User.objects.get(pk=self.data.get('receiver'))
            except (User.DoesNotExist, ValueError, TypeError):
                receiver = None
        elif self.initial.get('receiver'):
            receiver = self.initial.get('receiver')
        if receiver:
            self.fields['receiver_egg'].queryset = receiver.eggs.all()
            self.fields['receiver_dinosaur'].queryset = receiver.dinosaurs.all()
    class Meta:
        model = Trade
        fields = ['receiver', 'sender_egg', 'sender_dinosaur', 'receiver_egg', 'receiver_dinosaur']

    def clean(self):
        cleaned_data = super().clean()
        sender_items = [cleaned_data.get('sender_egg'), cleaned_data.get('sender_dinosaur')]
        receiver_items = [cleaned_data.get('receiver_egg'), cleaned_data.get('receiver_dinosaur')]
        if sum([item is not None for item in sender_items]) != 1:
            raise ValidationError('You must offer exactly one item (egg or dinosaur).')
        if sum([item is not None for item in receiver_items]) != 1:
            raise ValidationError('You must request exactly one item (egg or dinosaur) in return.')
        return cleaned_data

@login_required
def trade_center(request):
    # Show all pending trades involving the user
    trades = Trade.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).order_by('-created_at')
    form = TradeForm(user=request.user)
    if request.method == 'POST':
        form = TradeForm(request.POST, user=request.user)
        if form.is_valid():
            trade = form.save(commit=False)
            trade.sender = request.user
            trade.status = 'pending'
            trade.save()
            messages.success(request, 'Trade offer submitted!')
            return redirect('trade_center')
    return render(request, 'trade_center.html', {'form': form, 'trades': trades, 'user': request.user})

@login_required
def accept_trade(request, trade_id):
    trade = get_object_or_404(Trade, id=trade_id, receiver=request.user, status='pending')
    # Swap ownership of items
    if trade.sender_egg:
        trade.sender_egg.owner = trade.receiver
        trade.sender_egg.save()
    if trade.sender_dinosaur:
        trade.sender_dinosaur.owner = trade.receiver
        trade.sender_dinosaur.save()
    if trade.receiver_egg:
        trade.receiver_egg.owner = trade.sender
        trade.receiver_egg.save()
    if trade.receiver_dinosaur:
        trade.receiver_dinosaur.owner = trade.sender
        trade.receiver_dinosaur.save()
    trade.status = 'accepted'
    trade.save()
    messages.success(request, 'Trade accepted and items swapped!')
    return redirect('trade_center')
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout, login as auth_login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.crypto import get_random_string
from django.contrib import messages  # for toast notifications
from django.views.decorators.csrf import csrf_protect
from .models import Egg, Dinosaur, RaiseAction, Trait
# Wilderness page view
import logging
from django.contrib.auth.decorators import login_required


def wilderness(request):
    from django.utils import timezone
    from datetime import timedelta
    import random
    messages_list = [
        "You saw some dinosaurs but got scared and hid until it was clear.",
        "You heard rustling in the bushes, but nothing appeared.",
        "You found some tracks, but the creatures were long gone.",
        "A sudden roar made you freeze, and you decided to stay hidden.",
        "You explored quietly, but the wilderness was empty this time."
    ]
    user = request.user
    now = timezone.now()
    # Store wilderness search timestamps in session
    searches = request.session.get('wilderness_searches', [])
    # Remove searches older than 24 hours
    searches = [ts for ts in searches if timezone.datetime.fromisoformat(ts) > now - timedelta(hours=24)]
    can_search = len(searches) < 5
    found_egg = None
    message = None
    if request.method == "POST" and can_search:
        searches.append(now.isoformat())
        request.session['wilderness_searches'] = searches
        if random.random() < 0.25:
            egg_color = random.choice(['green', 'orange', 'blue'])
            egg_data = {
                'green': {'species_name': 'Green Egg', 'element_type': 'Earth', 'rarity': 'Common'},
                'orange': {'species_name': 'Orange Egg', 'element_type': 'Fire', 'rarity': 'Common'},
                'blue': {'species_name': 'Blue Egg', 'element_type': 'Water', 'rarity': 'Common'},
            }
            Egg.objects.create(
                species_name=egg_data[egg_color]['species_name'],
                element_type=egg_data[egg_color]['element_type'],
                rarity=egg_data[egg_color]['rarity'],
                owner=user
            )
            found_egg = egg_data[egg_color]['species_name']
            message = f"You found a {found_egg}!"
        else:
            message = random.choice(messages_list)
    elif request.method == "POST" and not can_search:
        message = "You have reached your search limit for today. Please come back in 24 hours."
    return render(request, "wilderness.html", {"can_search": can_search, "message": message, "found_egg": found_egg})

def create_dinosaur_from_egg(egg):
    # Only create if not already linked
    if not hasattr(egg, 'dinosaur') or egg.dinosaur is None:
        dino_name = egg.name if egg.name else f"{egg.species_name}-{get_random_string(4)}"
        return Dinosaur.objects.create(
            name=dino_name,
            species_name=egg.species_name,
            stage="juvenile",
            mood="happy",
            egg=egg,
            owner=egg.owner
        )
    return egg.dinosaur

# Your dinosaurs inventory page
@login_required
def your_dinosaurs(request):
    dinosaurs = Dinosaur.objects.filter(owner=request.user)
    print(f"DEBUG: Found {dinosaurs.count()} dinosaurs for user {request.user}")
    for dino in dinosaurs:
        raw_species = dino.species_name
        species = raw_species.strip().lower().replace('_', ' ').replace('-', ' ')
        is_green_egg = 'green egg' in species
        is_orange_egg = 'orange egg' in species
        is_blue_egg = 'blue egg' in species
        print(f"DEBUG: {dino.name} RAW species_name='{raw_species}' PROCESSED species='{species}' is_green_egg={is_green_egg} is_orange_egg={is_orange_egg} is_blue_egg={is_blue_egg} stage='{dino.stage}'")
        # Treat any non-adult stage as 'juvenile' for image purposes
        if dino.stage == 'adult':
            if is_green_egg:
                dino.image_path = "images/adult dinos/green_rex_adult.png"
                print(f"DEBUG: {dino.name} assigned adult GREEN image")
            elif is_orange_egg:
                dino.image_path = "images/adult dinos/orange_trike_adult.png"
                print(f"DEBUG: {dino.name} assigned adult ORANGE image")
            elif is_blue_egg:
                dino.image_path = "images/adult dinos/blue_spino_adult.png"
                print(f"DEBUG: {dino.name} assigned adult BLUE image")
            else:
                dino.image_path = "images/adult dinos/green_rex_adult.png"
                print(f"DEBUG: {dino.name} assigned adult DEFAULT image")
        else:
            if is_green_egg:
                dino.image_path = "images/juvenile dinos/green_rex_juvie.png"
                print(f"DEBUG: {dino.name} assigned juvenile GREEN image")
            elif is_orange_egg:
                dino.image_path = "images/juvenile dinos/orange_trike_juvie.png"
                print(f"DEBUG: {dino.name} assigned juvenile ORANGE image")
            elif is_blue_egg:
                dino.image_path = "images/juvenile dinos/blue_spino_juvie.png"
                print(f"DEBUG: {dino.name} assigned juvenile BLUE image")
            else:
                dino.image_path = "images/juvenile dinos/green_rex_juvie.png"
                print(f"DEBUG: {dino.name} assigned juvenile DEFAULT image")
        print(f"DEBUG: {dino.name} FINAL image_path='{dino.image_path}' for RAW species_name='{raw_species}' PROCESSED species='{species}'")
    return render(request, 'your_dinosaurs.html', {'dinosaurs': dinosaurs})
from django.contrib.auth import get_user_model

# Dashboard page for logged-in users
@login_required
def dashboard(request):
    import logging
    try:
        has_egg = Egg.objects.filter(owner=request.user).exists()
        all_dinos = Dinosaur.objects.filter(owner=request.user)
        juvenile_dinos = all_dinos.filter(stage='juvenile')
        has_dino = all_dinos.exists()
        for dino in juvenile_dinos:
            color = dino.species_name.split()[0].lower()
            image_map = {
                'green': 'green_rex_juvie.png',
                'blue': 'blue_spino_juvie.png',
                'orange': 'orange_trike_juvie.png',
            }
            dino.image_path = f"images/juvenile dinos/{image_map.get(color, 'green_rex_juvie.png')}"
        return render(request, 'dashboard.html', {'has_egg': has_egg, 'juvenile_dinos': juvenile_dinos, 'has_dino': has_dino})
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
            article = 'an' if egg_data[color]['species_name'][0].lower() in 'aeiou' else 'a'
            messages.success(request, f"You claimed {article} {egg_data[color]['species_name']}!")
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
    if request.method == 'POST':
        if 'release_egg' in request.POST:
            # Delete associated dinosaur if exists
            dino = getattr(egg, 'dinosaur', None)
            if dino:
                dino.delete()
            egg.delete()
            from django.contrib import messages
            messages.success(request, "Your egg and dinosaur have been released to the wild!")
            return redirect('active_nests')
        if not egg.is_hatched:
            if egg.twigs >= 5 and egg.leaves >= 5:
                egg.is_hatched = True
                egg.save()
                create_dinosaur_from_egg(egg)
                return redirect('hatching_page', egg_id=egg.id)
            elif 'set_egg_name' in request.POST:
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
                    if egg.twigs < 5:
                        egg.twigs += 1
                        egg.save()
                        message = 'You found a twig!'
                    else:
                        message = 'You searched but found nothing this time.'
                elif found == 'leaf':
                    if egg.leaves < 5:
                        egg.leaves += 1
                        egg.save()
                        message = 'You found a leaf!'
                    else:
                        message = 'You searched but found nothing this time.'
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
    elif egg.is_hatched:
        # Ensure dinosaur exists for already hatched eggs
        create_dinosaur_from_egg(egg)
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

# Registration view
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
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
    eggs = Egg.objects.filter(owner=request.user) if request.user.is_authenticated else Egg.objects.none()
    has_egg = Egg.objects.filter(owner=request.user, is_hatched=False).exists() if request.user.is_authenticated else False
    has_dino = Dinosaur.objects.filter(owner=request.user).exists() if request.user.is_authenticated else False
    import logging
    logging.warning(f"DEBUG home: has_egg={has_egg}, has_dino={has_dino}, eggs={eggs.count()}")
    return render(request, 'home.html', {'eggs': eggs, 'has_egg': has_egg, 'has_dino': has_dino})

# Hatch egg view
def hatch_egg(request, egg_id):
    egg = get_object_or_404(Egg, id=egg_id)
    if not egg.is_hatched:
        egg.is_hatched = True
        egg.save()
        create_dinosaur_from_egg(egg)
    # Always redirect to hatching page
    return redirect('hatching_page', egg_id=egg_id)

# Dino profile view
@login_required
def dinosaur_detail(request, dino_id):
    import logging
    try:
        dino = get_object_or_404(Dinosaur, id=dino_id)
        # Ensure orphaned egg is deleted if dinosaur exists and is not an egg
        if dino.egg:
            try:
                dino.egg.delete()
            except Exception:
                pass
        if request.method == 'POST':
            if 'release_dino' in request.POST:
                dino.delete()
                from django.contrib import messages
                messages.success(request, "Your dinosaur has been released to the wild!")
                return redirect('your_dinosaurs')
            elif 'set_dino_name' in request.POST:
                new_name = request.POST.get('dino_name', '').strip()
                if new_name:
                    dino.name = new_name
                    dino.save()
                    from django.contrib import messages
                    messages.success(request, f"Dinosaur named '{new_name}'!")
                else:
                    from django.contrib import messages
                    messages.error(request, "Dinosaur name cannot be empty.")
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
        # Image mapping logic (same as inventory)
        raw_species = dino.species_name
        species = raw_species.strip().lower().replace('_', ' ').replace('-', ' ')
        is_green_egg = 'green egg' in species
        is_orange_egg = 'orange egg' in species
        is_blue_egg = 'blue egg' in species
        if dino.stage == 'adult':
            if is_green_egg:
                dino.image_path = "images/adult dinos/green_rex_adult.png"
            elif is_orange_egg:
                dino.image_path = "images/adult dinos/orange_trike_adult.png"
            elif is_blue_egg:
                dino.image_path = "images/adult dinos/blue_spino_adult.png"
            else:
                dino.image_path = "images/adult dinos/green_rex_adult.png"
        else:
            if is_green_egg:
                dino.image_path = "images/juvenile dinos/green_rex_juvie.png"
            elif is_orange_egg:
                dino.image_path = "images/juvenile dinos/orange_trike_juvie.png"
            elif is_blue_egg:
                dino.image_path = "images/juvenile dinos/blue_spino_juvie.png"
            else:
                dino.image_path = "images/juvenile dinos/green_rex_juvie.png"
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
    except Exception as e:
        logging.error(f"Error in dinosaur_detail view: {e}")
        return render(request, 'dinosaur_detail.html', {
            'dino': None,
            'actions': [],
            'error': str(e),
        })

# Hatching page view
from django.conf import settings
@login_required
def hatching_page(request, egg_id):
    egg = get_object_or_404(Egg, id=egg_id, owner=request.user)
    # Determine image path based on egg color/species
    color = egg.species_name.split()[0].lower()  # e.g., 'green', 'blue', 'orange'
    image_path = f"images/hatching egg/{color}_hatching_egg.png"
    message = "Congratulations! Your egg is hatching!"
    # Delete the egg immediately after hatching page is shown
    egg.delete()
    return render(request, "hatching_page.html", {"egg": None, "image_path": image_path, "message": message})
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
            # If dino is juvenile and has enough feed actions, evolve to adult
            feeds_needed = 3
            evolved = False
            # Evolve if feed_actions >= feeds_needed and not already adult
            if dino.stage != "adult" and feed_actions >= feeds_needed:
                dino.stage = "adult"
                outcome += f" 🦉 {dino.name} has evolved into an Adult!"
                messages.success(request, f"{dino.name} evolved into an Adult!")
                evolved = True
            # Apply image mapping logic after possible evolution
            raw_species = dino.species_name
            species = raw_species.strip().lower().replace('_', ' ').replace('-', ' ')
            is_green_egg = 'green egg' in species
            is_orange_egg = 'orange egg' in species
            is_blue_egg = 'blue egg' in species
            if dino.stage == 'adult':
                if is_green_egg:
                    dino.image_path = "images/adult dinos/green_rex_adult.png"
                elif is_orange_egg:
                    dino.image_path = "images/adult dinos/orange_trike_adult.png"
                elif is_blue_egg:
                    dino.image_path = "images/adult dinos/blue_spino_adult.png"
                else:
                    dino.image_path = "images/adult dinos/green_rex_adult.png"
            else:
                if is_green_egg:
                    dino.image_path = "images/juvenile dinos/green_rex_juvie.png"
                elif is_orange_egg:
                    dino.image_path = "images/juvenile dinos/orange_trike_juvie.png"
                elif is_blue_egg:
                    dino.image_path = "images/juvenile dinos/blue_spino_juvie.png"
                else:
                    dino.image_path = "images/juvenile dinos/green_rex_juvie.png"
        elif action_type == "play":
            outcome = f"{dino.name} had fun playing!"
            dino.mood = "playful"
        elif action_type == "train":
            outcome = f"{dino.name} trained hard and grew stronger!"
            dino.mood = "tired"
            dino.level_up()  # training increases level
            if dino.level == 100:
                messages.success(request, f"{dino.name} reached the max level 100!")
        elif action_type == "wilderness_search" and dino.stage == "juvenile":
            # If twigs or leaves is already 5, always return 'didn't find anything'
            if dino.twigs >= 5 or dino.leaves >= 5:
                outcome = f"{dino.name} searched the wilderness but didn't find anything (max resources reached)."
                dino.mood = "hungry"
                messages.info(request, outcome)
            else:
                import random
                if random.random() < 0.6:
                    outcome = f"{dino.name} found some delicious food in the wilderness!"
                    dino.mood = "happy"
                    messages.success(request, outcome)
                else:
                    outcome = f"{dino.name} searched the wilderness but found nothing this time."
                    dino.mood = "hungry"
                    messages.info(request, outcome)
        dino.save()
        RaiseAction.objects.create(
            dinosaur=dino,
            action_type=action_type,
            outcome=outcome
        )
        # Unlock trait only at levels 2, 26, 51, 76, 99, and only once per level
        trait_levels = [2, 26, 51, 76, 99]
        # Check if a trait for this level has already been unlocked
        if dino.stage in ["juvenile", "adult"] and dino.level in trait_levels and dino.traits.count() < 5:
            # Check if a RaiseAction for trait unlock at this level already exists
            trait_action_exists = RaiseAction.objects.filter(dinosaur=dino, action_type="trait_unlock", outcome__icontains=f"level {dino.level}").exists()
            if not trait_action_exists:
                import random
                all_traits = list(Trait.objects.exclude(pk__in=dino.traits.values_list('pk', flat=True)))
                if all_traits:
                    trait = random.choice(all_traits)
                    dino.traits.add(trait)
                    dino.save()
                    outcome_text = f"{dino.name} unlocked a new trait: {trait.name}! (level {dino.level})"
                    RaiseAction.objects.create(
                        dinosaur=dino,
                        action_type="trait_unlock",
                        outcome=outcome_text
                    )
                    messages.success(request, f"{dino.name} unlocked a new trait: {trait.name}!")
                    # Redirect with trait info for modal
                    from django.urls import reverse
                    from django.utils.http import urlencode
                    params = urlencode({
                        'trait_unlocked': 1,
                        'trait_name': trait.name,
                        'trait_description': trait.description
                    })
                    url = reverse("dinosaur_detail", args=[dino.id]) + f"?{params}"
                    return redirect(url)
        return redirect("dinosaur_detail", dino_id=dino.id)
