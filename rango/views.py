from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required

from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query

from datetime import datetime

def index(request):
  # request the context of the request.
  # The context contains information such as the client's machine details, for example.
  context = RequestContext(request)
  
  # Query the database for a list of ALL categories currently stored.
  # Order the categories by no. likes in descending order.
  # Retrieve the top 5 only - or all if less than 5.
  # Place the list in our context_dict_dictionary which will be passed to the template engine.
  cat_list = get_category_list() 

  page_list = Page.objects.order_by('-views')[:5]

  # We loop through each category returned and create a URL attribute
  # This attribute stores an encoded URL (e.g. spaces replaced with underscores)
  #for category in cat_list:
  #  category.url = encode_url(category.name)

  context_dict = { 'cat_list': cat_list, 'pages': page_list }  
  
  if request.session.get('last_visit'):
    last_visit_time = request.session.get('last_visit')
    visits = request.session.get('visits', 0)
 
    #if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).days > 0:
    if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 5:
      request.session['visits'] = visits + 1
      request.session['last_visit'] = str(datetime.now())
    
  else:
    # The get returns None, and the session does not have a value for the last visit.
    request.session['visits'] = 1
    request.session['last_visit'] = str(datetime.now())

  print 'visits: %s, last_visit: %s' % (request.session['visits'], request.session['last_visit'])
    
  # Return response back to the user, updating any cookies that need changed.
  return render_to_response('rango/index.html', context_dict, context)

def category(request, category_name_url):
  # request our context from the request passed to us.
  context = RequestContext(request)

  # Change underscores in the category name to spaces.
  # URLs don't handle spaces well, so we encode them as underscores.
  # We can then simply replace the underscores with spaces again to get the name.
  category_name = decode_url(category_name_url)

  # Create a context dictionary which we can pass to the template rendering enginde
  # We start by containing the name of the category passed by the user.
  context_dict = { 'category_name': category_name, 
                   'category_name_url': category_name_url }

  # Populate list of categories
  context_dict['cat_list'] = get_category_list()
  
  try:
    # Can we find a category with the given name?
    # If we can't, the.get() method raises a DoesNotExist exception
    # So the .get() method returns one model instance or raises an exception.
    category = Category.objects.get(name__iexact=category_name)

    # Retrieve all of the associated pages.
    # Note that filter returns >= 1 model instance.
    pages = Page.objects.filter(category=category).order_by('-views')

    # Adds our results list to the template context under name pages.
    context_dict['pages'] = pages
    # We also add the category object from the database to the context dictionary
    # We'll use this in the template to verify that the category exists.
    context_dict['category'] = category

  except Category.DoesNotExist:
    # We get here if we didn't find the specified category.
    # Don't do anything - the template displays the 'no category' message for us
    print "Category doesn't exists"

  if request.method == 'POST':
    query = request.POST['query'].strip()
  
    if query:
      # Run our Bing function to get results list!
      context_dict['result_list']= run_query(query)

  # Go render the response and return it to the client  
  return render_to_response('rango/category.html', context_dict, context)

@login_required
def add_category(request):
  # Get the context from the request.
  context = RequestContext(request)
  
  # A HTTP POST?
  if request.method == 'POST':
    form = CategoryForm(request.POST)

    # Have we been provided with a valid form?
    if form.is_valid():
      # Save the new category to the database
      form.save(commit=True)

      # NOw call the index() view
      return index(request)
    else:
      # The supplied form contained errors - just print them to the terminal
      print form.errors
  else:
    # If the request was not a POST, display the form to enter details
    form = CategoryForm()
  
  # Bad form (or form details), no form supplied...
  # Render the form with error messages (if any)
  return render_to_response('rango/add_category.html', 
    {'form': form, 'cat_list': get_category_list()}, context)

@login_required
def like_category(request):
  context = RequestContext(request)
  likes_number = None
  if request.method == 'GET' and 'category_id' in request.GET:
    try:
      category = Category.objects.get(pk=int(request.GET['category_id']))
      category.likes += 1
      print 'Category %s, likes %d' % (category.name, category.likes)
      category.save()
      likes_number = category.likes
    except:
      print 'Category ID: %d does not exists.' % request.GET['category_id']
  return HttpResponse(likes_number)

