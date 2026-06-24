from urllib.parse import quote

from flask import redirect, render_template, request
from flask_login import current_user

from anyway.backend_constants import BE_CONST
from anyway.views.user_system.api import SAFETY_DATA_APP_ID

ADMIN_PAGE_STRINGS = {
    "pageTitle": "ניהול הרשאות - Safety Data",
    "accessDenied": "אין הרשאה",
    "pageHeading": "ניהול הרשאות משתמשים",
    "pageSubtitle": "Safety Data Admin",
    "logout": "התנתקות",
    "addGrantSectionTitle": "הוספת הרשאה למשתמש",
    "emailLabel": "כתובת אימייל",
    "emailPlaceholder": "user@example.com",
    "grantLabel": "הרשאה",
    "loadingGrants": "טוען הרשאות...",
    "addGrantButton": "הוסף הרשאה",
    "lookupUserGrantsButton": "הצג הרשאות משתמש",
    "currentGrantsSectionTitle": "הרשאות נוכחיות",
    "allGrantsSectionTitle": "כל ההרשאות במערכת",
    "loading": "טוען...",
    "noGrantsInSystem": "אין הרשאות במערכת",
    "noGrantsAvailable": "אין הרשאות זמינות",
    "selectGrant": "בחר הרשאה",
    "loadError": "שגיאה בטעינה",
    "loadGrantsError": "שגיאה בטעינת הרשאות",
    "loadUsersError": "שגיאה בטעינת משתמשים",
    "emailRequired": "יש להזין כתובת אימייל",
    "userNotFound": "משתמש לא נמצא",
    "userHasNoGrants": "למשתמש אין הרשאות",
    "removeGrant": "הסר",
    "addGrantError": "שגיאה בהוספת הרשאה",
    "removeGrantError": "שגיאה בהסרת הרשאה",
    "emailAndGrantRequired": "יש למלא אימייל ולבחור הרשאה",
    "grantAddedSuccess": 'ההרשאה "{grant}" נוספה בהצלחה ל-{email}',
    "grantRemovedSuccess": 'ההרשאה "{grant}" הוסרה מ-{email}',
    "networkError": "שגיאת רשת, נסו שוב",
}

ADMIN_PAGE_API = {
    "getGrantsList": "/sd-user/get_grants_list",
    "getAllUsersInfo": "/sd-user/get_all_users_info",
    "addToGrant": "/sd-user/add_to_grant",
    "removeFromGrant": "/sd-user/remove_from_grant",
}


def _admin_page_config():
    return {
        "strings": ADMIN_PAGE_STRINGS,
        "api": ADMIN_PAGE_API,
    }


def _is_safety_data_admin() -> bool:
    if current_user.is_anonymous:
        return False
    if not hasattr(current_user, "app") or current_user.app != SAFETY_DATA_APP_ID:
        return False
    admin_role = BE_CONST.Roles2Names.Admins.value
    user_roles = {role.name for role in current_user.roles if role.app == SAFETY_DATA_APP_ID}
    return admin_role in user_roles


def safety_data_admin_page():
    strings = ADMIN_PAGE_STRINGS
    if current_user.is_anonymous or not hasattr(current_user, "app") or current_user.app != SAFETY_DATA_APP_ID:
        redirect_url = quote(request.url, safe="")
        return redirect(f"/sd-authorize/google?redirect_url={redirect_url}")

    if not _is_safety_data_admin():
        return (
            render_template(
                "safety_data_admin.html",
                access_denied=True,
                strings=strings,
            ),
            403,
        )

    return render_template(
        "safety_data_admin.html",
        access_denied=False,
        admin_email=current_user.email,
        strings=strings,
        admin_config=_admin_page_config(),
    )
