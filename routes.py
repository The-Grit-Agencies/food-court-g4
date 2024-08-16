from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from app import db
from models import User, Restaurant, MenuItem, Order, CartItem
from forms import RegistrationForm, LoginForm, UserProfileForm, OwnerRegistrationForm, AdminRegistrationForm, MenuItemForm, OrderStatusForm, RestaurantProfileForm, EditMenuItemForm # Add OrderStatusForm here
from sqlalchemy import func


main = Blueprint('main', __name__)

@main.route('/')
def home():
    menu_items = MenuItem.query.all()
    restaurants = Restaurant.query.all()
    
    restaurant = None
    if current_user.is_authenticated and hasattr(current_user, 'restaurant'):
        restaurant = current_user.restaurant
    
    return render_template('home.html', menu_items=menu_items, restaurants=restaurants, restaurant=restaurant)



@main.route('/user/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Asante sana! Karibu Nyumbani', 'success')
        return redirect(url_for('main.login'))
    return render_template('user/register.html', form=form)

@main.route('/user/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.dashboard'))
        else:
            flash('wah wah wah pole mahn', 'danger')
    return render_template('user/login.html', form=form)

@main.route('/user/dashboard')
@login_required
def dashboard():
    return render_template('user/dashboard.html', username=current_user.username, email=current_user.email)


@main.route('/owner/register_owner', methods=['GET', 'POST'])
def register_owner():
    form = OwnerRegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data,
                    email=form.email.data,
                    password=hashed_password,
                    role='owner')
        db.session.add(user)
        db.session.commit()
        
        restaurant = Restaurant(name=form.restaurant_name.data,
                                contact=form.restaurant_contact.data,
                                owner=user)
        db.session.add(restaurant)
        db.session.commit()
        
        flash('Owner registered successfully!', 'success')
        return redirect(url_for('main.login_owner'))
    return render_template('/owner/register_owner.html', form=form)


@main.route('/owner/login_owner', methods=['GET', 'POST'])
def login_owner():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role='owner').first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.owner_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('/owner/login_owner.html', form=form)

@main.route('/admin/register_admin', methods=['GET', 'POST'])
def register_admin():
    form = AdminRegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role='admin')
        db.session.add(user)
        db.session.commit()
        flash('Admin registered successfully!', 'success')
        return redirect(url_for('main.login_admin'))
    return render_template('/admin/register_admin.html', form=form)

@main.route('/admin/login_admin', methods=['GET', 'POST'])
def login_admin():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data, role='admin').first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('/admin/login_admin.html', form=form)

@main.route('/admin', methods=['GET', 'POST'])
def admin():
    register_form = AdminRegistrationForm()
    login_form = LoginForm()
    
    if register_form.submit.data and register_form.validate_on_submit():
        hashed_password = generate_password_hash(register_form.password.data, method='pbkdf2:sha256')
        user = User(username=register_form.username.data, email=register_form.email.data, password=hashed_password, role='admin')
        db.session.add(user)
        db.session.commit()
        flash('Admin registered successfully!', 'success')
        return redirect(url_for('main.admin'))

    if login_form.submit.data and login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data, role='admin').first()
        if user and check_password_hash(user.password, login_form.password.data):
            login_user(user, remember=login_form.remember.data)
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('admin/admin.html', login_form=login_form, register_form=register_form)


@main.route('/owner/owner_dashboard')
@login_required
def owner_dashboard():
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    popular_items = db.session.query(
        MenuItem.name,
        func.count(Order.id).label('order_count')
    ).join(Order, Order.restaurant_id == current_user.restaurant.id
    ).group_by(MenuItem.name).order_by(func.count(Order.id).desc()).all()
    
    
    restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
    orders = Order.query.filter_by(restaurant_id=restaurant.id).all()
    total_orders=len(orders)
    avg_order_value = db.session.query(
    func.avg(Order.total).label('avg_order_value')
).filter_by(restaurant_id=current_user.restaurant.id).scalar()
    return render_template('/owner/owner_dashboard.html', 
                           username=current_user.username, 
                           email=current_user.email,
                           restaurant_name=restaurant.name if restaurant else None,
                           restaurant_contact=restaurant.contact if restaurant else None,
                           orders=orders, popular_items=popular_items, 
                           avg_order_value=avg_order_value, total_orders=total_orders
                            )

