from django.db import models


# Create your models here.


class UploadedMedia(models.Model):
    media = models.FileField()
    is_valid = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)




class UserMedia(models.Model):
    files = models.ManyToManyField(UploadedMedia, blank=True)
    access_by = models.ManyToManyField('users.User', blank=True)
    owner = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='Owner_of_media')

    def __str__(self):
        return str(self.id)


class P2pChatModel(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='user',
                             related_name='from_user', db_index=True)
    recipient = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='recipient',
                                  related_name='to_user', db_index=True)
    timestamp = models.DateTimeField('timestamp', auto_now_add=True, editable=False,
                                     db_index=True)
    body = models.TextField()

    read = models.BooleanField(default=False)

    is_delete = models.BooleanField(default=False)
    is_receiver_delete = models.BooleanField(default=False)
    clear_all = models.BooleanField(default=False)
    is_media_present = models.BooleanField(default=False)
    bucket = models.ForeignKey('chat.UserMedia', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ['-timestamp']

class GroupChatModel(models.Model):
    group_name = models.CharField(max_length=300)
    name = models.CharField(max_length=300, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_image/', null=True, blank=True)
    group_info = models.TextField(null=True, blank=True)

    admin = models.ManyToManyField('users.User', blank=True, related_name='group_admin')
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='group_created_by_user')
    created_at = models.DateTimeField(auto_now_add=True)

    member_count = models.IntegerField(default=0)
    def get_profile_img(self):
        if self.profile_image:
            return self.profile_image.url
        return ''


    def __str__(self):
        return str(self.id)



class GroupChat(models.Model):
    group = models.ForeignKey(GroupChatModel, on_delete=models.CASCADE, related_name='from_group')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='grp_user',
                             related_name='from_user_to_group', db_index=True)
    timestamp = models.DateTimeField('timestamp', auto_now_add=True, editable=False,
                                     db_index=True)
    body = models.TextField()

    user_read = models.ManyToManyField('users.User', blank=True, verbose_name='User_unread_msg_check')
    receiver_delete = models.ManyToManyField('users.User', blank=True, verbose_name='User_deleted_chat',
                                             related_name='user_receiver_delete')
    is_delete = models.BooleanField(default=False)
    is_media_present = models.BooleanField(default=False)
    bucket = models.ForeignKey('chat.UserMedia', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        ordering = ['-timestamp']

class GroupChatUnreadMessage(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='grp_user',
                             related_name='from_user_to_group_unread_msg')
    read = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)