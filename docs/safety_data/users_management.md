# User and Authorization API Endpoints

## Table of Contents
- [Authorization Endpoints](#authorization-endpoints)
- [User Information Endpoints](#user-information-endpoints)
- [User Update Endpoints](#user-update-endpoints)
- [Role Management Endpoints](#role-management-endpoints)
- [Grant Management Endpoints](#grant-management-endpoints)
- [Organization Management Endpoints](#organization-management-endpoints)
- [User Deletion Endpoint](#user-deletion-endpoint)
- [Common Error Responses](#common-error-responses)

---

## Authorization Endpoints

### OAuth Authorization
**`GET /authorize/<provider>`**

Initiates OAuth flow with a provider (currently only Google is supported).

**Parameters:**
- `provider` (path, required): OAuth provider name (only "google" supported)
- `redirect_url` (query, optional): URL to redirect after successful login

**Response:** Redirects to OAuth provider

**Example:**
```http
GET /authorize/google?redirect_url=https://example.com/dashboard
```

---

### OAuth Callback
**`GET /callback/<provider>`** (Anyway app) or **`GET /sd-callback/<provider>`** (Safety Data app)

OAuth callback endpoint after provider authentication. Creates or updates user and logs them in.

**Parameters:**
- `provider` (path, required): OAuth provider name (currently only "google" supported)
- `state` (query): Base64-encoded JSON with redirect URL

**Response:** HTTP 302 redirect to application with user logged in

**Note**: The callback endpoint determines which app the user belongs to:
- `/callback/google` → creates/finds user with `app=0` (Anyway)
- `/sd-callback/google` → creates/finds user with `app=1` (Safety Data)

Users with the same email can have separate accounts in each app, allowing concurrent login.

---

### Logout
**`GET /logout`**

Logs out the current user.

**Parameters:** None

**Response:**
```http
Status: 200 OK
```

---

## User Information Endpoints

### Get Current User Info
**`GET /user/info`**

Get information about the currently logged-in user.

**Authentication:** Required (Authenticated role)

**Parameters:** None

**Example Response:**
```json
{
  "id": 123,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+972501234567",
  "user_type": "individual",
  "user_url": "https://example.com",
  "user_desc": "Traffic safety researcher",
  "is_user_completed_registration": true,
  "oauth_provider": "google",
  "oauth_provider_user_name": "John Doe",
  "oauth_provider_user_picture_url": "https://lh3.googleusercontent.com/...",
  "user_register_date": "2024-01-15T10:30:00",
  "user_last_login_date": "2024-11-20T08:15:00"
}
```

---

### Check If User Is Logged In
**`GET /user/is_user_logged_in`**

Check if a user is currently logged in.

**Authentication:** None

**Parameters:** None

**Example Response:**
```json
{
  "is_user_logged_in": true
}
```

---

### Get All Users Info (Admin)
**`GET /user/get_all_users_info`**

Get information about all users in the system.

**Authentication:** Required (Admin role)

**Parameters:** None

**Example Response:**
```json
[
  {
    "id": 123,
    "email": "user1@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+972501234567",
    "user_type": "individual",
    "roles": ["authenticated", "editor"],
    "is_active": true,
    "is_user_completed_registration": true,
    "user_register_date": "2024-01-15T10:30:00",
    "user_last_login_date": "2024-11-20T08:15:00"
  },
  {
    "id": 124,
    "email": "user2@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "+972509876543",
    "user_type": "organization",
    "roles": ["authenticated"],
    "is_active": true,
    "is_user_completed_registration": true,
    "user_register_date": "2024-02-20T14:20:00",
    "user_last_login_date": "2024-11-19T16:45:00"
  }
]
```

---

## User Update Endpoints

### Update Current User
**`POST /user/update`**

Update current user's information. Also used for first-time registration completion.

**Authentication:** Required (Authenticated role)

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "newemail@example.com",
  "phone": "+972501234567",
  "user_type": "individual",
  "user_url": "https://example.com",
  "user_desc": "Traffic safety researcher",
  "is_user_completed_registration": true
}
```

**Field Descriptions:**
- `first_name` (string, optional): User's first name
- `last_name` (string, optional): User's last name
- `email` (string, optional): User's email address (must be valid email format)
- `phone` (string, optional): User's phone number (must be valid format)
- `user_type` (string, optional): Type of user ("individual" or "organization")
- `user_url` (string, optional): User's website URL
- `user_desc` (string, optional): User description
- `is_user_completed_registration` (boolean, optional): Registration completion status

**Success Response:**
```http
Status: 200 OK
```

**Error Response:**
```json
{
  "error_code": 1001,
  "error_message": "Invalid email format"
}
```

---

### Admin Update User
**`POST /user/update_user`**

Admin endpoint to update any user's information.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "user_current_email": "currentemail@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "email": "newemail@example.com",
  "phone": "+972501234567",
  "user_type": "organization",
  "user_url": "https://example.com",
  "user_desc": "Updated description",
  "is_user_completed_registration": true
}
```

**Field Descriptions:**
- `user_current_email` (string, required): Current email of the user to update
- Other fields same as "Update Current User" endpoint

**Success Response:**
```http
Status: 200 OK
```

---

### Change User Active Mode (Admin)
**`POST /user/change_user_active_mode`**

Enable or disable a user account.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "user@example.com",
  "is_active": false
}
```

**Field Descriptions:**
- `email` (string, required): Email of the user to update
- `is_active` (boolean, required): Active status (true = enabled, false = disabled)

**Success Response:**
```http
Status: 200 OK
```

---

## Role Management Endpoints

### Add Role (Admin)
**`POST /user/add_role`**

Create a new role in the system.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "name": "editor",
  "description": "Can edit content"
}
```

**Field Descriptions:**
- `name` (string, required): Role name (2+ characters, alphanumeric with hyphens/underscores)
- `description` (string, optional): Role description

**Success Response:**
```http
Status: 200 OK
```

---

### Add User to Role (Admin)
**`POST /user/add_to_role`**

Add a user to a specific role.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "user@example.com",
  "role": "editor"
}
```

**Field Descriptions:**
- `email` (string, required): Email of the user
- `role` (string, required): Name of the role to add

**Success Response:**
```http
Status: 200 OK
```

---

### Remove User from Role (Admin)
**`POST /user/remove_from_role`**

Remove a user from a specific role.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "user@example.com",
  "role": "editor"
}
```

**Field Descriptions:**
- `email` (string, required): Email of the user
- `role` (string, required): Name of the role to remove

**Success Response:**
```http
Status: 200 OK
```

---

### Get Roles List (Admin)
**`GET /user/get_roles_list`**

Get a list of all roles in the system.

**Authentication:** Required (Admin role)

**Parameters:** None

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "authenticated",
    "description": "Basic authenticated user"
  },
  {
    "id": 2,
    "name": "editor",
    "description": "Can edit content"
  },
  {
    "id": 3,
    "name": "admin",
    "description": "Full system access"
  }
]
```

---

## Grant Management Endpoints

### Add Grant (Admin)
**`POST /sd-user/add_grant`**

Create a new grant in the system.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "name": "view_reports",
  "description": "Can view safety reports"
}
```

**Field Descriptions:**
- `name` (string, required): Grant name (2+ characters, alphanumeric with hyphens/underscores, max 100 chars)
- `description` (string, required): Grant description (max 255 chars)

**Success Response:**
```http
Status: 200 OK
```

---

### Add User to Grant (Admin)
**`POST /sd-user/add_to_grant`**

Add a user to a specific grant.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "user@example.com",
  "grant": "view_reports"
}
```

**Field Descriptions:**
- `email` (string, required): Email of the user
- `grant` (string, required): Name of the grant to add

**Success Response:**
```http
Status: 200 OK
```

---

### Remove User from Grant (Admin)
**`POST /sd-user/remove_from_grant`**

Remove a user from a specific grant.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "user@example.com",
  "grant": "view_reports"
}
```

**Field Descriptions:**
- `email` (string, required): Email of the user
- `grant` (string, required): Name of the grant to remove

**Success Response:**
```http
Status: 200 OK
```

---

### Delete Grant (Admin)
**`POST /sd-user/delete_grant`**

Delete a grant from the system. This will also remove all user-grant associations for this grant.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "grant": "view_reports"
}
```

**Field Descriptions:**
- `grant` (string, required): Name of the grant to delete

**Success Response:**
```http
Status: 200 OK
```

---

### Get Grants List (Admin)
**`GET /sd-user/get_grants_list`**

Get a list of all grants in the system.

**Authentication:** Required (Admin role)

**Parameters:** None

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "view_reports",
    "description": "Can view safety reports"
  },
  {
    "id": 2,
    "name": "edit_reports",
    "description": "Can edit safety reports"
  },
  {
    "id": 3,
    "name": "delete_reports",
    "description": "Can delete safety reports"
  }
]
```

---

## Organization Management Endpoints

### Get Organization List (Admin)
**`GET /user/get_organization_list`**

Get a list of all organizations in the system.

**Authentication:** Required (Admin role)

**Parameters:** None

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "Ministry of Transportation"
  },
  {
    "id": 2,
    "name": "Local Municipality"
  },
  {
    "id": 3,
    "name": "Traffic Safety NGO"
  }
]
```

---

### Add Organization (Admin)
**`POST /user/add_organization`**

Create a new organization.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "name": "New Organization Name"
}
```

