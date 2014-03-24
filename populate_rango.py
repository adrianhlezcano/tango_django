import os

def populate():
  python_cat = add_cat(name='Python', views=128, likes=64)

  add_page(cat=python_cat, title='Official Python Tutorial', url='http://docs.python.org/2/tutorial/')
  add_page(cat=python_cat, title='How to think like a computer scientist', url='http://www.greenteapress.com/thinkpython/')
  add_page(cat=python_cat, title='Learn Python in 10 Minutos', url='http://www.korokithakis.net/tutorials/python/')

  django_cat = add_cat(name='Django', views=64, likes=32)
  add_page(cat=django_cat, title='Official Django Tutorial', url='http://docs.djangoproject.com/en/1.6/intro/tutorial01/')
  add_page(cat=django_cat, title='Django Rocks', url='http://djangorocks.com/')
  add_page(cat=django_cat, title='How to tango with Django', url='http://tangowithdjango/')

  frame_cat = add_cat(name='Other Frameworks', views=32, likes=16)
  add_page(cat=frame_cat, title='Bottle', url='http://bottlepy.org/docs/dev/')
  add_page(cat=frame_cat, title='Flask', url='http://flask.pocoo.org/')
 
  # Print out what we have added to the user.
  for c in Category.objects.all():
    for p in Page.objects.filter(category=c):
      print "{0} - {1}".format(str(c), str(p))

def add_cat(name, views, likes):
  c = Category.objects.get_or_create(name=name, views=views, likes=likes)[0]
  return c

def add_page(cat, title, url, views=0):
  p = Page.objects.get_or_create(category=cat, title=title, url=url, views=views)[0]
  return p

# Start execution here!
if __name__ == '__main__':
  print 'Starting Rango population script...'
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tango_django.settings')
  import tango_django
  from rango.models import Category, Page
  populate()
