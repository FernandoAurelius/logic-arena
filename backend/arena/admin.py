from django.contrib import admin

from .models import (
    Exercise,
    ExerciseExplanation,
    ExerciseExplanationCodeExample,
    ExerciseExplanationConcept,
    ExerciseTrack,
    ExerciseTrackConcept,
    ExerciseTrackPrerequisite,
    ExerciseType,
    LearningModule,
)


class ExerciseExplanationCodeExampleInline(admin.TabularInline):
    model = ExerciseExplanationCodeExample
    extra = 0


class ExerciseExplanationConceptInline(admin.TabularInline):
    model = ExerciseExplanationConcept
    extra = 0


class ExerciseTrackConceptInline(admin.TabularInline):
    model = ExerciseTrackConcept
    extra = 0


class ExerciseTrackPrerequisiteInline(admin.TabularInline):
    model = ExerciseTrackPrerequisite
    extra = 0


@admin.register(ExerciseExplanation)
class ExerciseExplanationAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'updated_at')
    search_fields = ('exercise__title', 'exercise__slug')
    inlines = [ExerciseExplanationConceptInline, ExerciseExplanationCodeExampleInline]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'track', 'exercise_type', 'track_position', 'difficulty', 'language', 'is_active')
    list_filter = ('track__module', 'track', 'exercise_type', 'difficulty', 'language', 'is_active')
    search_fields = ('title', 'slug')


@admin.register(ExerciseTrack)
class ExerciseTrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'module', 'category', 'sort_order')
    list_filter = ('module', 'category')
    search_fields = ('name', 'slug')
    inlines = [ExerciseTrackConceptInline, ExerciseTrackPrerequisiteInline]


@admin.register(LearningModule)
class LearningModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'audience', 'source_kind', 'sort_order')
    list_filter = ('status', 'source_kind')
    search_fields = ('name', 'slug')


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'sort_order')
    search_fields = ('name', 'slug')
