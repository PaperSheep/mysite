import datetime
from django.shortcuts import render, redirect
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.db.models import Sum
from django.core.cache import cache
from django.contrib import auth
from django.contrib.auth.models import User
from django.urls import reverse

from read_statistics.utils import get_seven_days_read_data, get_today_hot_data, get_yesterday_hot_data
from blog.models import Blog
from .forms import LoginForm, RegForm


def get_7_days_hot_blogs():
    today = timezone.now().date()
    date = today - datetime.timedelta(days=7)
    blogs = Blog.objects \
                .filter(read_details__date__lt=today, read_details__date__gte=date) \
                .values('id', 'title') \
                .annotate(read_num_sum=Sum('read_details__read_num')) \
                .order_by('-read_num_sum')
    return blogs[:7]

def set_or_get_data_cache(data_name, func, blog_content_type):
    data = cache.get(data_name)
    if data is None:
        data = func() if blog_content_type is None else func(blog_content_type)
        cache.set(data_name, data, 3600)
    return data

def home(request):
    blog_content_type = ContentType.objects.get_for_model(Blog)
    # 获取7天热门数据的缓存数据
    dates_and_read_nums = set_or_get_data_cache('dates_and_read_nums', get_seven_days_read_data, blog_content_type)
    # 获取昨天热门博客的缓存数据
    hot_blogs_for_yesterday_day = set_or_get_data_cache('hot_blogs_for_yesterday_day', get_yesterday_hot_data, blog_content_type)
    # 获取7天热门博客的缓存数据
    hot_blogs_for_7_days = set_or_get_data_cache('hot_blogs_for_7_days', get_7_days_hot_blogs, None)

    context = {}
    context['dates'] = dates_and_read_nums['dates']
    context['read_nums'] = dates_and_read_nums['read_nums']
    context['today_hot_data'] = get_today_hot_data(blog_content_type)
    context['yesterday_hot_data'] = hot_blogs_for_yesterday_day
    context['hot_blogs_for_7_days'] = hot_blogs_for_7_days
    return render(request, 'home.html', context)

def login(request):
    if request.method == 'POST':
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user = login_form.cleaned_data['user']
            auth.login(request, user)
            return redirect(request.GET.get('from', reverse('home')))  # 跳转回刚才的页面
        # 增加clean错误信息的第二种方法
        # else:
        #     login_form.add_error(None, '用户名或密码不正确')
    else:
        login_form = LoginForm()

    context = {}
    context['login_form'] = login_form
    return render(request, 'login.html', context)

def register(request):
    if request.method == 'POST':
        reg_form = RegForm(request.POST)
        # is_valid()这个函数会自动调用所有的clean函数
        if reg_form.is_valid():
            username = reg_form.cleaned_data['username']
            email =reg_form.cleaned_data['email']
            password = reg_form.cleaned_data['password']
            # 创建用户
            user = User.objects.create_user(username, email, password)
            user.save()
            # 登录用户
            user = auth.authenticate(username=username, password=password)
            auth.login(request, user)
            # 使用 redirect 进行代码复用
            return redirect(request.GET.get('from', reverse('home')))
    else:
        reg_form = RegForm()

    context = {}
    context['reg_form'] = reg_form
    return render(request, 'register.html', context)
