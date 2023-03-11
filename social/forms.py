from django import forms
from .models import Post, Comment, Follow
from django.contrib.auth.models import User

class PostForm(forms.ModelForm):
    body = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control border-0 p-0',
                'placeholder': 'その気持ち、シェアしましょう！',
                'rows': 3,
                'style': 'resize:none;outline:none;box-shadow:none;'
            }
        ))
    image = forms.ImageField(required=False)

    class Meta:
        model = Post
        fields = ['body', 'image']

class CommentForm(forms.ModelForm):
    comment = forms.CharField(
        label='',
        widget=forms.Textarea(
            attrs={'rows': '1',
                   'placeholder': '公開コメントを入力...',
                   }
        ))

    class Meta:
        model = Comment
        fields = ['comment']

class FollowForm(forms.ModelForm):
    following = forms.ModelChoiceField(queryset=User.objects.all())

    
    class Meta:
        model = Follow
        fields = ('following',)