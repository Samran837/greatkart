from django.shortcuts import redirect, render
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Order, Payment, OrderProduct
from .forms import OrderForm
from carts.models import CartItem
from store.models import Product
import datetime


def payments(request):
    body = request.POST
    order = Order.objects.get(order_number=body['order_number'])

    # Create payment object
    payment = Payment(
        user=request.user,
        payment_id=body['transaction_id'],
        payment_method=body['payment_method'],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()
    print('✅ Payment saved:', payment.payment_id)

    # Update order
    order.payment = payment
    order.is_ordered = True
    order.save()
    print('✅ Order updated, is_ordered:', order.is_ordered)

    # Move cart items to order products
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct()
        order_product.order = order
        order_product.payment = payment
        order_product.user = request.user
        order_product.product = item.product
        order_product.quantity = item.quantity
        order_product.product_price = item.product.price
        order_product.ordered = True
        order_product.save()

        # Add variations to order product
        cart_item_variations = item.variations.all()
        order_product.variations.set(cart_item_variations)
        order_product.save()

        # Reduce product stock
        product = Product.objects.get(id=item.product.id)
        product.stock -= item.quantity
        product.save()

    # Clear cart
    CartItem.objects.filter(user=request.user).delete()
    print('✅ Cart cleared')

    # Send confirmation email
    try:
        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/orders_received_email.html', {
            'user': request.user,
            'order': order,
        })
        to_email = request.user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email])
        send_email.send()
        print('✅ Email sent')
    except Exception as e:
        print('❌ Email error:', e)  # won't block the redirect

    # Redirect to order complete page
    return redirect(f'/orders/order_complete/?order_number={order.order_number}&payment_id={payment.payment_id}')

def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number
            current_date = datetime.date.today().strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
        else:
            print('Form errors:', form.errors)
            return redirect('checkout')
    else:
        return redirect('checkout')


def order_complete(request):
    order_number = request.GET.get('order_number')
    transaction_id = request.GET.get('payment_id')

    # ADD THESE PRINTS
    print('order_number:', order_number)
    print('transaction_id:', transaction_id)

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order=order)
        payment = Payment.objects.get(payment_id=transaction_id)
        print('payment found:', payment)

        subtotal = sum(item.product_price * item.quantity for item in ordered_products)

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'payment': payment,
            'subtotal': subtotal,
        }
        return render(request, 'orders/order_complete.html', context)
    
    except (Order.DoesNotExist):
        print('❌ Order not found')
        return redirect('home')  # ✅ just redirect to home if order not found
    except(payment.DoesNotExist):
        print('❌ Payment not found')
        return redirect('home')