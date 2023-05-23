from ..base.models import TimeStampedModel
from ..blog.models import BlogImage
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.template.defaultfilters import slugify

STATUS_CHOICE = (
    ('Drafted', 'Drafted'),
    ('Published', 'Published'),
    ('Rejected', 'Rejected'),
    ('Trashed', 'Trashed'),
)

SUGGESTION_STATUS = (
    ('Open', 'Open'),
    ('In Progress', 'In Progress'),
    ('Closed', 'Closed'),
)


class ArogyamCategory(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    meta_keywords = models.TextField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="arogyam_blog_category", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(ArogyamCategory, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def category_posts(self):
        return ArogyamPost.objects.filter(category=self).count()


class ArogyamTags(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)

    def save(self, *args, **kwargs):
        tempslug = slugify(self.name)
        if self.id:
            tag = ArogyamTags.objects.get(pk=self.id)
            if tag.name != self.name:
                self.slug = create_tag_slug(tempslug)
        else:
            self.slug = create_tag_slug(tempslug)
        super(ArogyamTags, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


def create_tag_slug(tempslug):
    slugcount = 0
    while True:
        try:
            ArogyamTags.objects.get(slug=tempslug)
            slugcount += 1
            tempslug = tempslug + '-' + str(slugcount)
        except ObjectDoesNotExist:
            return tempslug


class ArogyamPost(TimeStampedModel):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="arogyam_post_creator", blank=True, null=True,
                             on_delete=models.CASCADE)
    content = models.TextField()
    domain = models.CharField(max_length=1024, null=True, blank=True)
    category = models.ForeignKey(ArogyamCategory, blank=True, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(ArogyamTags, related_name='arogyam_rel_posts', blank=True)
    posted_on = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICE, default='Drafted')
    keywords = models.TextField(max_length=5000, blank=True)
    featured_image = models.CharField(max_length=5000, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_on']

    def save(self, *args, **kwargs):
        tempslug = slugify(self.title)
        if self.id:
            blogpost = ArogyamPost.objects.get(pk=self.id)
            if blogpost.title != self.title:
                self.slug = create_slug(tempslug)
        else:
            self.slug = create_slug(tempslug)
            # self.email_to_admins_on_post_create()
        super(ArogyamPost, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def is_deletable_by(self, user):
        if self.user == user or user.is_superuser:
            return True
        return False

    def create_activity(self, user, content):
        return ArogyamPostHistory.objects.create(
            user=user, post=self, content=content
        )

    def create_activity_instance(self, user, content):
        return ArogyamPostHistory(
            user=user, post=self, content=content
        )

    def remove_activity(self):
        self.history.all().delete()

    def store_old_slug(self, old_slug):
        query = ArogyamPostSlugs.objects.filter(blog=self, slug=old_slug).values_list("slug", flat=True)
        if not (query and old_slug != self.slug):
            old_slug, _ = ArogyamPostSlugs.objects.get_or_create(blog=self, slug=old_slug)
            old_slug.is_active = False
            old_slug.save()
        active_slug, _ = ArogyamPostSlugs.objects.get_or_create(blog=self, slug=self.slug)
        active_slug.is_active = True
        active_slug.save()


def create_slug(tempslug):
    slugcount = 0
    while True:
        try:
            ArogyamPost.objects.get(slug=tempslug)
            slugcount += 1
            tempslug = tempslug + '-' + str(slugcount)
        except ObjectDoesNotExist:
            return tempslug


class ArogyamPostSlugs(models.Model):
    blog = models.ForeignKey(ArogyamPost, related_name='arogyam_slugs', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.slug


class ArogyamPostHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="arogyam_post_history", on_delete=models.CASCADE)
    post = models.ForeignKey(ArogyamPost, related_name='arogyam_history', on_delete=models.CASCADE)
    content = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return '{username} {content} {blog_title}'.format(
            username=str(self.user.get_username()),
            content=str(self.content),
            blog_title=str(self.post.title)
        )


class ArogyamVideoFile(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    link = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ArogyamDisease(TimeStampedModel):
    disease_type = models.CharField(max_length=524, blank=True, null=True)
    disease_name = models.CharField(max_length=524, blank=True, null=True)
    main_image = models.CharField(max_length=3000, null=True, blank=True)
    side_image = models.ManyToManyField(BlogImage, blank=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    content = models.TextField(blank=True)
    domain = models.CharField(max_length=1024, null=True, blank=True)
    posted_on = models.DateTimeField(blank=True, null=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class ArogyamEvents(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    event_date = models.DateTimeField(blank=True, null=True)
    event_image = models.CharField(max_length=3000, null=True, blank=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    content = models.TextField(blank=True)
    domain = models.CharField(max_length=1024, null=True, blank=True)
    posted_on = models.DateTimeField(blank=True, null=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class ArogyamContactUs(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    contact_rank = models.PositiveSmallIntegerField(blank=True, null=True)
    phone_no = models.CharField(max_length=64, blank=True, null=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    link = models.CharField(max_length=2000, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ArogyamPageSEO(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    meta_description = models.TextField(max_length=1024, null=True, blank=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class ArogyamSlider(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    silder_image = models.CharField(max_length=3000, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class ArogyamComment(models.Model):
    post = models.ForeignKey(ArogyamPost, related_name='arogyam_comments', blank=True, on_delete=models.PROTECT)
    reply_to = models.ForeignKey('self', related_name='arogyam_replies', null=True, blank=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=1000, blank=True, null=True)
    email = models.EmailField(blank=True)
    body = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return 'Comment by {} on {}'.format(self.name, self.post)


class ArogyamRating(models.Model):
    post = models.ForeignKey(ArogyamPost, related_name='arogyam_ratings', blank=True, null=True, on_delete=models.PROTECT)
    ip_address = models.CharField(max_length=500, blank=True, null=True)
    name = models.CharField(max_length=80, blank=True, null=True)
    email = models.EmailField(blank=True)
    rating = models.PositiveSmallIntegerField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return 'Rating by {} on {}'.format(self.name, self.post)


class ArogyamContactUsForm(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=128, blank=True, null=True)
    subject = models.CharField(max_length=5000, blank=True, null=True)
    description = models.TextField(max_length=10000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class ArogyamSuggestionBox(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=128, blank=True, null=True)
    subject = models.CharField(max_length=5000, blank=True, null=True)
    description = models.TextField(max_length=10000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=128, choices=SUGGESTION_STATUS, default="Open")
