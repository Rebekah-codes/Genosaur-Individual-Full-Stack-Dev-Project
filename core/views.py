from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def home(request):
    """Simple homepage view"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Genosaur Project</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; text-align: center; }
            h1 { color: #2c3e50; }
            .success { color: #27ae60; font-size: 18px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🦕 Welcome to Genosaur Project!</h1>
            <p class="success">✅ Your Django application is successfully deployed on Heroku!</p>
            <p>This is your homepage. You can now start building your application.</p>
            <hr>
            <p><a href="/admin/">Admin Panel</a></p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)
