from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from users.models import User, UserBasic, UserEducation, CollegeName


class EmailForm(forms.Form):
    email = forms.CharField(label='email')

class RegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username','first_name', 'last_name','phone_number', 'password1', 'password2', 'uploaded_document')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['uploaded_document'].required = True
        self.fields['college_code'].required = False

    def clean(self):
        super(RegistrationForm, self).clean()
        phone_number = self.cleaned_data.get('phone_number')
        if len(str(phone_number)) != 10:
            raise ValidationError(
                _(f'{phone_number} is not an valid mobile number'))

class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_image']

class CoverPhotoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['cover_image']

class CollegeCoverPhotoForm(forms.ModelForm):
    class Meta:
        model = CollegeName
        fields = ['cover_image']

class CollegeProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = CollegeName
        fields = ['profile_image']

class LoginForm(forms.Form):
    email = forms.CharField(label='email')
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name' ,'last_name', 'bio', 'designation')

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(
                _(f'{email} is not an valid email'))

        try:
            email = User.objects.exclude(pk=self.instance.pk).get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError('email "%s" is already in use.' % email)

class UserBasicForm(forms.ModelForm):
    class Meta:
        model = UserBasic
        fields = ['dob', 'city', 'country', 'about_me']

class UserNameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']

class UserEducationForm(forms.ModelForm):
    class Meta:
        model = UserEducation
        exclude = ['user']