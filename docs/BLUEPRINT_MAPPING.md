# Blueprint Mapping Documentation

## Blueprint Tanımları

### 1. Auth Blueprint
- **Name**: `auth`
- **URL Prefix**: `/`
- **File**: `routes/auth.py`
- **Routes**:
  - `/login` - Login page
  - `/register` - Register page
  - `/register_with_invite` - Register with invite token
  - `/logout` - Logout

### 2. Dashboard Blueprint
- **Name**: `dashboard`
- **URL Prefix**: `/`
- **File**: `routes/dashboard.py`
- **Routes**:
  - `/` - Main dashboard (index)
  - `/monthly_dashboard` - Monthly dashboard

### 3. Transactions Blueprint
- **Name**: `transactions`
- **URL Prefix**: `/`
- **File**: `routes/transactions.py`
- **Routes**:
  - `/transactions` - Transaction list
  - `/add_t` - Add transaction
  - `/edit_t/<int:id>` - Edit transaction
  - `/delete_t/<int:id>` - Delete transaction

### 4. Assets Blueprint
- **Name**: `assets`
- **URL Prefix**: `/`
- **File**: `routes/assets.py`
- **Routes**:
  - `/assets_view` - Asset view page
  - `/assets_management` - Asset management
  - `/investment_performance` - Investment performance
  - `/new_asset` - Create new asset
  - `/edit_asset/<int:id>` - Edit asset
  - `/del_asset/<int:id>` - Delete asset

### 5. Plans Blueprint
- **Name**: `plans`
- **URL Prefix**: `/`
- **File**: `routes/plans.py`
- **Routes**:
  - `/plans` - Recurring plans list
  - `/add_plan` - Add recurring plan
  - `/edit_plan/<int:id>` - Edit recurring plan
  - `/delete_plan/<int:id>` - Delete recurring plan

### 6. Categories Blueprint
- **Name**: `categories`
- **URL Prefix**: `/`
- **File**: `routes/categories.py`
- **Routes**:
  - `/categories` - Categories management

### 7. Export Blueprint
- **Name**: `export`
- **URL Prefix**: `/`
- **File**: `routes/export.py`
- **Routes**:
  - `/export` - Export data

### 8. Settings Blueprint
- **Name**: `settings`
- **URL Prefix**: `/`
- **File**: `routes/settings.py`
- **Routes**:
  - `/settings` - Settings page

### 9. Strategy Blueprint
- **Name**: `strategy`
- **URL Prefix**: `/`
- **File**: `routes/strategy.py`
- **Routes**:
  - `/strategy` - Strategy center

### 10. Financial Education Blueprint
- **Name**: `financial_education`
- **URL Prefix**: `/`
- **File**: `routes/financial_education.py`
- **Routes**:
  - `/financial_education` - Financial education page

### 11. Admin Blueprint
- **Name**: `admin`
- **URL Prefix**: `/admin`
- **File**: `routes/admin.py`
- **Routes**:
  - `/admin` - Admin dashboard
  - `/admin/login` - Admin login
  - `/admin/tenants` - Tenant management
  - `/admin/users` - User management

### 12. Tenant Blueprint
- **Name**: `tenant`
- **URL Prefix**: `/tenant`
- **File**: `routes/tenant.py`
- **Routes**:
  - `/tenant/users` - Tenant user list
  - `/tenant/users/<user_id>/toggle_status` - Toggle user status
  - `/tenant/users/<user_id>/change_role` - Change user role
  - `/tenant/invite` - Invite user
  - `/tenant/invites` - Invite list

## URL Pattern Examples

### Auth Routes
- `url_for('auth.login')` → `/login`
- `url_for('auth.register')` → `/register`
- `url_for('auth.register_with_invite', token='abc123')` → `/register_with_invite?token=abc123`

### Dashboard Routes
- `url_for('dashboard.index')` → `/`
- `url_for('dashboard.monthly_dashboard')` → `/monthly_dashboard`

### Tenant Routes (with prefix)
- `url_for('tenant.users')` → `/tenant/users`
- `url_for('tenant.invite')` → `/tenant/invite`
- `url_for('tenant.invites')` → `/tenant/invites`

### Admin Routes (with prefix)
- `url_for('admin.index')` → `/admin`
- `url_for('admin.tenants')` → `/admin/tenants`
- `url_for('admin.users')` → `/admin/users`

## Common Issues and Solutions

### 404 Errors
1. **Wrong blueprint name**: Ensure the blueprint name in `url_for()` matches the actual blueprint name
2. **Missing URL prefix**: Routes with `url_prefix` require the prefix in the actual URL
3. **Wrong route function name**: Ensure the function name matches the route definition

### Example Fixes
- ❌ `url_for('tenant.users_list')` → ✅ `url_for('tenant.users')`
- ❌ `url_for('users')` → ✅ `url_for('tenant.users')`
- ❌ `url_for('admin.user_management')` → ✅ `url_for('admin.users')`

## Blueprint Registration Order
Blueprints are registered in `routes/__init__.py` in the following order:
1. auth
2. settings
3. dashboard
4. transactions
5. assets
6. plans
7. categories
8. export
9. strategy
10. financial_education
11. admin
12. tenant

This order is important for route resolution and template context availability.
