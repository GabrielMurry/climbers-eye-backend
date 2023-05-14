from django.contrib import admin
from .models import Movie

class MovieAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)

admin.site.register(Movie, MovieAdmin)