@main.route('/admin/admin_dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    restaurant = current_user.restaurant
    return render_template('/admin/admin_dashboard.html', username=current_user.username, email=current_user.email, restaurant=restaurant)

@main.route('/owner/menu', methods=['GET', 'POST'])
@login_required
def manage_menu():
    if current_user.is_anonymous or current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    
    restaurant = current_user.restaurant
    if not restaurant:
        flash('No restaurant associated with this account!', 'danger')
        return redirect(url_for('main.home'))
    
    form = MenuItemForm()
    if form.validate_on_submit():
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(filepath)
        else:
            filename = 'default.jpg'
        
        menu_item = MenuItem(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            image_file=filename,
            restaurant=restaurant
        )
        db.session.add(menu_item)
        db.session.commit()
        flash('Menu item added successfully!', 'success')
        return redirect(url_for('main.manage_menu'))
    
    menu_items = MenuItem.query.filter_by(restaurant=restaurant).all()
    return render_template('/owner/manage_menu.html', form=form, menu_items=menu_items, restaurant=restaurant)


@main.route('/owner/orders')
@login_required
def view_orders():
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    
    restaurant = current_user.restaurant
    orders = Order.query.filter_by(restaurant_id=restaurant.id).all()
    #orders = Order.query.all()
    return render_template('/owner/view_orders.html', orders=orders, restaurant=restaurant)

@main.route('/owner/orders/<int:order_id>/update', methods=['GET', 'POST'])
@login_required
def update_order_status(order_id):
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    restaurant = current_user.restaurant
    order = Order.query.get_or_404(order_id)
    form = OrderStatusForm()
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash('Order status updated!', 'success')
        return redirect(url_for('main.view_orders'))
    
    return render_template('/owner/update_order_status.html', form=form, order=order, restaurant=restaurant)

@main.route('/owner/profile', methods=['GET', 'POST'])
@login_required
def owner_profile():
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))

    restaurant = current_user.restaurant
    form = RestaurantProfileForm()
    
    if form.validate_on_submit():
        restaurant.name = form.name.data
        restaurant.contact = form.contact.data
        restaurant.address = form.address.data
        restaurant.opening_hours = form.opening_hours.data

        if form.logo.data:
            filename = secure_filename(form.logo.data.filename)
            filepath = os.path.join(current_app.config['LOGO_UPLOAD_FOLDER'], filename)
            try:
                form.logo.data.save(filepath)
                restaurant.logo = filename
                print(f"File saved to {filepath}")
            except Exception as e:
                print(f"Error saving file: {e}")
                flash('An error occurred while uploading the file.', 'danger')
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.owner_profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the profile. Please try again.', 'danger')
            print(f"Error during DB commit: {e}")
    
    elif request.method == 'GET':
        form.name.data = restaurant.name
        form.contact.data = restaurant.contact
        form.address.data = restaurant.address
        form.opening_hours.data = restaurant.opening_hours
    
    return render_template('/owner/profile.html', form=form, restaurant=restaurant)

@main.route('/owner/menu/<int:menu_item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_menu_item(menu_item_id):
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    restaurant = current_user.restaurant
    menu_item = MenuItem.query.get_or_404(menu_item_id)
    form = EditMenuItemForm()
    if form.validate_on_submit():
        menu_item.name = form.name.data
        menu_item.description = form.description.data
        menu_item.price = form.price.data
        menu_item.category = form.category.data
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.image.data.save(filepath)
            menu_item.image_file = filename
        db.session.commit()
        flash('Menu item updated successfully!', 'success')
        return redirect(url_for('main.manage_menu'))
    
    elif request.method == 'GET':
        form.name.data = menu_item.name
        form.description.data = menu_item.description
        form.price.data = menu_item.price
        form.category.data = menu_item.category
    
    return render_template('/owner/edit_menu_item.html', form=form, menu_item=menu_item, restaurant=restaurant)

@main.route('/owner/menu/<int:menu_item_id>/delete', methods=['POST'])
@login_required
def delete_menu_item(menu_item_id):
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))

    menu_item = MenuItem.query.get_or_404(menu_item_id)
    db.session.delete(menu_item)
    db.session.commit()
    flash('Menu item deleted successfully!', 'success')
    return redirect(url_for('main.manage_menu'))

@main.route('/owner/reports')
@login_required
def sales_reports():
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    
    restaurant = current_user.restaurant
    orders = Order.query.filter_by(restaurant_id=restaurant.id).all()
    
    # Example analytics - total sales
    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)
    
    return render_template('/owner/reports.html', total_sales=total_sales, total_orders=total_orders, restaurant=restaurant)





@main.route('/user/cart/add/<int:menu_item_id>', methods=['POST'])
@login_required
def add_to_cart(menu_item_id):
    
    MenuItem.query.get_or_404(menu_item_id)
    
    quantity = request.form.get('quantity', type=int)

    if quantity < 1:
        flash('Invalid quantity!', 'danger')
        return redirect(url_for(main.home))

    cart_item = CartItem.query.filter_by(user_id=current_user.id, menu_item_id=menu_item_id).first()

    if cart_item:
        cart_item.quantity += quantity
    else:
        new_item = CartItem(user_id=current_user.id, menu_item_id=menu_item_id, quantity=quantity)
        db.session.add(new_item)

    db.session.commit()
    flash('Item added to cart!', 'success')
    return redirect(url_for('main.home'))