@login_required
def add_page(request, category_name_url):
  context = RequestContext(request)

  category_name = decode_url(category_name_url)

  if request.method == 'POST':
    form = PageForm(request.POST)
    
    if form.is_valid():
      # This time we cannot commit straight away.
      # Not all fields are automatically populated!
      page = form.save(commit=False)
      
      # Retrieve the associated Category object so we can add it.
      # Wrap the code in a try block - check if the category actually exists
      try:
        cat = Category.objects.get(name=category_name)
        page.category = cat
      except Category.DoesNotExists:
        # If we get here the catgory does not exists
        # Go back and render the add category form as a way to saying the category does not exists
        return render_to_response('rango/add_category', {}, context)
      
      # Also, create a default value for the number of views.
      page.views = 0

      # with this, we can then save our new model instance
      page.save()
   
      # Now that the page is saved, display the category instead.
      return category(request, category_name_url)
  else:
    form = PageForm()

  return render_to_response('rango/add_page.html',
      {'category_name_url': category_name_url,
      'category_name': category_name, 'form': form}, context)

def register(request):
  # check if the cookie work
  if request.session.test_cookie_worked():
    print ">>> TEST COOKIE WORKED!"
    request.session.delete_test_cookie()

  # Like before, get the request's context.
  context = RequestContext(request)
  
  # A boolean value for telling the template whether the registration was successful.
  # Set to False initially. Code changes value to True when registration succeds.
  registered = request.user.is_authenticated()
  
  # If it's a HTTP POST method, we're interested in processing the form data.
  if request.method == 'POST':
    # Attempt to grab information from the raw from information
    # Note htat we make use of both UserForm and UserProfileForm
    user_form = UserForm(data=request.POST)
    profile_form = UserProfileForm(data=request.POST)

    # If the tow forms are valid...
    if user_form.is_valid() and profile_form.is_valid():
      # Save the user's form data to the database.
      user = user_form.save()

      # Now we hash the password with the set_password method.
      # Once hashed, we can update the user object.
      user.set_password(user.password)
      user.save()

      # Now sort out the UserProfile instance.
      # Since we need to se the user attribute ourselves, we set commit=False
      # This delays saving the model until we're ready to avoid integrity problems.
      profile = profile_form.save(commit=False)
      profile.user = user

      # Did the user provide a profile picture?
      # If so, we need to get it from the input form and put it in the UserProfile model.
      if 'picture' in request.FILES:
        profile.picture =  request.FILES['picture']

      # Now we save the UserProfile model instance.
      profile.save()

      # Update our variable to tell the template registration was succesful
      registered = True

    # Invalid form or forms - mistakes or something else?
    # Print problems to the terminal.
    # They'll also be shown to the user
    else:
      print user_form.errors, profile_form.errors
  # Not a HTTP POST, so we render our form using two ModelForm instances.
  # These forms will be blank, ready for user input
  else:
    user_form = UserForm()
    profile_form = UserProfileForm()
  
  # Render the template depending on the context.
  return render_to_response(
    'rango/register.html',
    {'user_form': user_form, 'profile_form': profile_form, 
     'registered': registered }, context)
  
def login_user(request):
  context = RequestContext(request)
  
  if request.method == 'POST':
    # Gather the username and password provided by the user.
    # This information is obtained from the login form.
    username = request.POST['username']
    password = request.POST['password']

    # User Django's machinery to attempt to see if the username/password
    # combination is valid - a User object is returned if it is
    user = authenticate(username=username, password=password)

    # If we have a User object, the details are correct
    # If None, no user with matching credentials was found
    if user is not None:
      # Is the account active? It could have been disabled
      if user.is_active:
        # If the account is valid and active, we can log the user in.
        # We'll send the user back to the homepage.
        login(request, user)
        return HttpResponseRedirect("/rango/")
      else:
        # An inactive account was used - no logging in!
        return HttpResponse("Your rango account is disabled")
    else:
      # Bad Login details were provided. So we can't log the user in.
      print "Invalid login details: {0}, {1}".format(username, password)
      
      # Populate error messages
      if len(username.strip()) == 0 or len(password.strip()) == 0:
        error_message = "Enter a valid username or password"
      else:
        error_message = "Invalid username or password" 

      return render_to_response('rango/login.html', 
        {'error_message': error_message}, context)
  # The request is not HTTP POST, so diplay the login form.
  # This scenario would most likely be a HTTP GET
  else:
    # No context variables to pass to the template system, hence the
    # blank dictionary object...
    return render_to_response('rango/login.html', {}, context) 
      
