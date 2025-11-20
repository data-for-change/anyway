# Safety Data Users System - Administrator Quick Start

Quick reference guide for system administrators deploying the Safety Data users system.

## Prerequisites

- Production environment access
- Google Cloud Console access
- Database backup capability
- Deployment access

## Required Changes

### 1. Google Cloud Console OAuth Configuration

**Action**: Add Safety Data callback URL to existing OAuth client

1. Navigate to: [Google Cloud Console > APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Edit your production OAuth 2.0 Client ID
3. Add to "Authorized redirect URIs":
   - `https://your-domain.com/sd-callback/google`
4. Verify existing Anyway callback is present:
   - `https://your-domain.com/callback/google`
5. Save changes

**Note**: Both apps use the same OAuth credentials. No new client needed.

### 2. Database Migration

**Action**: Run Alembic migration

```bash
# 1. Backup database
pg_dump your_database > backup_before_safety_data_$(date +%Y%m%d).sql

# 2. Run migration
alembic upgrade head
```

**Migration**: `a1b2c3d4e5f6_add_safety_data_user_system.py`

**What it does**:
- Adds `app` column to: `users`, `roles`, `organization`, `users_to_roles`, `users_to_organizations`
- Creates indexes for app-based queries
- Creates Safety Data default roles (`anonymous`, `authenticated`, `admins`)
- Creates built-in Safety Data admin user (`anyway@anyway.co.il`, `app=1`)

**Impact**: Existing Anyway users (`app=0`) unaffected. Migration is additive only.

### 3. Code Deployment

**Action**: Deploy code containing Safety Data user system

**Required components**:
- API endpoints with `/sd-user/` prefix
- OAuth callback handlers (`/sd-callback/google`, `/sd-authorize/google`)
- Database migration files

**No environment variable changes needed** - uses existing `GOOGLE_LOGIN_CLIENT_ID` and `GOOGLE_LOGIN_CLIENT_SECRET`

### 4. Verification

**Quick checks**:

```bash
# 1. Verify migration
psql your_database -c "SELECT app, COUNT(*) FROM users GROUP BY app;"

# 2. Verify Safety Data admin exists
psql your_database -c "SELECT email, app FROM users WHERE email='anyway@anyway.co.il' AND app=1;"

# 3. Test endpoints
curl https://your-domain.com/sd-user/is_user_logged_in
curl https://your-domain.com/sd-authorize/google
```

**Functional tests**:
- [ ] Anyway login still works: `https://your-domain.com/authorize/google`
- [ ] Safety Data login works: `https://your-domain.com/sd-authorize/google`
- [ ] Existing users can log into Anyway
- [ ] New users can register in Safety Data

## Rollback Procedure

If issues occur:

```bash
# 1. Rollback migration
alembic downgrade -1

# 2. Restore database (if needed)
psql your_database < backup_before_safety_data_YYYYMMDD.sql

# 3. Remove callback URL from Google Cloud Console (if needed)
```

## Key Points

- **No new OAuth credentials**: Uses existing Google OAuth client
- **No environment variable changes**: Uses existing `GOOGLE_LOGIN_CLIENT_ID` and `GOOGLE_LOGIN_CLIENT_SECRET`
- **Backward compatible**: Existing Anyway users continue working
- **User separation**: Handled by `app` column (0=Anyway, 1=Safety Data)
- **Concurrent login**: Same email can have separate accounts in each app

## Monitoring

After deployment, monitor:
- OAuth callback errors in logs
- User registration success rate
- Database `app` column distribution
- API endpoint response times

## Support

For detailed documentation:
- [Implementation Guide](./IMPLEMENTATION_GUIDE.md) - Full setup guide
- [Developer Reference](./DEVELOPER_REFERENCE.md) - API usage guide
- [User Management API](./users_management.md) - Complete API reference

