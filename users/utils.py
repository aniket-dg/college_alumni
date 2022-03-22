import uuid

from django.core.files import File
from pathlib import Path
from PIL import Image
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import models
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import EmailMessage
from django.contrib import messages
from six import text_type
from django.core.mail.message import EmailMultiAlternatives


image_types = {
    "jpg": "JPEG",
    "jpeg": "JPEG",
    "png": "PNG",
    "gif": "GIF",
    "tif": "TIFF",
    "tiff": "TIFF",
}

class AppTokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return text_type(user.is_active) + text_type(user.pk) + text_type(timestamp)
        # if nt working try (text_type(user.is_active) + text_type(user.pk) + text_type(timestamp))


account_activation_token = AppTokenGenerator()


def send_activation_mail(request, message, user):
    current_site = get_current_site(request)
    email_body = {
        # 'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    }

    link = reverse('activate', kwargs={'uidb64': email_body['uid'], 'token': email_body['token']})

    activate_url = 'http://' + current_site.domain + link

    email_subject = 'Welcome to MahaSIG Portal'
    email_body_message = 'Please click the link and login to active your account'
    email_body = 'Hi ' + user.get_full_name() + ', ' + email_body_message + '. \n\n <a href=' + \
                 activate_url + '>activate</a>'

    email = EmailMessage(
        email_subject,
        email_body,
        settings.AUTH_USER_MODEL,
        [user.email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)
    messages.success(request, message)