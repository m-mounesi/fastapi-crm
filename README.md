# CRM API

A production-oriented CRM backend built with **FastAPI**, **SQLAlchemy 2**, **Alembic**, **JWT Authentication**, and **Role-Based Access Control (RBAC)**.

The project follows a layered architecture with separation between API, services, repositories, database models, schemas, and security components.

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
 operator.read
 operator.write


It might refactor to Modular monolith
