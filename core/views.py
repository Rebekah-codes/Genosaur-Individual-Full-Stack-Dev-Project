from django.shortcuts import render, get_object_or_404, redirect
from .models import Egg

# Homepage: show all eggs
# Optionally filter: eggs = Egg.objects.filter(is_hatched=False)
def home(request):
    eggs = Egg.objects.all()
    return render(request, 'home.html', {'eggs': eggs})

# Hatch egg view
def hatch_egg(request, egg_id):
    egg = get_object_or_404(Egg, id=egg_id)
    if request.method == 'POST' and not egg.is_hatched:
        egg.is_hatched = True
        egg.save()
        # Optionally: create Dinosaur instance here
    return redirect('home')
