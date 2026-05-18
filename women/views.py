from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseNotFound, Http404, \
    HttpResponsePermanentRedirect
from django.shortcuts import render,  get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import  ListView, DetailView, FormView, CreateView, UpdateView, DeleteView

from .forms import AddPostForm,  ContactForm
from .models import Women,  TagPost
from .utils import DataMixin
from django.core.cache import cache

class WomenHome(DataMixin, ListView):
    #model = Women
    template_name = 'women/index.html'
    context_object_name = 'posts'
    title_page = "Main page"
    cat_selected = 0


    def get_queryset(self):
        w_lst = cache.get('women_posts')
        if not w_lst:
            w_lst = Women.published.all().select_related('cat')
            cache.set('women_posts', w_lst, 60)

        return w_lst

@login_required
def about(request):
    contact_list = Women.published.all()
    paginator = Paginator(contact_list, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'women/about.html', {'page_obj': page_obj, 'title': 'О сайте'})

def categories(request, cat_id):
    return HttpResponse(f"<h1>Articels about categories </h1><p>id: {cat_id}</p>")

def categories_by_slug(request, cat_slug):
    return HttpResponse(f"<h1>Articels about categories </h1><p>slug: {cat_slug}</p>")

def post_detail(request):
    if request.GET:
        result = "|".join([f'{k}={v}' for k,v  in request.GET.lists()])
        return  HttpResponse(result)
    else:
        return HttpResponse("GET is empty")

def archive(request, year):
    if year > 2005:
        #raise Http404
        #return redirect('cats', 'music')
        uri = reverse('cats', args =('music',))
        #return redirect(uri)
        #return  HttpResponseRedirect('/')
        return HttpResponsePermanentRedirect(uri)

    return HttpResponse(f"<h1>Archive by years </h1><p>year: {year}</p>")

def posts_list(request, year):
    if  not (1990 <= year <= 2023):
        raise Http404
    return HttpResponse(f'posts: {year}')

def page_not_found(request, exception):
    return HttpResponseNotFound("<h1>Page Not Found</h1>")


class ShowPost(DataMixin, DetailView):
    model = Women
    template_name = 'women/post.html'
    slug_url_kwarg = 'post_slug'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, title=context['post'].title)

    def get_object(self, queryset = None):
        return get_object_or_404(Women.published, slug = self.kwargs[self.slug_url_kwarg])

class AddPage(PermissionRequiredMixin, LoginRequiredMixin, DataMixin, CreateView):
     form_class =  AddPostForm
     template_name = 'women/addpage.html'
     success_url = reverse_lazy('home')
     title_page = 'Добавление статьи'
     permission_required = 'women.add_women'

     def form_valid(self, form):
         w = form.save(commit=False)
         w.author = self.request.user
         return super().form_valid(form)


class UpdatePage(DataMixin, PermissionRequiredMixin, UpdateView):
    model = Women
    fields = ['title', 'content', 'photo', 'is_published', 'cat']
    template_name = 'women/addpage.html'
    success_url = reverse_lazy('home')
    title_page = 'Редактирование статьи'
    permission_required = 'women.change_women'


class DeletePage(DataMixin, DeleteView):
    model = Women
    #fields = ('title', 'content', 'photo', 'is_published', 'cat')
    #template_name = 'women/addpage.html'
    context_object_name = 'post'
    #template_name_suffix = 'confirm.html'
    success_url = reverse_lazy('home')
    title_page = 'Удаление статьи'

class ContactFormView(LoginRequiredMixin, DataMixin, FormView):
    form_class = ContactForm
    template_name = 'women/contact.html'
    success_url = reverse_lazy('home')
    title_page = "Обратная связь"

    def form_valid(self, form):
        print(form.cleaned_data)
        return super().form_valid(form)


def login(request):
    return HttpResponse(f'Authorization')


class WomenCategory(DataMixin, ListView):
    template_name = 'women/index.html'
    context_object_name = 'posts'
    allow_empty = False

    def get_queryset(self):
        return Women.published.filter(cat__slug = self.kwargs['cat_slug']).select_related('cat')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cat = context['posts'][0].cat
        return self.get_mixin_context(context, title='Категория - ' + cat.name, cat_selected=cat.pk)



class WomenTagView( DataMixin, ListView):
    template_name = 'women/index.html'
    context_object_name = 'posts'
    allow_empty = False

    def get_queryset(self):
        self.tag = get_object_or_404(TagPost, slug=self.kwargs['tag_slug'])
        return  self.tag.tags.filter(is_published=Women.Status.PUBLISHED).select_related('cat')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return self.get_mixin_context(context, title= f'Тег:  {self.tag.tag}')
