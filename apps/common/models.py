import uuid
from typing import TYPE_CHECKING, Any, Iterable, Optional, TypeVar
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils.text import slugify

T = TypeVar('T', bound='BaseModel')


def make_unique_slug(model_cls: type[models.Model], value: str, fallback: str = 'item', slug_field: str = 'slug') -> str:
    """
    Generate a unique slug for a model class without duplicating counter loops across apps.
    """
    base_slug = slugify(value) or fallback
    slug = base_slug
    counter = 1
    manager: Any = getattr(model_cls, 'objects')
    while manager.filter(**{slug_field: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug



class UUIDModel(models.Model):
    """
    Abstract model mixin replacing the default integer primary key with a UUIDv4 primary key.
    Ensures secure, non-sequential, globally unique identifiers across all domain models.
    """
    id: Any = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """
    Abstract model mixin providing created_at and updated_at datetime tracking.
    Inherited across all domain models for consistent audit timestamps.
    """
    created_at: Any = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at: Any = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActiveModelMixin(models.Model):
    """
    Abstract model mixin providing an is_active boolean toggle.
    """
    is_active: Any = models.BooleanField(default=True, db_index=True)

    class Meta:
        abstract = True


class UUIDReferenceModel(models.Model):
    """
    Abstract model mixin providing an immutable UUID reference identifier.
    Kept for backwards compatibility where a distinct reference token is required.
    """
    reference_id: Any = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimestampedModel):
    """
    Standard base model for Axoora entities.
    Combines UUID primary key with audit timestamps and shared DRY CRUD helpers.
    """
    objects: Any = models.Manager()

    if TYPE_CHECKING:
        def __getattr__(self, name: str) -> Any: ...

    class Meta(UUIDModel.Meta, TimestampedModel.Meta):
        abstract = True

    @classmethod
    def _base_queryset(cls) -> Any:
        """
        Base queryset hook for subclasses to attach default annotations, select_related,
        or prefetch_related in one place (used automatically by get_by_id).
        """
        return cls.objects

    @classmethod
    def get_by_id(
        cls: type[T],
        pk: Any,
        select_related: Iterable[str] = (),
        prefetch_related: Iterable[str] = (),
    ) -> Optional[T]:
        """
        Safely fetch an instance by UUID primary key without raising on invalid UUIDs or missing rows.
        """
        try:
            qs = cls._base_queryset()
            if select_related:
                qs = qs.select_related(*select_related)
            if prefetch_related:
                qs = qs.prefetch_related(*prefetch_related)
            return qs.get(id=pk)
        except (ObjectDoesNotExist, ValueError, TypeError, ValidationError):
            return None

    @classmethod
    def delete_by_id(cls, pk: Any) -> bool:
        """
        Safely delete an instance by UUID primary key. Returns True if deleted, False if not found.
        """
        instance = cls.get_by_id(pk)
        if not instance:
            return False
        instance.delete()
        return True

    def apply_updates(self, allowed_fields: Iterable[str], **fields: Any) -> list[str]:
        """
        Apply partial field updates for keys in `allowed_fields`, automatically saving `updated_at`
        when modified. Returns the list of updated field names.
        """
        allowed = set(allowed_fields)
        update_fields: list[str] = []
        for key, value in fields.items():
            if key in allowed and value is not None:
                setattr(self, key, value)
                update_fields.append(key)
        if update_fields:
            update_fields.append('updated_at')
            self.save(update_fields=update_fields)
        return update_fields
