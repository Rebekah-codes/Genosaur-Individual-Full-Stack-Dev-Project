from django.shortcuts import render, get_object_or_404, redirect
from django.utils.crypto import get_random_string
from .models import Egg, Dinosaur, RaiseAction

# Homepage: show all eggs
# Optionally filter: eggs = Egg.objects.filter(is_hatched=False)
def home(request):
    eggs = Egg.objects.all().select_related('dinosaur')
    return render(request, 'home.html', {'eggs': eggs})

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
    return render(request, 'dinosaur_detail.html', {
        'dino': dino,
        'actions': actions
    })

# Perform feed/play/train action
def perform_action(request, dino_id):
    dino = get_object_or_404(Dinosaur, id=dino_id)
    if request.method == "POST":
        action_type = request.POST.get("action_type")
        # Simple outcome logic
        if action_type == "feed":
            outcome = f"{dino.name} enjoyed a tasty meal!"
            dino.mood = "happy"
        elif action_type == "play":
            outcome = f"{dino.name} had fun playing!"
            dino.mood = "playful"
        elif action_type == "train":
            outcome = f"{dino.name} trained hard and grew stronger!"
            dino.stage = "juvenile" if dino.stage == "hatchling" else dino.stage
        else:
            outcome = "Nothing happened."
        dino.save()
        RaiseAction.objects.create(
            dinosaur=dino,
            action_type=action_type,
            outcome=outcome
        )
    return redirect("dinosaur_detail", dino_id=dino.id)
