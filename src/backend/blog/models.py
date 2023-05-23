import datetime

from ..base.models import TimeStampedModel, upload_blog_image
from ..patients.models import Patients, City, State, Country
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


class Category(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=500, blank=True, null=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    meta_keywords = models.TextField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="blog_category", on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def category_posts(self):
        return Post.objects.filter(category=self).count()


class Tags(TimeStampedModel):
    name = models.CharField(max_length=20, unique=True)
    slug = models.CharField(max_length=20, unique=True)

    def save(self, *args, **kwargs):
        tempslug = slugify(self.name)
        if self.id:
            tag = Tags.objects.get(pk=self.id)
            if tag.name != self.name:
                self.slug = create_tag_slug(tempslug)
        else:
            self.slug = create_tag_slug(tempslug)
        super(Tags, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


def create_tag_slug(tempslug):
    slugcount = 0
    while True:
        try:
            Tags.objects.get(slug=tempslug)
            slugcount += 1
            tempslug = tempslug + '-' + str(slugcount)
        except ObjectDoesNotExist:
            return tempslug


class BlogImage(TimeStampedModel):
    name = models.CharField(max_length=1000, blank=True, null=True)
    image = models.FileField(upload_to=upload_blog_image, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def image_path(self):
        return self.image.name


class Post(TimeStampedModel):
    title = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="post_creator", blank=True, null=True,
                             on_delete=models.CASCADE)
    content = models.TextField()
    domain = models.CharField(max_length=1024, null=True, blank=True)
    category = models.ForeignKey(Category, blank=True, null=True, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tags, related_name='rel_posts', blank=True)
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
            blogpost = Post.objects.get(pk=self.id)
            if blogpost.title != self.title:
                self.slug = create_slug(tempslug)
        else:
            self.slug = create_slug(tempslug)
            self.email_to_admins_on_post_create()
        super(Post, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    def is_deletable_by(self, user):
        if self.user == user or user.is_superuser:
            return True
        return False

    def create_activity(self, user, content):
        return PostHistory.objects.create(
            user=user, post=self, content=content
        )

    def create_activity_instance(self, user, content):
        return PostHistory(
            user=user, post=self, content=content
        )

    def remove_activity(self):
        self.history.all().delete()

    def store_old_slug(self, old_slug):
        query = Post_Slugs.objects.filter(blog=self, slug=old_slug).values_list("slug", flat=True)
        if not (query and old_slug != self.slug):
            old_slug, _ = Post_Slugs.objects.get_or_create(blog=self, slug=old_slug)
            old_slug.is_active = False
            old_slug.save()
        active_slug, _ = Post_Slugs.objects.get_or_create(blog=self, slug=self.slug)
        active_slug.is_active = True
        active_slug.save()


def create_slug(tempslug):
    slugcount = 0
    while True:
        try:
            Post.objects.get(slug=tempslug)
            slugcount += 1
            tempslug = tempslug + '-' + str(slugcount)
        except ObjectDoesNotExist:
            return tempslug


class Post_Slugs(models.Model):
    blog = models.ForeignKey(Post, related_name='slugs', on_delete=models.CASCADE)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.slug


class PostHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='history', on_delete=models.CASCADE)
    content = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return '{username} {content} {blog_title}'.format(
            username=str(self.user.get_username()),
            content=str(self.content),
            blog_title=str(self.post.title)
        )


class Image_File(models.Model):
    upload = models.FileField(upload_to=upload_blog_image, blank=True, null=True)
    date_created = models.DateTimeField(default=datetime.datetime.now)
    is_image = models.BooleanField(default=True)
    thumbnail = models.FileField(upload_to=upload_blog_image, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.date_created


class VideoFile(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    link = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class Events(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    event_date = models.DateTimeField(blank=True, null=True)
    event_image = models.CharField(max_length=3000, null=True, blank=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    content = models.TextField(blank=True)
    domain = models.CharField(max_length=1024, null=True, blank=True)
    posted_on = models.DateTimeField(blank=True, null=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class ContactUs(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    contact_rank = models.PositiveSmallIntegerField(blank=True, null=True)
    phone_no = models.CharField(max_length=64, blank=True, null=True)
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    link = models.CharField(max_length=2000, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class PageSEO(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    meta_description = models.TextField(max_length=1024, null=True, blank=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class Slider(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    name = models.CharField(max_length=256, blank=True, null=True)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    silder_image = models.CharField(max_length=3000, null=True, blank=True)
    is_active = models.BooleanField(default=True)


class Facility(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class LandingPageVideo(TimeStampedModel):
    name = models.CharField(max_length=256, blank=True, null=True)
    rank = models.PositiveSmallIntegerField(blank=True, null=True)
    link = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class LandingPageContent(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    image = models.CharField(max_length=3000, null=True, blank=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', blank=True, on_delete=models.PROTECT)
    reply_to = models.ForeignKey('self', related_name='replies', null=True, blank=True, on_delete=models.PROTECT)
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


class Rating(models.Model):
    post = models.ForeignKey(Post, related_name='ratings', blank=True, null=True, on_delete=models.PROTECT)
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


class ContactUsForm(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=128, blank=True, null=True)
    subject = models.CharField(max_length=5000, blank=True, null=True)
    description = models.TextField(max_length=10000, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class ProductContent(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    image = models.CharField(max_length=3000, null=True, blank=True)
    price = models.FloatField(blank=True, null=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class ProductDetail(TimeStampedModel):
    product = models.ForeignKey(ProductContent, blank=True, null=True, on_delete=models.PROTECT)
    quantity = models.IntegerField(blank=True, null=True)


class ProductSale(TimeStampedModel):
    patient = models.ForeignKey(Patients, blank=True, null=True, on_delete=models.PROTECT)
    products = models.ManyToManyField(ProductDetail, blank=True)
    referal_code = models.CharField(max_length=50, blank=True, null=True)
    promo_code = models.CharField(max_length=50, blank=True, null=True)
    discount_value = models.FloatField(blank=True, null=True)
    total_amount = models.FloatField(blank=True, null=True)
    name = models.CharField(max_length=524, blank=True, null=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    mobile_no = models.CharField(max_length=100, null=True, blank=True)
    alt_mobile = models.CharField(max_length=100, null=True, blank=True)
    address1 = models.CharField(max_length=1000, null=True, blank=True)
    address2 = models.CharField(max_length=1000, null=True, blank=True)
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.PROTECT)
    state = models.ForeignKey(State, blank=True, null=True, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.PROTECT)
    pincode = models.CharField(max_length=100, null=True, blank=True)
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    payment_status = models.CharField(max_length=100, null=True, blank=True, default="Failed")
    is_active = models.BooleanField(default=True)


class TherapyContent(TimeStampedModel):
    title = models.CharField(max_length=524, blank=True, null=True)
    image = models.CharField(max_length=3000, null=True, blank=True)
    content = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class SuggestionBox(TimeStampedModel):
    name = models.CharField(max_length=1024, blank=True, null=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=128, blank=True, null=True)
    subject = models.CharField(max_length=5000, blank=True, null=True)
    description = models.TextField(max_length=10000, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=128, choices=SUGGESTION_STATUS, default="Open")


class SymptomList(TimeStampedModel):
    name = models.CharField(max_length=524, blank=True, null=True)
    is_active = models.BooleanField(default=True)


class DiseaseCategory(TimeStampedModel):
    category = models.CharField(max_length=524, blank=True, null=True)
    main_image = models.CharField(max_length=3000, null=True, blank=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    content = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    domain = models.CharField(max_length=1024, null=True, blank=True)
    posted_on = models.DateTimeField(blank=True, null=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class DiseaseList(TimeStampedModel):
    category = models.ForeignKey(DiseaseCategory, blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(max_length=524, blank=True, null=True)
    symptoms = models.ManyToManyField(SymptomList, blank=True)
    is_active = models.BooleanField(default=True)


class Disease(TimeStampedModel):
    disease = models.ForeignKey(DiseaseList, blank=True, null=True, on_delete=models.PROTECT)
    main_image = models.CharField(max_length=3000, null=True, blank=True)
    meta_description = models.TextField(max_length=160, null=True, blank=True)
    content = models.TextField(blank=True)
    treatment = models.TextField(blank=True)
    domain = models.CharField(max_length=1024, null=True, blank=True)
    posted_on = models.DateTimeField(blank=True, null=True)
    keywords = models.TextField(max_length=5000, blank=True)
    is_active = models.BooleanField(default=True)


class Medicines(TimeStampedModel):
    medicine_type = models.CharField(max_length=160, null=True, blank=True)
    image = models.CharField(max_length=1024, null=True, blank=True)
    description = models.TextField(max_length=3000, null=True, blank=True)
    name = models.CharField(max_length=1024, blank=True, null=True)
    dosage = models.CharField(max_length=1024, blank=True, null=True)
    frequency = models.CharField(max_length=1024, blank=True, null=True)
    duration = models.CharField(max_length=1024, blank=True, null=True)
    duration_type = models.CharField(max_length=1024, blank=True, null=True)
    instruction = models.CharField(max_length=1024, blank=True, null=True)
    benefit = models.TextField(max_length=3000, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    before_food = models.BooleanField(default=True)
    after_food = models.BooleanField(default=True)


class Conversion(TimeStampedModel):
    diseases = models.ManyToManyField(DiseaseList, blank=True)
    allopath = models.ManyToManyField(Medicines, blank=True, related_name="allopath")
    ayurveda = models.ManyToManyField(Medicines, blank=True, related_name="ayurveda")
    is_active = models.BooleanField(default=True)


class DynamicData(TimeStampedModel):
    language = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    sub_category = models.CharField(max_length=100, blank=True, null=True)
    image = models.CharField(max_length=1024, blank=True, null=True)
    title = models.CharField(max_length=1024, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


class CareersApplication(TimeStampedModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    mobile1 = models.CharField(max_length=100, blank=True, null=True)
    mobile2 = models.CharField(max_length=100, blank=True, null=True)
    address1 = models.CharField(max_length=1000, blank=True, null=True)
    address2 = models.CharField(max_length=1000, blank=True, null=True)
    job = models.ForeignKey(DynamicData, blank=True, null=True, on_delete=models.PROTECT)
    city = models.ForeignKey(City, blank=True, null=True, on_delete=models.PROTECT)
    state = models.ForeignKey(State, blank=True, null=True, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, blank=True, null=True, on_delete=models.PROTECT)
    relocation = models.BooleanField(default=False)
    pincode = models.CharField(max_length=100, blank=True, null=True)
    resume = models.CharField(max_length=100, blank=True, null=True)
    why_hire = models.CharField(max_length=10000, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True, default="Applied")
    is_active = models.BooleanField(default=True)
