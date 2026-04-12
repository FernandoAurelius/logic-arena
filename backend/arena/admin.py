from django.contrib import admin

from .models import Exercise, ExerciseExplanation, ExerciseExplanationCodeExample, ExerciseExplanationConcept, ExerciseTrack


class ExerciseExplanationCodeExampleInline(admin.TabularInline):
    model = ExerciseExplanationCodeExample
    extra = 0


class ExerciseExplanationConceptInline(admin.TabularInline):
    model = ExerciseExplanationConcept
    extra = 0


@admin.register(ExerciseExplanation)
class ExerciseExplanationAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'updated_at')
    search_fields = ('exercise__title', 'exercise__slug')
    inlines = [ExerciseExplanationConceptInline, ExerciseExplanationCodeExampleInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'track', 'difficulty', 'language', 'is_active')
    list_filter = ('track', 'difficulty', 'language', 'is_active')
    search_fields = ('title', 'slug')


@admin.register(ExerciseTrack)
class ExerciseTrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'category', 'sort_order')
    list_filter = ('category',)
    search_fields = ('name', 'slug')
