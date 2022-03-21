from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=200)
    icon = models.CharField(max_length=100, default="mdi mdi-pencil")

    def __str__(self):
        return f"{self.name}"

VIEW_CHOICES = (
    ('Only Friends', 'Only Friends'),
    ('Only College','Only College'),
    ('All Portal', 'All Portal')
)

class ViewArea(models.Model):
    name = models.CharField(max_length=100, choices=VIEW_CHOICES)
    is_for_student = models.BooleanField(default=True)
    is_for_college = models.BooleanField(default=False)
    is_for_industry = models.BooleanField(default=False)

class Post(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image1 = models.ImageField(upload_to='post_image/', null=True, blank=True)
    image2 = models.ImageField(upload_to='post_image/', null=True, blank=True)
    image3 = models.ImageField(upload_to='post_image/', null=True, blank=True)
    image4 = models.ImageField(upload_to='post_image/', null=True, blank=True)
    image5 = models.ImageField(upload_to='post_image/', null=True, blank=True)
    liked_by = models.ManyToManyField('users.User', blank=True, related_name='liked_by')
    timestamp = models.DateTimeField(auto_now_add=True)
    view_area = models.ForeignKey(ViewArea, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.id}"

    class Meta:
        ordering = ['-timestamp']

class PostComment(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comment')
    comment = models.TextField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}"

    class Meta:
        ordering = ['-id']