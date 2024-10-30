from django.shortcuts import render

def tester(request):
    return render(request, 'index.html')
