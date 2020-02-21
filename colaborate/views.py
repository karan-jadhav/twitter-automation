from django.shortcuts import render, HttpResponse

# Create your views here.

def index(request):
    context = {
        "page": "colab"
    }
    # return render(request, 'colaborate/home.html', context)
    return render(request, 'colaborate/RequestPage.html', context)
