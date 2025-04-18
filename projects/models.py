import base64
import random
import secrets
import string
from datetime import timedelta

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from guardian.shortcuts import assign_perm

from studio.utils import get_logger

logger = get_logger(__name__)


class BasicAuth(models.Model):
    name = models.CharField(max_length=512)
    owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    password = models.CharField(max_length=100, blank=True, default="")
    project = models.ForeignKey(
        settings.PROJECTS_MODEL,
        on_delete=models.CASCADE,
        related_name="ba_project",
        null=True,
    )
    username = models.CharField(max_length=100, blank=True, default="")


class Environment(models.Model):
    app = models.ForeignKey(
        settings.APPS_MODEL, on_delete=models.CASCADE, null=True, help_text="App associated with the environment"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    image = models.CharField(max_length=100, help_text="Image name. Could be like jupyter/minimal-notebook:latest")
    name = models.CharField(max_length=100, help_text="Display name for the environment for users")
    project = models.ForeignKey(
        settings.PROJECTS_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Project associated with the environment",
    )

    repository = models.CharField(
        max_length=100, blank=True, null=True, help_text="Repository name. Could be empty or like ghcr.io"
    )
    slug = models.CharField(max_length=100, null=True, blank=True, help_text="This one seem to be legacy and unused")
    updated_at = models.DateTimeField(auto_now=True)

    public = models.BooleanField(default=False, help_text="Seems to be legacy and have no effect.")

    def __str__(self):
        return str(self.name)

    def get_full_image_reference(self):
        """
        Get the full image reference for the environment

        It's either just the image name or the repository/image name
        """
        return f"{self.repository}/{self.image}" if self.repository else self.image


class Flavor(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    cpu_lim = models.TextField("CPU limit", blank=True, null=True, default="2000m")
    gpu_lim = models.TextField(blank=True, null=True, default="0")
    ephmem_lim = models.TextField("Ephemeral storage limit", blank=True, null=True, default="5000Mi")
    mem_lim = models.TextField("Memory limit", blank=True, null=True, default="4Gi")
    cpu_req = models.TextField("CPU request", blank=True, null=True, default="200m")
    gpu_req = models.TextField(blank=True, null=True, default="0")
    ephmem_req = models.TextField("Ephemeral storage request", blank=True, null=True, default="200Mi")
    mem_req = models.TextField("Memory request", blank=True, null=True, default="0.5Gi")
    name = models.CharField("Flavor name (N vCPU, N GB RAM)", max_length=512)
    project = models.ForeignKey(settings.PROJECTS_MODEL, on_delete=models.CASCADE, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def to_dict(self, app_slug=None):
        flavor_dict = dict(
            flavor=dict(
                requests={
                    "cpu": self.cpu_req,
                    "memory": self.mem_req,
                    "ephemeral-storage": self.ephmem_req,
                },
                limits={
                    "cpu": self.cpu_lim,
                    "memory": self.mem_lim,
                    "ephemeral-storage": self.ephmem_lim,
                },
            )
        )
        # allow GPU only for specific apps.
        apps_allowed_gpus = ["jupyter-lab"]
        if self.gpu_req and int(self.gpu_req) > 0 and app_slug in apps_allowed_gpus:
            flavor_dict["flavor"]["requests"]["nvidia.com/gpu"] = self.gpu_req
            flavor_dict["flavor"]["limits"]["nvidia.com/gpu"] = self.gpu_lim

        return flavor_dict


# it will become the default objects attribute for a Project model
class ProjectManager(models.Manager):
    def create_project(self, name, owner, description, status="active", project_template=None):
        user_can_create = self.user_can_create(owner)

        if not user_can_create:
            raise Exception("User not allowed to create project")

        key = self.generate_passkey()
        letters = string.ascii_lowercase
        secret = self.generate_passkey(40)
        slug = slugify(name[:47])
        if len(slug) < 3:
            slug = "".join(random.choice(letters) for i in range(3))
        slug_extension = "".join(random.choice(letters) for i in range(3))
        slug = "{}-{}".format(slugify(slug), slug_extension)

        project = self.create(
            name=name,
            owner=owner,
            slug=slug,
            project_key=key,
            project_secret=secret,
            description=description,
            status=status,
            project_template=project_template,
        )

        assign_perm("can_view_project", owner, project)
        return project

    def generate_passkey(self, length=20):
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        # Encrypt the key
        password = password.encode("ascii")
        base64_bytes = base64.b64encode(password)
        password = base64_bytes.decode("ascii")

        return password

    def user_can_create(self, user):
        if not user.is_authenticated:
            return False

        num_of_projects = self.filter(Q(owner=user), status="active").count()

        try:
            project_per_user_limit = settings.PROJECTS_PER_USER_LIMIT
        except Exception:
            project_per_user_limit = None

        has_perm = user.has_perm("projects.add_project")

        return project_per_user_limit is None or project_per_user_limit > num_of_projects or has_perm

    def get_projects_from_user(self, user):
        return self.filter(Q(owner=user) | Q(authorized=user)).distinct()

    def get_project(self, user, slug=None, id=None):
        qs = (
            self.filter(Q(owner=user) | Q(authorized=user), pk=id)
            if id is not None
            else self.filter(Q(owner=user) | Q(authorized=user), slug=slug)
        )

        return qs.first() if qs.count() != 0 else None


def get_random_pattern_class():
    randint = random.randint(1, 12)

    return f"pattern-{randint}"


def get_default_apps_per_project_limit():
    try:
        apps_per_project_limit = settings.APPS_PER_PROJECT_LIMIT if settings.APPS_PER_PROJECT_LIMIT is not None else {}
    except Exception:
        apps_per_project_limit = {}

    return apps_per_project_limit


class ProjectTemplate(models.Model):
    description = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to="projecttemplates/images/", blank=True, null=True)
    name = models.CharField(max_length=512)
    revision = models.IntegerField(default=1)
    slug = models.CharField(max_length=512, default="")
    template = models.TextField(null=True, blank=True)
    available_apps = models.ManyToManyField("apps.Apps", blank=True, related_name="available_apps")

    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = (
            "slug",
            "revision",
        )

    def __str__(self):
        return "{} ({})".format(self.name, self.revision)


class Project(models.Model):
    authorized = models.ManyToManyField(get_user_model(), blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    clone_url = models.CharField(max_length=512, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    name = models.CharField(max_length=512)
    objects = ProjectManager()
    owner = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING, related_name="owner")

    apps_per_project = models.JSONField(blank=True, null=True, default=get_default_apps_per_project_limit)

    pattern = models.CharField(max_length=255, default="")

    slug = models.CharField(max_length=512, unique=True)
    status = models.CharField(max_length=20, null=True, blank=True, default="active")
    updated_at = models.DateTimeField(auto_now=True)

    # Is needed because of environments
    image = models.CharField(max_length=2048, blank=True, null=True)

    # Is needed for minio
    project_key = models.CharField(max_length=512)
    project_secret = models.CharField(max_length=512)
    # ----------------------

    # Is needed to determine project template
    project_template = models.ForeignKey(ProjectTemplate, on_delete=models.DO_NOTHING, null=True)

    class Meta:
        permissions = [("can_view_project", "Can view project")]

    def __str__(self):
        return "Name: {} ({})".format(self.name, self.status)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.status == "created":
            if self.created_at is not None and self.created_at < timezone.now() - timedelta(minutes=2):
                self.status = "active"
                self.save()


@receiver(pre_delete, sender=Project)
def on_project_delete(sender, instance, **kwargs):
    Model = apps.get_model(app_label=settings.MODELS_MODEL)
    logger.info("ARCHIVING PROJECT MODELS")
    models = Model.objects.filter(project=instance)

    for model in models:
        model.status = "AR"
        model.save()


@receiver(pre_save, sender=Project)
def on_project_save(sender, instance, **kwargs):
    if instance.pattern == "":
        projects = Project.objects.filter(owner=instance.owner)

        patterns = projects.values_list("pattern", flat=True)

        arr = []

        for i in range(1, 31):
            pattern = f"pattern-{i}"

            if pattern not in patterns:
                arr.append(pattern)

        pattern = ""

        if len(arr) > 0:
            rand_index = random.randint(0, len(arr) - 1)

            pattern = arr[rand_index]

        else:
            randint = random.randint(1, 30)
            pattern = f"pattern-{randint}"

        instance.pattern = pattern


class ProjectLog(models.Model):
    MODULE_CHOICES = [
        ("DE", "deployments"),
        ("LA", "labs"),
        ("MO", "models"),
        ("PR", "projects"),
        ("RE", "reports"),
        ("UN", "undefined"),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=512)
    headline = models.CharField(max_length=256)
    module = models.CharField(max_length=2, choices=MODULE_CHOICES, default="UN")
    project = models.ForeignKey(settings.PROJECTS_MODEL, on_delete=models.CASCADE)
