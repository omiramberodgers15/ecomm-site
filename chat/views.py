from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import ChatSession, Message
from core.models import Product

@login_required
def chat_session(request, product_id=None):
    """Get or create a chat session for the user (optionally for a product)"""
    product = None
    if product_id:
        product = get_object_or_404(Product, id=product_id)

    session, created = ChatSession.objects.get_or_create(user=request.user, product=product)
    messages = session.messages.all()
    
    return render(request, 'chat/chat.html', {'session': session, 'messages': messages})


@login_required
def send_message(request):
    """Send a chat message via AJAX"""
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        content = request.POST.get('content')

        session = get_object_or_404(ChatSession, id=session_id)
        msg = Message.objects.create(session=session, sender=request.user, content=content)

        return JsonResponse({
            'id': msg.id,
            'content': msg.content,
            'sender': msg.sender.username,
            'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)
