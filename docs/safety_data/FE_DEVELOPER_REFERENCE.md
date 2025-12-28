# Safety Data Users API - Developer Reference Guide

This guide provides a comprehensive reference for Safety Data developers working with the Safety Data users API.

## Table of Contents
- [Overview](#overview)
- [Authentication Flow](#authentication-flow)
- [API Endpoints](#api-endpoints)
- [Code Examples](#code-examples)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Overview

The Safety Data users system provides a complete user management API that is separate from the Anyway app users. Both systems use the same Google OAuth provider, but users are separated by the `app` column in the database:

- **Anyway app**: `app=0`, uses endpoints prefixed with `/user/`
- **Safety Data app**: `app=1`, uses endpoints prefixed with `/sd-user/`

### Key Concepts

1. **User Separation**: Users with the same email can have separate accounts in each app
2. **Concurrent Sessions**: Users can be logged into both apps simultaneously
3. **Shared OAuth**: Both apps use the same Google OAuth credentials
4. **Independent Roles**: Each app has its own roles, organizations, and permissions

---

## Authentication Flow

### Step 1: Initiate OAuth Login

Redirect the user to the authorization endpoint:

```javascript
// Frontend example
const redirectUrl = encodeURIComponent('https://your-app.com/dashboard');
window.location.href = `https://api.anyway.co.il/sd-authorize/google?redirect_url=${redirectUrl}`;
```

**Endpoint**: `GET /sd-authorize/google`

**Parameters**:
- `redirect_url` (optional): URL to redirect after successful login

**Response**: HTTP 302 redirect to Google OAuth

### Step 2: OAuth Callback

After Google authentication, the user is redirected to:
```
https://api.anyway.co.il/sd-callback/google?code=<oauth_code>&state=<state>
```

The callback automatically:
1. Creates or finds the user with `app=1` (Safety Data)
2. Logs the user in
3. Sets session cookies
4. Redirects to the `redirect_url` from Step 1

**Note**: The `/sd-callback/google` endpoint determines that this is a Safety Data user.

### Step 3: Check Login Status

Verify if the user is logged in:

```javascript
fetch('https://api.anyway.co.il/sd-user/is_user_logged_in', {
  credentials: 'include' // Important: include cookies
})
.then(response => response.json())
.then(data => {
  if (data.is_user_logged_in) {
    // User is logged in
  }
});
```

### Step 4: Get User Information

Retrieve current user information:

```javascript
fetch('https://api.anyway.co.il/sd-user/info', {
  credentials: 'include'
})
.then(response => response.json())
.then(user => {
  console.log('User:', user);
});
```

### Step 5: Logout

```javascript
fetch('https://api.anyway.co.il/logout', {
  method: 'GET',
  credentials: 'include'
})
.then(() => {
  // User logged out
});
```

---

## API Endpoints

All Safety Data endpoints are prefixed with `/sd-user/` (except OAuth endpoints which use `/sd-authorize/` and `/sd-callback/`).

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/sd-authorize/google` | Initiate OAuth login | No |
| GET | `/sd-callback/google` | OAuth callback | No |
| GET | `/logout` | Logout user | No |

### User Information Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/sd-user/info` | Get current user info | Yes (Authenticated) |
| GET | `/sd-user/is_user_logged_in` | Check login status | No |
| GET | `/sd-user/get_all_users_info` | Get all users (admin) | Yes (Admin) |

### User Management Endpoints (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sd-user/update` | Update current user |
| POST | `/sd-user/update_user` | Admin: Update any user |
| POST | `/sd-user/change_user_active_mode` | Enable/disable user |
| POST | `/sd-user/delete_user` | Delete user |

### Role Management Endpoints (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sd-user/add_role` | Create new role |
| GET | `/sd-user/get_roles_list` | Get all roles |
| POST | `/sd-user/add_to_role` | Add user to role |
| POST | `/sd-user/remove_from_role` | Remove user from role |

### Organization Management Endpoints (Admin Only)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sd-user/get_organization_list` | Get all organizations |
| POST | `/sd-user/add_organization` | Create organization |
| POST | `/sd-user/update_user_org` | Update user's organization |

---

## Code Examples

### Complete Login Flow (React Example)

```javascript
import React, { useState, useEffect } from 'react';

const SafetyDataLogin = () => {
  const [user, setUser] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const API_BASE = 'https://api.anyway.co.il';

  // Check login status on mount
  useEffect(() => {
    checkLoginStatus();
  }, []);

  const checkLoginStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/sd-user/is_user_logged_in`, {
        credentials: 'include'
      });
      const data = await response.json();
      setIsLoggedIn(data.is_user_logged_in);
      
      if (data.is_user_logged_in) {
        fetchUserInfo();
      }
    } catch (error) {
      console.error('Error checking login status:', error);
    }
  };

  const fetchUserInfo = async () => {
    try {
      const response = await fetch(`${API_BASE}/sd-user/info`, {
        credentials: 'include'
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
  };

  const handleLogin = () => {
    const redirectUrl = encodeURIComponent(window.location.origin + '/dashboard');
    window.location.href = `${API_BASE}/sd-authorize/google?redirect_url=${redirectUrl}`;
  };

  const handleLogout = async () => {
    try {
      await fetch(`${API_BASE}/logout`, {
        method: 'GET',
        credentials: 'include'
      });
      setIsLoggedIn(false);
      setUser(null);
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  if (!isLoggedIn) {
    return (
      <div>
        <button onClick={handleLogin}>Login with Google</button>
      </div>
    );
  }

  return (
    <div>
      <h1>Welcome, {user?.first_name} {user?.last_name}</h1>
      <p>Email: {user?.email}</p>
      <button onClick={handleLogout}>Logout</button>
    </div>
  );
};

export default SafetyDataLogin;
```

### Update User Profile

```javascript
const updateUserProfile = async (userData) => {
  try {
    const response = await fetch('https://api.anyway.co.il/sd-user/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        first_name: userData.firstName,
        last_name: userData.lastName,
        email: userData.email,
        phone: userData.phone,
        user_type: userData.userType,
        user_url: userData.website,
        user_desc: userData.description
      })
    });

    if (response.ok) {
      console.log('Profile updated successfully');
    } else {
      const error = await response.json();
      console.error('Error updating profile:', error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

### Admin: Get All Users

```javascript
const getAllUsers = async () => {
  try {
    const response = await fetch('https://api.anyway.co.il/sd-user/get_all_users_info', {
      credentials: 'include'
    });

    if (response.ok) {
      const users = await response.json();
      return users;
    } else if (response.status === 401 || response.status === 403) {
      console.error('Unauthorized: Admin access required');
    }
  } catch (error) {
    console.error('Error fetching users:', error);
  }
};
```

### Admin: Add User to Role

```javascript
const addUserToRole = async (userEmail, roleName) => {
  try {
    const response = await fetch('https://api.anyway.co.il/sd-user/add_to_role', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        email: userEmail,
        role: roleName
      })
    });

    if (response.ok) {
      console.log('User added to role successfully');
    } else {
      const error = await response.json();
      console.error('Error adding user to role:', error);
    }
  } catch (error) {
    console.error('Network error:', error);
  }
};
```

### Python Example (Backend/Testing)

```python
import requests

API_BASE = "https://api.anyway.co.il"

# Create a session to maintain cookies
session = requests.Session()

# Check login status
response = session.get(f"{API_BASE}/sd-user/is_user_logged_in")
print(response.json())  # {"is_user_logged_in": false}

# Get user info (requires authentication)
response = session.get(f"{API_BASE}/sd-user/info")
if response.status_code == 200:
    user = response.json()
    print(f"User: {user['email']}")
else:
    print(f"Not logged in: {response.status_code}")

# Admin: Get all users
response = session.get(f"{API_BASE}/sd-user/get_all_users_info")
if response.status_code == 200:
    users = response.json()
    print(f"Total users: {len(users)}")
```

---

## Error Handling

### Common Error Responses

All error responses follow this format:

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
- `404` - Not Found
- `500` - Internal Server Error

### Common Error Codes

| Code | Message | Description |
|------|---------|-------------|
| 1001 | Invalid email format | Email validation failed |
| 1002 | Invalid phone number format | Phone validation failed |
| 1003 | Missing required fields | Required field is missing |
| 1004 | User not found | User doesn't exist |
| 1005 | Role not found | Role doesn't exist |
| 1006 | Organization not found | Organization doesn't exist |
| 1007 | Insufficient permissions | User lacks required role |
| 1008 | Invalid role name format | Role name doesn't match pattern |

### Error Handling Example

```javascript
const handleApiCall = async (url, options) => {
  try {
    const response = await fetch(url, {
      ...options,
      credentials: 'include'
    });

    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 401:
          // Not logged in - redirect to login
          window.location.href = '/login';
          break;
        case 403:
          // Insufficient permissions
          console.error('Access denied:', error.error_message);
          break;
        case 400:
          // Bad request - show validation errors
          console.error('Validation error:', error);
          break;
        default:
          console.error('API error:', error);
      }
      
      throw new Error(error.error_message || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('Request failed:', error);
    throw error;
  }
};
```

---

## Best Practices

### 1. Always Include Credentials

When making authenticated requests, always include credentials:

```javascript
fetch(url, {
  credentials: 'include'  // Important!
})
```

### 2. Handle Session Expiration

Check login status before making authenticated requests:

```javascript
const makeAuthenticatedRequest = async (url) => {
  // First check if still logged in
  const loginCheck = await fetch('/sd-user/is_user_logged_in', {
    credentials: 'include'
  });
  
  const { is_user_logged_in } = await loginCheck.json();
  
  if (!is_user_logged_in) {
    // Redirect to login
    window.location.href = '/login';
    return;
  }
  
  // Proceed with request
  return fetch(url, { credentials: 'include' });
};
```

### 3. Store User Context

Cache user information to avoid repeated API calls:

```javascript
class UserContext {
  constructor() {
    this.user = null;
    this.lastFetch = null;
    this.CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  }

  async getUser(forceRefresh = false) {
    const now = Date.now();
    
    if (!forceRefresh && this.user && this.lastFetch && 
        (now - this.lastFetch) < this.CACHE_DURATION) {
      return this.user;
    }

    const response = await fetch('/sd-user/info', {
      credentials: 'include'
    });

    if (response.ok) {
      this.user = await response.json();
      this.lastFetch = now;
      return this.user;
    }

    return null;
  }

  clear() {
    this.user = null;
    this.lastFetch = null;
  }
}

const userContext = new UserContext();
```

### 4. Use Environment Variables

Don't hardcode API URLs:

```javascript
// config.js
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'https://api.anyway.co.il';

// usage
import { API_BASE_URL } from './config';
fetch(`${API_BASE_URL}/sd-user/info`, { credentials: 'include' });
```

### 5. Implement Retry Logic

For critical operations, implement retry logic:

```javascript
const fetchWithRetry = async (url, options, maxRetries = 3) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) {
        return await response.json();
      }
      
      // Don't retry on client errors
      if (response.status >= 400 && response.status < 500) {
        throw new Error(`Client error: ${response.status}`);
      }
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

### 6. Validate User Permissions

Check user roles before showing admin features:

```javascript
const hasRole = (user, roleName) => {
  if (!user || !user.roles) return false;
  return user.roles.some(role => role.name === roleName);
};

// Usage
if (hasRole(user, 'admins')) {
  // Show admin features
}
```

---

## Testing

### Manual Testing Checklist

- [ ] Can initiate OAuth login via `/sd-authorize/google`
- [ ] OAuth callback redirects correctly
- [ ] User can check login status
- [ ] User can retrieve their information
- [ ] User can update their profile
- [ ] User can logout
- [ ] Admin can view all users
- [ ] Admin can manage roles
- [ ] Admin can manage organizations
- [ ] Concurrent login works (same email, different apps)

### Integration Testing Example

```javascript
describe('Safety Data User API', () => {
  let session;

  beforeEach(() => {
    session = new Session(); // Your session management
  });

  test('should check login status', async () => {
    const response = await session.get('/sd-user/is_user_logged_in');
    expect(response.data.is_user_logged_in).toBe(false);
  });

  test('should require authentication for user info', async () => {
    const response = await session.get('/sd-user/info');
    expect(response.status).toBe(401);
  });

  // Add more tests...
});
```

---

## Additional Resources

- [User Management API Documentation](./users_management.md) - Complete API reference
- [Implementation Guide](./IMPLEMENTATION_GUIDE.md) - Setup instructions
- [Anyway User API](../USERAPI.md) - Anyway app API (for comparison)

---

## Support

For questions or issues:
- Check the [Implementation Guide](./IMPLEMENTATION_GUIDE.md) for setup help
- Review [User Management API Documentation](./users_management.md) for API details
- Contact the development team