@login_required
def restricted(request):
  context = RequestContext(request)
  return render_to_response("rango/restricted.html", {}, context)

# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def logout_user(request):
  # Since we know the user is logged in, we can now just log them out
  logout(request)

  # Take the user back to the homepage
  return HttpResponseRedirect('/rango/')
  
def about(request):
  context = RequestContext(request)
  
  # Get the number of visited
  if request.session.get('visits'):
    counter = int(request.session.get('visits'))
  else:
    counter = 1

  context_dict = {'boldmessage': 'Hey, works in yours stuff', 'visits': counter}
  return render_to_response('rango/about.html', context_dict, context)

def search(request):
  context = RequestContext(request)
  result_list = []
  
  if request.method == 'POST':
    query = request.POST['query'].strip()
   
    if query:
      # Run our Bing function to get results list!
      result_list = run_query(query)
  return render_to_response('rango/search.html',
    {'result_list': result_list}, context)

@login_required
def profile(request):
  context = RequestContext(request)
  cat_list = get_category_list()
  context_dict = {'cat_list': cat_list}
  
  if request.user:
    try:
      profile = UserProfile.objects.get(user=request.user)
    except:
      profile = None

    context_dict['profile'] = profile
    print "UserProfile: ", profile
  return render_to_response('rango/profile.html', context_dict, context)

def track_url(request):
  context = RequestContext(request)
  redirect_url = '/rango/'
  if request.method == 'GET' and 'page_id' in request.GET:
    try:
      page_id = request.GET['page_id']
      page = Page.objects.get(id=page_id)
      page.views += 1
      print "Page: %s, views: %d" % (page.title, page.views)
      page.save()
      print "Redirecting to ", page.url
      redirect_url = page.url
    except Exception as e:
      print "Invalid page id: ", page_id
      print e
  return HttpResponseRedirect(redirect_url)

def suggest_category(request):
  context = RequestContext(request)
  cat_list = []
  if request.method == 'GET' and 'query' in request.GET:
    # retrieve all category that starts with 'query'
    query = request.GET['query']
    print 'Category starts with:', query
    top = 8
    cat_list = filter_category(starts_with=query, max_result=top)
    print 'Query result %r' % cat_list
  
  return render_to_response('rango/category_list.html', {'cat_list': cat_list}, context)

@login_required
def auto_add_page(request):
  context = RequestContext(request)
  page_list = []
  if request.method == 'GET':
    cat_id = request.GET.get('cat_id', '')
    title = request.GET.get('title', '')
    url = request.GET.get('url', '')
    if cat_id and title and url:
      try:
        category = Category.objects.get(pk=int(cat_id))
        p = Page(category=category, title=title, url=url)
        p.save()
        page_list = Page.objects.filter(category=category).order_by('-views')
        print "New Page was added: %r" % p
      except Exception as e:
        print e
    else:
      print "Request empty. category: %d, title: %s, url: %s" % (cat_id, title, url)
  else:
    print 'Invalid Request'
  return render_to_response('rango/page_list.html', {'pages': page_list}, context)

######## Helper functions ########
def get_category_list():
  cat_list = Category.objects.order_by('-likes')[:5]
  for category in cat_list:
    category.url = encode_url(category.name)
  return cat_list 

def filter_category(max_result=0, starts_with=''):
  if starts_with:
    cat_list = Category.objects.filter(name__istartswith=starts_with)
  else: 
    cat_list = Category.objects.all()

  if max_result and max_result < len(cat_list):
    cat_list = cat_list[:max_result]
  
  for cat in cat_list:
    cat.url = encode_url(cat.name)
  return cat_list

######## Utilities Functions #######
def encode_url(url_name):
  return url_name.replace(' ', '_')

def decode_url(url_name):
  return url_name.replace('_', ' ')