@main.route('/user/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.menu_item.price * item.quantity for item in cart_items)
    return render_template('user/cart.html', cart_items=cart_items, total=total)


@main.route('/user/cart/update/<int:cart_item_id>', methods=['POST'])
@login_required
def update_cart(cart_item_id):
    cart_item = CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id != current_user.id:
        abort(403)

    quantity = request.form.get('quantity', type=int)

    if quantity < 1:
            flash('wah wah wah zii', 'danger')
            return redirect(url_for('main.view_cart'))
        
    cart_item.quantity = quantity
    db.session.commit()
    flash('Cart Updated!', 'success')
    return redirect(url_for('main.view_cart'))

@main.route('/user/cart/remove/<int:cart_item_id>', methods=['POST'])
@login_required
def remove_from_cart(cart_item_id):
    cart_item =CartItem.query.get_or_404(cart_item_id)
    if cart_item.user_id != current_user.id:
        abort(403)

    db.session.delete(cart_item)
    db.session.commit()
    flash('item removed nicely', 'success')
    return redirect(url_for('main.view_cart'))



@main.route('/user/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if request.method == 'POST':
        

        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            flash('Your cart is empty!', 'danger')
            return redirect(url_for('main.view_cart'))

        order = Order(
            customer_id=current_user.id,
            restaurant_id=cart_items[0].menu_item.restaurant_id,
            status='Processing',
            total=sum(item.menu_item.price * item.quantity for item in cart_items)
        )
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            db.session.delete(item)

        db.session.commit()

        flash('Order placed successfully!', 'success')
        return redirect(url_for('main.order_success'))

    return render_template('user/checkout.html')

@main.route('/user/order/success')
@login_required
def order_success():
    return render_template('user/order_success.html')

@main.route('/user/order/history')
@login_required
def order_history():
    orders = Order.query.filter_by(customer_id=current_user.id).all()
    return render_template('user/order_history.html', orders=orders)


@main.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    form = UserProfileForm()
    if form.validate_on_submit():
        if form.profile_picture.data:
            picture_file = secure_filename(form.profile_picture.data.filename)
            picture_path = os.path.join(current_app.config['PIC_UPLOAD_FOLDER'], picture_file)
            form.profile_picture.data.save(picture_path)
            current_user.profile_picture = picture_file

        current_user.username = form.username.data
        current_user.email = form.email.data
        if form.password.data:
            current_user.password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('main.user_profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        
    
    return render_template('user/profile.html', form=form)

@main.route('/owner/analytics')
@login_required
def owner_analytics():
    if current_user.role != 'owner':
        return redirect(url_for('index'))

    # Sales Trends: Orders grouped by day (or week/month)
    sales_trends = db.session.query(
        func.date(Order.date_created).label('date'),
        func.sum(Order.total).label('total_sales')
    ).filter_by(restaurant_id=current_user.restaurant.id).group_by('date').all()

    # Popular Items: Menu items ordered the most
    popular_items = db.session.query(
        MenuItem.name,
        func.count(Order.id).label('order_count')
    ).join(Order, Order.restaurant_id == current_user.restaurant.id
    ).group_by(MenuItem.name).order_by(func.count(Order.id).desc()).all()

    # Peak Ordering Times: Most orders placed at which time of the day
    peak_ordering_times = db.session.query(
        func.strftime('%H', Order.date_created).label('hour'),
        func.count(Order.id).label('order_count')
    ).filter_by(restaurant_id=current_user.restaurant.id).group_by('hour').order_by('hour').all()

    # Customer Insights
    frequent_customers = db.session.query(
        User.username,
        func.count(Order.id).label('order_count')
    ).join(Order, Order.customer_id == User.id
    ).filter(Order.restaurant_id == current_user.restaurant.id
    ).group_by(User.username).order_by(func.count(Order.id).desc()).all()

    avg_order_value = db.session.query(
        func.avg(Order.total).label('avg_order_value')
    ).filter_by(restaurant_id=current_user.restaurant.id).scalar()

    repeat_orders = db.session.query(
        User.username,
        func.count(Order.id).label('order_count')
    ).join(Order, Order.customer_id == User.id
    ).filter(Order.restaurant_id == current_user.restaurant.id
    ).group_by(User.username).having(func.count(Order.id) > 1).order_by(func.count(Order.id).desc()).all()

    return render_template('owner/analytics.html', 
                           sales_trends=sales_trends, 
                           popular_items=popular_items, 
                           peak_ordering_times=peak_ordering_times,
                           frequent_customers=frequent_customers,
                           avg_order_value=avg_order_value,
                           repeat_orders=repeat_orders)
@main.route('/user/menu')
def menu():
    # Fetch menu items from the database
    menu_items = MenuItem.query.all()
    return render_template('menu.html', menu_items=menu_items)

@main.route('/search')
def search():
    query = request.args.get('q')
    if query:
        restaurants = Restaurant.query.filter(Restaurant.name.ilike(f'%{query}%')).all()
        menu_items = MenuItem.query.filter(MenuItem.name.ilike(f'%{query}%')).all()
    else:
        restaurants = []
        menu_items = []

    return render_template('searchbar.html', query=query, restaurants=restaurants, menu_items=menu_items)    

@main.route('/user/restaurant/<int:restaurant_id>/menu')
def restaurant_menu(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    menu_item = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template('user/restaurant_menu.html', restaurant=restaurant, menu_item=menu_item)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
