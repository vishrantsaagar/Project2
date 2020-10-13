from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import *


def index(request):
    return render(request, "auctions/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

# view for dashboard
@login_required(login_url='/login')
def watchlist(request):
    winners = Winner.objects.filter(winner=request.user.username)
    # checking for watchlist
    lst = Watchlist.objects.filter(user=request.user.username)
    # list of products available in WinnerModel
    present = False
    prodlst = []
    i = 0
    if lst:
        present = True
        for item in lst:
            product = Listing.objects.get(id=item.listingid)
            prodlst.append(product)
    print(prodlst)
    return render(request, "auctions/watchlist.html", {
        "product_list": prodlst,
        "present": present,
        "products": winners
    })



def activelisting(request):
    products = Listing.objects.all()
    return render(request, "auctions/activelisting.html", {
        "products": products,
    })



def createlisting(request):
    if request.method == "POST":
        item = Listing()
        item.seller = request.user.username
        item.title = request.POST.get('title')
        item.description = request.POST.get('description')
        item.category = request.POST.get('category')
        item.starting_bid = request.POST.get('starting_bid')
        item.save()
        products = Listing.objects.all()
        return render(request, "auctions/activelisting.html", {
            "products": products,
        })
    # if request is get
    else:
        return render(request, "auctions/createlisting.html")



def categories(request):
    return render(request, "auctions/categories.html")


def viewlisting(request, product_id):
    # if the user submits his bid
    comments = Comment.objects.filter(listingid=product_id)
    if request.method == "POST":
        item = Listing.objects.get(id=product_id)
        newbid = int(request.POST.get('newbid'))
        # checking if the newbid is greater than or equal to current bid
        if item.starting_bid >= newbid:
            product = Listing.objects.get(id=product_id)
            return render(request, "auctions/viewlisting.html", {
                "product": product,
                "message": "Your Bid should be higher than the Current one.",
                "msg_type": "danger",
                "comments": comments
            })
        # if bid is greater then updating in Listings table
        else:
            item.starting_bid = newbid
            item.save()
            # saving the bid in Bid model
            bidobj = Bid.objects.filter(listingid=product_id)
            if bidobj:
                bidobj.delete()
            obj = Bid()
            obj.user = request.user.username
            obj.title = item.title
            obj.listingid = product_id
            obj.bid = newbid
            obj.save()
            product = Listing.objects.get(id=product_id)
            return render(request, "auctions/viewlisting.html", {
                "product": product,
                "message": "Your Bid is added.",
                "msg_type": "success",
                "comments": comments
            })
    # accessing individual listing GET
    else:
        product = Listing.objects.get(id=product_id)
        added = Watchlist.objects.filter(
            listingid=product_id, user=request.user.username)
        return render(request, "auctions/viewlisting.html", {
            "product": product,
            "added": added,
            "comments": comments
        })



def addtowatchlist(request, product_id):

    obj = Watchlist.objects.filter(
        listingid=product_id, user=request.user.username)
    comments = Comment.objects.filter(listingid=product_id)
    # checking if it is already added to the watchlist
    if obj:
        # if its already there then user wants to remove it from watchlist
        obj.delete()
        # returning the updated content
        product = Listing.objects.get(id=product_id)
        added = Watchlist.objects.filter(
            listingid=product_id, user=request.user.username)
        return render(request, "auctions/viewlisting.html", {
            "product": product,
            "added": added,
            "comments": comments
        })
    else:
        # if it not present then the user wants to add it to watchlist
        obj = Watchlist()
        obj.user = request.user.username
        obj.listingid = product_id
        obj.save()
        # returning the updated content
        product = Listing.objects.get(id=product_id)
        added = Watchlist.objects.filter(
            listingid=product_id, user=request.user.username)
        return render(request, "auctions/viewlisting.html", {
            "product": product,
            "added": added,
            "comments": comments
        })



def addcomment(request, product_id):
    obj = Comment()
    obj.comment = request.POST.get("comment")
    obj.user = request.user.username
    obj.listingid = product_id
    obj.save()
    # returning the updated content
    comments = Comment.objects.filter(listingid=product_id)
    product = Listing.objects.get(id=product_id)
    added = Watchlist.objects.filter(
        listingid=product_id, user=request.user.username)
    return render(request, "auctions/viewlisting.html", {
        "product": product,
        "added": added,
        "comments": comments
    })



def category(request, categ):
    # retieving all the products that fall into this category
    categ_products = Listing.objects.filter(category=categ)
    return render(request, "auctions/category.html", {
        "categ": categ,
        "products": categ_products
    })


# view when the user wants to close the bid
@login_required(login_url='/login')
def closebid(request, product_id):
    winobj = Winner()
    listobj = Listing.objects.get(id=product_id)
    obj = get_object_or_None(Bid, listingid=product_id)
    if not obj:
        message = "Deleting Bid"
        msg_type = "danger"
    else:
        bidobj = Bid.objects.get(listingid=product_id)
        winobj.owner = request.user.username
        winobj.winner = bidobj.user
        winobj.listingid = product_id
        winobj.winprice = bidobj.bid
        winobj.title = bidobj.title
        winobj.save()
        message = "Bid Closed"
        msg_type = "success"
        bidobj.delete()
    if Watchlist.objects.filter(listingid=product_id):
        watchobj = Watchlist.objects.filter(listingid=product_id)
        watchobj.delete()
    if Comment.objects.filter(listingid=product_id):
        commentobj = Comment.objects.filter(listingid=product_id)
        commentobj.delete()
    listobj.delete()
    winners = Winner.objects.all()
    return render(request, "auctions/closedlisting.html", {
        "products": winners,
        "message": message,
        "msg_type": msg_type
    })



def closedlisting(request):
    winners = Winner.objects.all()
    return render(request, "auctions/closedlisting.html", {
        "products": winners,
    })