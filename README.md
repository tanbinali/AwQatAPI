# AwQat Gamestore API

**AwQat Gamestore** is a Django REST Framework backend for a digital gaming e-commerce platform. It enables users to purchase in-game currencies and digital gaming services using local payment methods, solving the accessibility gap for gamers without international credit cards. The API manages users, games, categories, carts, orders, and reviews with role-based permissions.

## Team: Jade Codex

* A project for the Web Development Course CSE 242.

## Features

* User registration, authentication (JWT), and profile management.
* Role-based access control (Admin and Customer).
* CRUD operations for Games and Categories.
* Shopping cart system linked to user accounts.
* Order management with automated status tracking (e.g., updating to PAID).
* Local payment integration (SSLCommerz).
* Game reviews with a rating system.
* Swagger and Redoc API documentation.

## Tech Stack

* **Backend:** Python, Django, Django REST Framework
* **Database:** PostgreSQL
* **Authentication:** Djoser, Simple JWT
* **Documentation:** DRF-YASG (Swagger / OpenAPI)
* **Frontend:** ReactJS (Handled in a separate repository)

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/tanbinali/AwQat-API.git
cd AwQat-API

```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

```

3. **Install dependencies**

```bash
pip install -r requirements.txt

```

4. **Set up environment variables**

Create a `.env` file in the root directory and configure your variables:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True
DB_ENGINE=django.db.backends.postgresql
DB_NAME=awqat_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
USE_CLOUDINARY=False

```

## Running the Server

Apply the database migrations, create an admin user, and start the development server.

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

```

## API Documentation

Interactive API documentation is built-in. Start the server and navigate to:

* Swagger UI: `/swagger/`
* ReDoc UI: `/redoc/`

## Usage

* Register and log in users via the `/auth/` endpoints.
* Admin users can create and manage games, categories, and orders via the Django Admin panel or administrative API routes.
* Customers can browse the game catalog, add items to their cart, proceed to checkout, and leave reviews for purchased games.
* Payments process through local gateways, updating the order status upon success.

## Permissions

* **Admin:** Full access to all endpoints, inventory management, and user data.
* **Customer:** Restricted access to their own cart, orders, and profile, plus the ability to leave reviews.
* **Anonymous:** Read-only access to categories, games, and public reviews.

## Project Structure

* `users/`: User models, authentication serializers, and profile logic.
* `games/`: Game models, categories, and inventory management.
* `orders/`: Shopping cart, checkout process, and order history.
* `reviews/`: Game ratings and user feedback.
* `api/`: Main routing, shared utilities, and global permissions.

## Future Improvements

* Email notifications for successful orders and status updates.
* Advanced search and filtering capabilities for the game catalog.
* Admin analytics dashboard for sales tracking.
* Webhook integrations for real-time payment status updates.

## License

This project is licensed under the BSD License. See the LICENSE file for details.