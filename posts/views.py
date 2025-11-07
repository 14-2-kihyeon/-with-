from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import (
    require_http_methods,
    require_safe,
    require_POST,
)
from .models import Post, Comment
from .forms import PostForm, CommentForm


def index(request):
    posts = Post.objects.all()

    context = {
        "posts": posts,
    }
    return render(request, "posts/index.html", context)


@require_safe
def detail(request, pk):
    post = Post.objects.get(pk=pk)
    comment_form = CommentForm()

    comments = post.comment_set.all()
    context = {
        "post": post,
        "comment_form": comment_form,
        "comments": comments,
    }
    return render(request, "posts/detail.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            return redirect("posts:detail", post.pk)
    else:
        form = PostForm()
    context = {
        "form": form,
    }
    return render(request, "posts/create.html", context)


@login_required
@require_POST
def delete(request, pk):
    post = Post.objects.get(pk=pk)

    post.delete()

    return redirect("posts:index")


@login_required
@require_http_methods(["GET", "POST"])
def update(request, pk):
    post = Post.objects.get(pk=pk)
    if request.user == post.user:
        if request.method == "POST":
            form = PostForm(request.POST, instance=post)
            if form.is_valid():
                form.save()
                return redirect("posts:detail", post.pk)

        else:
            form = PostForm(instance=post)
    else:
        return redirect("posts:index")
    context = {
        "post": post,
        "form": form,
    }
    return render(request, "posts/update.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def comments_create(request, pk):

    post = Post.objects.get(pk=pk)
    comment_form = CommentForm(request.POST)

    if comment_form.is_valid():
        comment = comment_form.save(commit=False)
        comment.post = post
        comment.user = request.user
        comment.save()
        return redirect("posts:detail", post.pk)
    context = {
        "post": post,
        "comment_form": comment_form,
    }
    return render(request, "posts/detail.html", context)


@login_required
@require_POST
def comments_delete(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    if request.user == comment.user:
        comment.delete()

    return redirect("posts:detail", post_pk)