**Field Descriptions:**
- `name` (string, required): Organization name

**Success Response:**
```http
Status: 200 OK
```

---

### Update User Organization (Admin)
**`POST /user/update_user_org`**

Update a user's organization membership.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "user_email": "user@example.com",
  "org_name": "Ministry of Transportation"
}
```

**Field Descriptions:**
- `user_email` (string, required): Email of the user
- `org_name` (string, required): Name of the organization

**Success Response:**
```http
Status: 200 OK
```

---

## User Deletion Endpoint

### Delete User (Admin)
**`POST /user/delete_user`**

Delete a user and all their connections from the system.

**Authentication:** Required (Admin role)

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Field Descriptions:**
- `email` (string, required): Email of the user to delete

**Success Response:**
```http
Status: 200 OK
```

---

## Common Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error_code": 1001,
  "error_message": "Descriptive error message",
  "additional_info": ["extra", "details"]
}
```

### HTTP Status Codes

- `200` - Success
- `302` - Redirect (OAuth flow)
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (not logged in)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (user/role/organization not found)
- `500` - Internal Server Error

### Common Error Codes

- `1001` - Invalid email format
- `1002` - Invalid phone number format
- `1003` - Missing required fields
- `1004` - User not found
- `1005` - Role not found
- `1006` - Organization not found
- `1007` - Insufficient permissions
- `1008` - Invalid role name format

---

## Authentication

Most endpoints require authentication using one of the following roles:

- **Authenticated**: Basic authenticated user (logged in)
- **Admin**: Full system access, can manage users, roles, and organizations

Authentication is handled through OAuth (Google) and session cookies. Include session cookies in requests after successful OAuth login.

### OAuth Configuration

Both Anyway and Safety Data apps use the same Google OAuth credentials. User separation is handled by the `app` column in the database:
- Anyway app users have `app=0` and use callback URL `/callback/google`
- Safety Data app users have `app=1` and use callback URL `/sd-callback/google`

**Important**: Both callback URLs must be registered in Google Cloud Console OAuth credentials:
- `https://your-domain.com/callback/google` (for Anyway app)
- `https://your-domain.com/sd-callback/google` (for Safety Data app)

Users with the same email can have separate accounts in each app, allowing concurrent login to both apps simultaneously. Each app maintains its own user records, roles, and sessions.

## Notes

- All dates are in ISO 8601 format
- Phone numbers should include country code (e.g., +972 for Israel)
- Emails must be valid email format
- Role names are alphanumeric with hyphens and underscores only
- User types are either "individual" or "organization"
