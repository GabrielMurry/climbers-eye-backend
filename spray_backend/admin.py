from django.contrib import admin
from .models import Movie, Gym

class MovieAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)

class GymAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)

admin.site.register(Movie, MovieAdmin)
admin.site.register(Gym, GymAdmin)