   # CRM API

A production-oriented CRM backend built with **FastAPI**, **SQLAlchemy 2**, **Alembic**, **JWT Authentication**, and **Role-Based Access Control (RBAC)**.

The project currently follows a layered architecture with separation between API, services, repositories, database models, schemas, and security components.

The architecture is being refactored toward a **Modular Monolith**, with the goal of organizing the system around business modules, improving cohesion, reducing coupling, and establishing clearer module boundaries.

---

## Features

### Authentication & Security

- JWT-based authentication
- Access token / Refresh token flow
- Refresh token rotation
- Token revocation support
- Password hashing with Argon2
- User authentication and authorization
- Protected API endpoints

### RBAC (Role-Based Access Control)

- Role management
- Permission management
- User-role assignment
- Role-permission mapping
- Permission-based endpoint protection

Example permissions:

- `operator.read`
- `operator.write`
