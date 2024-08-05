from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from . import db
from .models import User, Restaurant, MenuItem, Order  
from .forms import RegistrationForm, LoginForm, OwnerRegistrationForm, AdminRegistrationForm, MenuItemForm, OrderStatusForm, RestaurantProfileForm, EditMenuItemForm # Add OrderStatusForm here



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
        hashed_password = generate_password_hash(form.password.data, method='sha256')
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
        hashed_password = generate_password_hash(form.password.data, method='sha256')
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
        hashed_password = generate_password_hash(form.password.data, method='sha256')
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

@main.route('/owner/owner_dashboard')
@login_required
def owner_dashboard():
    if current_user.role != 'owner':
        flash('Access unauthorized!', 'danger')
        return redirect(url_for('main.home'))
    
    restaurant = Restaurant.query.filter_by(owner_id=current_user.id).first()
    return render_template('/owner/owner_dashboard.html', 
                           username=current_user.username, 
                           email=current_user.email,
                           restaurant_name=restaurant.name if restaurant else None,
                           restaurant_contact=restaurant.contact if restaurant else None)

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

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
