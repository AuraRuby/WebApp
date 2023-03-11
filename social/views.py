from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import View
from django.views.generic.edit import UpdateView, DeleteView
from .models import Post, Comment, UserProfile, Follow
from .forms import PostForm, CommentForm, FollowForm
from django.contrib import messages
from django.http import (HttpResponse, HttpResponseBadRequest, HttpResponseRedirect)
from django.views.generic.edit import FormView



class PostListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        form = PostForm()
        comment_form = CommentForm()
        following = request.user.following.all()
        users = User.objects.exclude(id=request.user.id)
        users_not_following = users.exclude(id__in=following.values_list('following__id', flat=True))

        context = {
            'post_list': posts,
            'form': form,
            'comment_form': comment_form,
            'following': following,  # pass the following users to the template
             'users': users_not_following,
        }
        return render(request, 'social/post_list.html', context)

    def post(self, request, *args, **kwargs):
        posts = Post.objects.all().order_by('-created_on')
        form = PostForm(request.POST, request.FILES)
        comment_form = CommentForm(request.POST)
            

        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            form = PostForm()

        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.author = request.user
            new_comment.post_id = request.POST.get('post_id')
            new_comment.save()
            comment_form = CommentForm()

        following = Follow.objects.filter(follower=request.user).values_list('following', flat=True)
        follower = request.user  # get users that the logged-in user is following
        following_id = request.POST.get('following_id') # assuming the following_id is sent in the POST data
        if following_id:
            user_to_follow = User.objects.get(id=following_id)
            if not Follow.objects.filter(follower=follower, following=user_to_follow).exists():
                follow = Follow.objects.create(follower=follower, following=user_to_follow)
                follow.save()
                messages.success(request, f"You are now following {user_to_follow.username}!")
            else:
                messages.warning(request, f"You are already following {user_to_follow.username}!")
                return redirect('social:profile', pk=following_id)


        context = {
            'post_list': posts,
            'form': form,
            'comment_form': comment_form,
            'following': following,  # pass the following users to the template
        }
        return render(request, 'social/post_list.html', context)


class PostDetailView(LoginRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        form = CommentForm()
        comments = Comment.objects.filter(post=post).order_by('-created_on')

        context = {
            'post': post,
            'form': form,
            'comments': comments,
        }

        return render(request, 'social/post_detail.html', context)

    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)
        form = CommentForm(request.POST)

        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.author = request.user
            new_comment.post = post
            new_comment.save()
            form = CommentForm()
        
        comments = Comment.objects.filter(post=post).order_by('-created_on')

        context = {
            'post': post,
            'form': form,
            'comments': comments,
        }

        return render(request, 'social/post_detail.html', context)

class PostEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    fields = ['body']
    template_name = 'social/post_edit.html'
    
    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('post-detail', kwargs={'pk': pk})
    
    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'social/post_delete.html'
    success_url = reverse_lazy('post-list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'social/comment_delete.html'

    def get_success_url(self):
        pk = self.kwargs['post_pk']
        return reverse_lazy('post-detail', kwargs={'pk': pk})

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author

class ProfileView(View):
    def get(self, request, pk, *args, **kwargs):
        profile = UserProfile.objects.get(pk=pk)
        user = profile.user
        posts = Post.objects.filter(author=user).order_by('-created_on')
        following = request.user.following.all()

        context = {
            'user' : user,
            'profile' : profile,
            'posts' : posts,
            'following': following
        }
        
        return render(request, 'social/profile.html', context)

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    fields = ['name','bio','birth_date', 'location','picture']
    template_name = 'social/profile_edit.html'

    def get_success_url(self):
        pk = self.kwargs['pk']
        return reverse_lazy('profile', kwargs={'pk': pk})
    
    def test_func(self):
        profile = self.get_object()
        return self.request.user == profile.user
    

class FollowView(FormView):
    form_class = FollowForm
    success_url = reverse_lazy('post-list')
    
    def form_valid(self, form):
        following_user = form.cleaned_data['following']
        follower_user = self.request.user
        Follow.objects.get_or_create(follower=follower_user, following=following_user)
        return super().form_valid(form)


class UnfollowView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # print(f"request.POST: {request.POST}")
        # print(f"kwargs: {kwargs}")
        user_id = request.POST.get('user_id')
        print(f"userid: {user_id}")
        if user_id is not None:
            print(f"userid: {user_id}")
            user_to_unfollow = get_object_or_404(User, followers=user_id)
            print(f"follow user {user_to_unfollow}")
            Follow.objects.filter(follower=request.user, following=user_to_unfollow).delete()
            return redirect('post-list')
        else:
            return HttpResponseBadRequest("No user ID provided.")
        

class AddLike(LoginRequiredMixin, View):
    def post (self, request, pk, *args, ** kwargs):
        post = Post.objects.get(pk=pk)

        is_dislike = False

        for dislike in post.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break        

            if is_dislike:
                post.dislikes.remove(request.user)
        
        is_like = False

        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

        if not is_like:
            post.likes.add(request.user)

        if is_like:
            post.likes.remove(request.user)

        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)

class AddDislike(LoginRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        post = Post.objects.get(pk=pk)

        is_like = False

        for like in post.likes.all():
            if like == request.user:
                is_like = True
                break

            if is_like :
                post.likes.remove(request.user)

        is_dislike = False

        for dislike in post.dislikes.all():
            if dislike == request.user:
                is_dislike = True
                break

        if not is_dislike:
            post.dislikes.add(request.user)

        if is_dislike:
            post.dislikes.remove(request.user)

        next = request.POST.get('next', '/')
        return HttpResponseRedirect(next)