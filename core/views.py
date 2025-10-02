from django.shortcuts import render, get_object_or_404, redirect
from django.utils.crypto import get_random_string
from .models import Egg, Dinosaur

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
